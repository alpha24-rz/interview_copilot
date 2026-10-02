import json
import os
import re

STOP_WORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of',
    'and', 'or', 'with', 'as', 'by', 'that', 'this', 'it', 'from', 'be', 'have', 'has',
    'do', 'does', 'did', 'can', 'could', 'will', 'would', 'should', 'you', 'your', 'my',
    'me', 'we', 'our', 'tell', 'explain', 'about', 'how', 'what', 'why', 'when', 'where',
    'which', 'who', 'describe', 'elaborate', 'discuss', 'give', 'walk'
}

class CopilotSearchEngine:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "qa_database.json")
        self.db_path = db_path
        self.items = []
        self.hotkey_map = {}
        self.item_kw_tokens = []
        self.load_database()

    def load_database(self):
        with open(self.db_path, "r", encoding="utf-8") as f:
            self.items = json.load(f)
        
        self.hotkey_map = {}
        self.item_kw_tokens = []

        for item in self.items:
            if "hotkey" in item:
                self.hotkey_map[item["hotkey"].upper()] = item

            # Pre-compute token sets untuk pencarian cepat < 1 ms
            kw_tokens = set()
            for kw in item.get("keywords", []):
                for t in re.findall(r'\w+', kw.lower()):
                    if t not in STOP_WORDS and len(t) > 2:
                        kw_tokens.add(t)
            
            title_tokens = set()
            for t in re.findall(r'\w+', item.get("title", "").lower()):
                if t not in STOP_WORDS and len(t) > 2:
                    title_tokens.add(t)

            self.item_kw_tokens.append({
                "kw_tokens": kw_tokens,
                "title_tokens": title_tokens,
                "keywords": [k.lower() for k in item.get("keywords", [])]
            })

    def get_by_hotkey(self, hotkey_str):
        return self.hotkey_map.get(hotkey_str.upper(), None)

    def search(self, query):
        query_clean = query.strip().lower()
        if not query_clean:
            return self.items[:3]

        # 1. Cek kecocokan langsung hotkey (F1, F2, dst)
        if query_clean.upper() in self.hotkey_map:
            return [self.hotkey_map[query_clean.upper()]]

        all_tokens = set(re.findall(r'\w+', query_clean))
        meaningful_tokens = {t for t in all_tokens if t not in STOP_WORDS and len(t) > 2}
        if not meaningful_tokens:
            meaningful_tokens = all_tokens

        scored_results = []

        for idx, item in enumerate(self.items):
            score = 0.0
            pre = self.item_kw_tokens[idx]

            # A. EXACT PHRASE MATCHING (Bobot Tertinggi)
            for kw in pre["keywords"]:
                if kw in query_clean:
                    # Semakin panjang kata kunci yang cocok, semakin tinggi skornya
                    score += 50.0 + (len(kw.split()) * 10.0)
                elif query_clean in kw:
                    score += 20.0

            # B. MEANINGFUL TOKEN OVERLAP WITH KEYWORDS
            kw_overlap = meaningful_tokens.intersection(pre["kw_tokens"])
            score += len(kw_overlap) * 15.0

            # C. TITLE TOKEN OVERLAP
            title_overlap = meaningful_tokens.intersection(pre["title_tokens"])
            score += len(title_overlap) * 20.0

            # D. CONTENT TEXT (HOOK & BULLETS) SEARCH
            content_text = (item.get("opening_hook", "") + " " + " ".join(item.get("bullets", []))).lower()
            for tok in meaningful_tokens:
                if tok in content_text:
                    score += 3.0

            if score > 0:
                scored_results.append((score, item))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_results]

if __name__ == "__main__":
    engine = CopilotSearchEngine()
    test_queries = [
        "Can you tell me about your thesis regarding lost in the middle?",
        "What did you do at BMKG with RAG and documents?",
        "How do you design tool use and function calling in AI agents?",
        "What are your salary expectations for this remote role?",
        "Explain the architecture of Orlith AI"
    ]
    for q in test_queries:
        res = engine.search(q)
        print(f"Q: '{q}'\n-> Matched: {res[0]['title']} ({res[0]['id']})\n")
