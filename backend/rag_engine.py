import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("rag_engine")
logging.basicConfig(level=logging.INFO)

class ScamRAGEngine:
    def __init__(self, knowledge_base_path: str = None):
        if knowledge_base_path is None:
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            knowledge_base_path = os.path.join(backend_dir, "knowledge_base.json")
            
        self.knowledge_base_path = knowledge_base_path
        self.items: List[Dict[str, Any]] = []
        self.chroma_collection = None
        self.use_chroma = False

        self._load_knowledge_base()
        self._init_vector_db()

    def _load_knowledge_base(self):
        try:
            if os.path.exists(self.knowledge_base_path):
                with open(self.knowledge_base_path, "r", encoding="utf-8") as f:
                    self.items = json.load(f)
                logger.info(f"Loaded {len(self.items)} items from Knowledge Base.")
            else:
                logger.warning(f"Knowledge base file not found at {self.knowledge_base_path}")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")

    def _init_vector_db(self):
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Persistent or in-memory chroma store
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            chroma_dir = os.path.join(backend_dir, "chroma_db")
            
            client = chromadb.PersistentClient(path=chroma_dir)
            collection = client.get_or_create_collection(name="scam_patterns")
            
            # Upsert all items into collection so newly added patterns are immediately indexed
            if self.items:
                documents = []
                metadatas = []
                ids = []
                
                for item in self.items:
                    ids.append(item["id"])
                    documents.append(f"{item['title']} - {item['category']}. Content: {item['pattern_text']}")
                    metadatas.append({
                        "id": item["id"],
                        "category": item["category"],
                        "title": item["title"],
                        "recommendation": item.get("recommendation", "")
                    })
                    
                collection.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"ChromaDB vector store indexed/upserted {len(self.items)} items successfully.")
                
            self.chroma_collection = collection
            self.use_chroma = True
        except Exception as e:
            logger.warning(f"ChromaDB initialization fallback mode active: {e}")
            self.use_chroma = False

    def retrieve_context(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve top relevant scam pattern entries for RAG context"""
        if not query or not query.strip():
            return []

        results = []
        if self.use_chroma and self.chroma_collection:
            try:
                res = self.chroma_collection.query(
                    query_texts=[query],
                    n_results=min(top_k, len(self.items))
                )
                
                ids = res['ids'][0] if res.get('ids') else []
                distances = res['distances'][0] if res.get('distances') else [0]*len(ids)
                
                # Match back to knowledge base objects
                kb_map = {item["id"]: item for item in self.items}
                for item_id, dist in zip(ids, distances):
                    if item_id in kb_map:
                        item = kb_map[item_id].copy()
                        item["similarity_score"] = round(1.0 / (1.0 + float(dist)), 3)
                        results.append(item)
                return results
            except Exception as e:
                logger.warning(f"Chroma query failed, using keyword fallback: {e}")

        # Fallback term-frequency matching
        query_words = set(query.lower().split())
        scored_items = []
        for item in self.items:
            text = f"{item['title']} {item['category']} {item['pattern_text']} {' '.join(item.get('tactics', []))}".lower()
            text_words = set(text.split())
            overlap = len(query_words.intersection(text_words))
            
            # Simple keyword score
            score = overlap / (len(query_words) + 1.0)
            scored_items.append((score, item))
            
        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item.copy() for score, item in scored_items[:top_k] if score > 0.05] or [self.items[0]]

# Global singleton
rag_engine = ScamRAGEngine()
