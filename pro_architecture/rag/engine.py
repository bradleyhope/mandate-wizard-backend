from __future__ import annotations
import json, time
from typing import Any, Dict, List
from config import S
from rag.intent import classify
from rag.retrievers.pinecone_retriever import PineconeRetriever
from rag.graph.dao import Neo4jDAO
from rag.ranking.reranker import get_reranker
from rag.embedder import get_embedder
from rag.fusion import dedup_keep_best, mmr
from rag.prompts import SYSTEM, USER_TEMPLATE

class Engine:
    def __init__(self):
        self.retriever = PineconeRetriever()
        self.graph = Neo4jDAO()
        self.embedder = get_embedder()
        self.reranker = get_reranker()

    def _multi_query(self, q: str) -> List[str]:
        # Lightweight MQE: simple rewrites to trade recall/latency without an LLM call.
        variants = [q]
        if S.M_Q_EXPANSIONS >= 1:
            variants.append(q + " Hollywood TV and film industry context")
        if S.M_Q_EXPANSIONS >= 2:
            variants.append(q.replace("mandate", "commissioning mandate"))
        return list(dict.fromkeys(variants))[: 1 + S.M_Q_EXPANSIONS]

    def retrieve(self, question: str) -> List[Dict[str, Any]]:
        qs = self._multi_query(question)
        all_hits: List[Dict[str, Any]] = []
        for subq in qs:
            hits = self.retriever.query(subq, top_k=S.TOP_K_VECTOR)
            all_hits.extend(hits)
        merged = dedup_keep_best(all_hits, key="id")

        # Rerank
        if self.reranker and merged:
            top = merged[: S.RERANK_TOP_K]
            texts = [h.get("metadata", {}).get("text", "") for h in top]
            ranks = self.reranker.rerank(question, texts, top_n=min(S.RERANK_RETURN, len(texts)))
            ranked = [top[r["index"]] for r in ranks]
            return ranked

        # MMR fallback if enabled
        if S.USE_MMR:
            return merged[: S.RERANK_RETURN]
        return merged[: S.RERANK_RETURN]

    def enrich_entities(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for d in docs[:5]:
            meta = d.get("metadata") or {}
            pid = meta.get("person_entity_id")
            if pid:
                p = self.graph.get_person_by_id(pid)
                if p:
                    out.append({"type": "neo4j_person", "entity_id": pid, "data": p})
        return out

    def synthesize(self, question: str, docs: List[Dict[str, Any]], entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        from openai import OpenAI
        client = OpenAI(
            api_key=S.OPENAI_API_KEY,
            base_url='https://api.openai.com/v1'
        )
        # Keep snippets small to preserve tokens, but include dates and URLs
        rows = []
        citations = []
        for d in docs:
            meta = d.get("metadata", {})
            snippet = {
                "id": d.get("id"),
                "text": meta.get("text", "")[:1200],
                "source": meta.get("source", ""),
                "score": d.get("score", 0),
                "updated": meta.get("updated", meta.get("source_date", meta.get("extraction_date", ""))),
                "source_publication": meta.get("source_publication", "")
            }
            rows.append(snippet)
            citations.append({"type": "doc", "id": d.get("id")})
        for e in entities:
            citations.append({"type": "neo4j", "id": e.get("entity_id")})
        prompt = USER_TEMPLATE.format(question=question, snippets="\n".join(json.dumps(r) for r in rows))
        chat = client.chat.completions.create(
            model=S.COMPLETIONS_MODEL,
            temperature=0.2,
            max_tokens=S.MAX_TOKENS,
            messages=[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}]
        )
        txt = chat.choices[0].message.content
        try:
            data = json.loads(txt)
        except Exception:
            # fallback wrapper
            data = {"final_answer": txt, "citations": citations, "entities": [], "sources": [], "last_updated": None}
        # ensure required fields
        if not data.get("citations"):
            data["citations"] = citations
        if not data.get("sources"):
            data["sources"] = []
        if not data.get("last_updated"):
            data["last_updated"] = None
        if not data.get("data_freshness"):
            data["data_freshness"] = "unknown"
        return data

    def answer(self, question: str, user_email: str = None) -> Dict[str, Any]:
        t0 = time.time()
        intent = classify(question)
        docs = self.retrieve(question)
        entities = self.enrich_entities(docs)
        out = self.synthesize(question, docs, entities)
        
        # Add metadata
        out["meta"] = {
            "intent": intent,
            "latency_ms": int((time.time() - t0)*1000),
            "retrieved": len(docs),
        }
        
        # Ensure follow_up_questions key exists
        if "follow_up_questions" not in out:
            out["follow_up_questions"] = []
        
        # Track demand signals (what users ask for that we don't have)
        from demand_signals import DemandSignalTracker
        tracker = DemandSignalTracker()
        tracker.log_demand(question, out, user_email)
        
        # Web search fallback for low-quality results
        from web_search_fallback import WebSearchFallback
        fallback = WebSearchFallback()
        if fallback.should_trigger(out):
            out = fallback.search_and_supplement(question, out)
        
        # Track potentially poor answers
        answer_length = len(out.get("final_answer", ""))
        if answer_length < 50 or len(entities) == 0:
            self._log_poor_answer(question, out, docs)
        
        return out
    
    def _log_poor_answer(self, question: str, response: Dict[str, Any], docs: List[Dict[str, Any]]):
        """Log questions that may have poor answers for later review."""
        import json
        from pathlib import Path
        from datetime import datetime
        
        log_dir = Path("/tmp/mandate_wizard_logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "poor_answers.jsonl"
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "question": question,
            "confidence": response.get("confidence", 0),
            "answer_length": len(response.get("final_answer", "")),
            "entities_count": len(response.get("entities", [])),
            "docs_retrieved": len(docs),
            "reason": []
        }
        
        if response.get("confidence", 0) < 0.7:
            entry["reason"].append("low_confidence")
        if len(response.get("final_answer", "")) < 50:
            entry["reason"].append("short_answer")
        if len(response.get("entities", [])) == 0:
            entry["reason"].append("no_entities")
        
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
