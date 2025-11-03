"""
Request Batching
Batch multiple embedding/LLM requests for better GPU utilization
"""

from typing import List, Dict, Any, Callable
from collections import defaultdict
import threading
import time
import queue


class RequestBatcher:
    """
    Batch multiple requests together for efficiency

    Use cases:
    - Batch embedding generation (4x faster for 4 queries)
    - Batch LLM requests
    - Batch database queries
    """

    def __init__(
        self,
        batch_size: int = 8,
        max_wait_ms: int = 50,
        processor: Callable = None
    ):
        """
        Initialize request batcher

        Args:
            batch_size: Maximum batch size
            max_wait_ms: Maximum wait time before processing batch (milliseconds)
            processor: Function to process batches (receives list of inputs)
        """
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms / 1000  # Convert to seconds
        self.processor = processor

        # Queue of pending requests: (input, result_queue)
        self.pending_queue = queue.Queue()

        # Batching thread
        self.running = True
        self.batch_thread = threading.Thread(target=self._batch_worker, daemon=True)
        self.batch_thread.start()

        # Statistics
        self.stats = {
            'total_requests': 0,
            'total_batches': 0,
            'avg_batch_size': 0.0
        }
        self.stats_lock = threading.Lock()

    def _batch_worker(self):
        """Background thread that batches requests"""
        while self.running:
            batch = []
            result_queues = []
            batch_start = time.time()

            # Collect requests until batch is full or timeout
            while len(batch) < self.batch_size:
                wait_time = self.max_wait_ms - (time.time() - batch_start)
                if wait_time <= 0:
                    break

                try:
                    input_data, result_q = self.pending_queue.get(timeout=wait_time)
                    batch.append(input_data)
                    result_queues.append(result_q)
                except queue.Empty:
                    break

            # Process batch if we have any requests
            if batch:
                try:
                    # Process entire batch
                    if self.processor:
                        results = self.processor(batch)
                    else:
                        results = batch  # No processor, just return inputs

                    # Distribute results
                    for result, result_q in zip(results, result_queues):
                        result_q.put(('success', result))

                except Exception as e:
                    # Send error to all waiting requests
                    for result_q in result_queues:
                        result_q.put(('error', str(e)))

                # Update stats
                with self.stats_lock:
                    self.stats['total_requests'] += len(batch)
                    self.stats['total_batches'] += 1
                    total_reqs = self.stats['total_requests']
                    total_batches = self.stats['total_batches']
                    self.stats['avg_batch_size'] = total_reqs / total_batches

    def process(self, input_data: Any, timeout: float = 10.0) -> Any:
        """
        Submit request for batched processing

        Args:
            input_data: Input to process
            timeout: Maximum time to wait for result (seconds)

        Returns:
            Processed result

        Raises:
            TimeoutError: If result not received within timeout
            Exception: If processing failed
        """
        # Create result queue
        result_q = queue.Queue()

        # Add to pending queue
        self.pending_queue.put((input_data, result_q))

        # Wait for result
        try:
            status, result = result_q.get(timeout=timeout)
            if status == 'error':
                raise Exception(f"Batch processing failed: {result}")
            return result
        except queue.Empty:
            raise TimeoutError(f"Batch processing timeout after {timeout}s")

    def process_many(self, inputs: List[Any], timeout: float = 10.0) -> List[Any]:
        """
        Submit multiple requests for batched processing

        Args:
            inputs: List of inputs to process
            timeout: Maximum time to wait for results

        Returns:
            List of results (same order as inputs)
        """
        # Submit all requests
        result_queues = []
        for input_data in inputs:
            result_q = queue.Queue()
            self.pending_queue.put((input_data, result_q))
            result_queues.append(result_q)

        # Collect results
        results = []
        for result_q in result_queues:
            try:
                status, result = result_q.get(timeout=timeout)
                if status == 'error':
                    raise Exception(f"Batch processing failed: {result}")
                results.append(result)
            except queue.Empty:
                raise TimeoutError(f"Batch processing timeout after {timeout}s")

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get batching statistics"""
        with self.stats_lock:
            return self.stats.copy()

    def shutdown(self):
        """Shutdown the batcher"""
        self.running = False
        self.batch_thread.join(timeout=5)


class EmbeddingBatcher:
    """
    Specialized batcher for embedding generation

    Batches multiple texts for embedding generation, achieving
    significant speedup (4x faster for batch of 4)
    """

    def __init__(self, embedding_model, batch_size: int = 8, max_wait_ms: int = 50):
        """
        Initialize embedding batcher

        Args:
            embedding_model: SentenceTransformer model
            batch_size: Maximum batch size
            max_wait_ms: Maximum wait time before processing
        """
        self.embedding_model = embedding_model

        # Create batcher with embedding processor
        self.batcher = RequestBatcher(
            batch_size=batch_size,
            max_wait_ms=max_wait_ms,
            processor=self._process_embeddings
        )

    def _process_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Process batch of texts to embeddings"""
        # Generate embeddings for entire batch
        embeddings = self.embedding_model.encode(texts)
        # Convert to list of lists
        return [emb.tolist() for emb in embeddings]

    def embed(self, text: str, timeout: float = 10.0) -> List[float]:
        """
        Generate embedding for text (batched)

        Args:
            text: Text to embed
            timeout: Maximum wait time

        Returns:
            Embedding vector
        """
        return self.batcher.process(text, timeout=timeout)

    def embed_many(self, texts: List[str], timeout: float = 10.0) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched)

        Args:
            texts: List of texts to embed
            timeout: Maximum wait time

        Returns:
            List of embedding vectors
        """
        return self.batcher.process_many(texts, timeout=timeout)

    def get_stats(self) -> Dict[str, Any]:
        """Get batching statistics"""
        return self.batcher.get_stats()


# Global instances
_embedding_batcher = None


def get_embedding_batcher(embedding_model) -> EmbeddingBatcher:
    """Get or create global embedding batcher"""
    global _embedding_batcher
    if _embedding_batcher is None:
        _embedding_batcher = EmbeddingBatcher(embedding_model)
    return _embedding_batcher


# Example usage
if __name__ == '__main__':
    from sentence_transformers import SentenceTransformer

    print("Testing request batching...\n")

    # Load model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Create batcher
    batcher = EmbeddingBatcher(model, batch_size=4, max_wait_ms=100)

    # Test single embedding
    print("1. Single embedding:")
    start = time.time()
    emb = batcher.embed("Who should I pitch to?")
    print(f"   Time: {(time.time() - start)*1000:.1f}ms")
    print(f"   Embedding shape: {len(emb)}")

    # Test multiple embeddings (benefits from batching)
    print("\n2. Multiple embeddings (batched):")
    texts = [
        "Who should I pitch to?",
        "Recent crime thrillers",
        "Brandon Riegg's mandate",
        "What's popular in UK?"
    ]

    start = time.time()
    embeddings = batcher.embed_many(texts)
    duration = (time.time() - start) * 1000
    print(f"   Time: {duration:.1f}ms ({duration/len(texts):.1f}ms per embedding)")
    print(f"   Generated {len(embeddings)} embeddings")

    # Show stats
    print("\n3. Batching stats:")
    stats = batcher.get_stats()
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Total batches: {stats['total_batches']}")
    print(f"   Avg batch size: {stats['avg_batch_size']:.2f}")
