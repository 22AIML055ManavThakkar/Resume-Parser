import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    USE_SBERT = True
    _model = None
except:
    USE_SBERT = False
    _model = None

class TextEmbedder:
    def __init__(self, name="all-MiniLM-L6-v2"):
        global _model
        if USE_SBERT:
            if _model is None:
                _model = SentenceTransformer(name)
            self.model = _model
        else:
            self.model = None

    def similarity(self, text1, text2):
        if USE_SBERT and self.model:
            v1 = self.model.encode([text1], convert_to_numpy=True)[0]
            v2 = self.model.encode([text2], convert_to_numpy=True)[0]
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            tfidf = TfidfVectorizer()
            vecs = tfidf.fit_transform([text1, text2]).toarray()
            v1, v2 = vecs[0], vecs[1]

        sim = cosine_similarity([v1], [v2])[0][0]
        return float(max(0, min(1, sim)))
