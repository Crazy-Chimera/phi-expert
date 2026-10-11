"""Lightweight keyword routing for Φ-Expert."""
ROUTES = {
 "physics": ("gravit", "particle", "metrik", "kvant", "quantum", "informion", "síla", "force", "phi", "omega"),
 "biology": ("buň", "cell", "enzym", "fotosynt", "photosynth", "biolog", "protein", "organism", "dna"),
 "economics": ("ekonom", "trh", "market", "cena", "price", "finance", "finan"),
 "philosophy": ("exist", "realit", "smysl", "meaning", "metafyz", "ethic", "svobodná vůle", "free will"),
 "consciousness": ("vědom", "conscious", "medit", "mikrotub", "self-model", "rekurz"),
 "cosmology": ("velký třesk", "big bang", "černá díra", "black hole", "temná hmota", "dark matter", "kosmolog", "vesmír", "universe"),
}
def classify_question(question: str) -> str:
    text = question.casefold()
    scores = {name: sum(1 for word in words if word in text) for name, words in ROUTES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "general"
