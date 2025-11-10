from flask import Flask, request, jsonify
from flask_cors import CORS
from rag.engine import Engine
from config import S
import os, psutil, time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins":"*","supports_credentials":True}})

_engine = None
def get_engine():
    global _engine
    if _engine is None:
        _engine = Engine()
    return _engine

@app.route("/healthz")
def healthz():
    return {"ok": True}, 200

@app.route("/", methods=["GET"])
def root():
    return {"service": "Mandate Wizard backend", "mode": S.EMBEDDER + "/" + S.RERANKER}, 200

@app.route("/metrics", methods=["GET"])
def metrics():
    p = psutil.Process(os.getpid())
    return {
        "rss_mb": round(p.memory_info().rss/1024/1024, 1),
        "threads": p.num_threads(),
        "cpu_percent": psutil.cpu_percent(interval=0.1)
    }, 200

@app.route("/api/answer", methods=["POST"])
def answer():
    data = request.get_json(force=True) or {}
    q = (data.get("question") or "").strip()
    if not q:
        return jsonify({"error":"question is required"}), 400
    eng = get_engine()
    out = eng.answer(q)
    return jsonify(out), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
