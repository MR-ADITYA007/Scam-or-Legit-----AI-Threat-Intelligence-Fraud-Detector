import os
import json
import logging
import re
from typing import List, Dict, Any, Optional

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
            
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            chroma_dir = os.path.join(backend_dir, "chroma_db")
            
            client = chromadb.PersistentClient(path=chroma_dir)
            collection = client.get_or_create_collection(name="scam_patterns")
            
            if self.items:
                documents = []
                metadatas = []
                ids = []
                
                for item in self.items:
                    ids.append(item["id"])
                    label = item.get("label", "scam")
                    documents.append(f"[{label.upper()}] {item['title']} - {item['category']}. Content: {item['pattern_text']}")
                    metadatas.append({
                        "id": item["id"],
                        "category": item["category"],
                        "title": item["title"],
                        "label": label,
                        "source_name": item.get("source_name", "Local Knowledge Base"),
                        "source_url": item.get("source_url", ""),
                        "verification_status": item.get("verification_status", "documented"),
                        "example_type": item.get("example_type", "pattern")
                    })
                    
                collection.upsert(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"ChromaDB vector store indexed {len(self.items)} items successfully.")
                
            self.chroma_collection = collection
            self.use_chroma = True
        except Exception as e:
            logger.warning(f"ChromaDB initialization fallback mode active: {e}")
            self.use_chroma = False

    def retrieve_context(
        self,
        query: str,
        top_k: int = 4,
        relevance_threshold: float = 0.35,
        include_legitimate: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top relevant knowledge base entries (scam patterns & legitimate counterexamples).
        Applies relevance thresholding and deduplication.
        """
        if not query or not query.strip():
            return []

        results = []
        kb_map = {item["id"]: item for item in self.items}

        # 1. Semantic Similarity Search via ChromaDB
        if self.use_chroma and self.chroma_collection:
            try:
                res = self.chroma_collection.query(
                    query_texts=[query],
                    n_results=min(top_k * 2, len(self.items))
                )
                
                ids = res['ids'][0] if res.get('ids') else []
                distances = res['distances'][0] if res.get('distances') else [0] * len(ids)
                
                for item_id, dist in zip(ids, distances):
                    if item_id in kb_map:
                        item = kb_map[item_id].copy()
                        # Normalize distance to similarity score in [0.0, 1.0]
                        similarity = round(1.0 / (1.0 + float(dist)), 3)
                        item["similarity_score"] = similarity
                        item["distance"] = round(float(dist), 3)
                        if similarity >= relevance_threshold:
                            results.append(item)
            except Exception as e:
                logger.warning(f"Chroma query failed, falling back to keyword retrieval: {e}")

        # 2. Keyword-based matching fallback or enhancement
        query_words = set(re.findall(r'\w+', query.lower()))
        keyword_hits = []
        for item in self.items:
            text = f"{item['title']} {item['category']} {item['pattern_text']} {' '.join(item.get('tactics', []))}".lower()
            text_words = set(re.findall(r'\w+', text))
            overlap = len(query_words.intersection(text_words))
            if overlap > 0:
                score = round(overlap / (len(query_words) + 2.0), 3)
                if score >= 0.1:
                    item_copy = item.copy()
                    item_copy["similarity_score"] = max(score, item_copy.get("similarity_score", 0.0))
                    keyword_hits.append(item_copy)

        # Merge results without duplicates
        merged_map = {}
        for r in (results + keyword_hits):
            r_id = r["id"]
            if r_id not in merged_map or r["similarity_score"] > merged_map[r_id]["similarity_score"]:
                merged_map[r_id] = r

        final_candidates = list(merged_map.values())
        final_candidates.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

        # Separate scam vs legitimate to ensure balanced RAG evidence
        scam_results = [item for item in final_candidates if item.get("label", "scam").lower() == "scam"]
        legit_results = [item for item in final_candidates if item.get("label", "").lower() in ["legitimate", "legit"]]

        selected = scam_results[:top_k]
        if include_legitimate and legit_results:
            selected.append(legit_results[0])

        # Deduplicate and format return payload
        deduped = []
        seen_ids = set()
        for item in selected:
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                deduped.append({
                    "id": item["id"],
                    "category": item["category"],
                    "label": item.get("label", "scam"),
                    "title": item["title"],
                    "pattern_text": item["pattern_text"],
                    "similarity_score": item.get("similarity_score", 0.5),
                    "source_name": item.get("source_name", "Knowledge Base"),
                    "source_url": item.get("source_url", ""),
                    "verification_status": item.get("verification_status", "documented"),
                    "example_type": item.get("example_type", "pattern_match"),
                    "tactics": item.get("tactics", []),
                    "risk_indicators": item.get("risk_indicators", []),
                    "recommendation": item.get("recommendation", "")
                })

        logger.info(f"RAG retrieved {len(deduped)} evidence items for query (length {len(query)}).")
        return deduped


rag_engine = ScamRAGEngine()
