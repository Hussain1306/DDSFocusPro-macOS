import spacy

# Load spaCy's English model
nlp = spacy.load("en_core_web_sm")

# Keywords to detect common topics
TOPIC_KEYWORDS = {
    "finance": ["invoice", "payment", "cost", "price", "tax", "budget", "finance"],
    "sales": ["client", "customer", "order", "deal", "contract", "lead", "prospect"],
    "devops": ["server", "deployment", "api", "docker", "git", "cloud", "monitoring"],
    "task": ["deadline", "task", "todo", "project", "assignment", "status", "tracker"]
}

def extract_entities_and_topic(text):
    doc = nlp(text)

    # Extract named entities
    entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]

    # Basic topic detection
    topic_scores = {topic: 0 for topic in TOPIC_KEYWORDS}
    lowered = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                topic_scores[topic] += 1

    topic = max(topic_scores, key=topic_scores.get) if any(topic_scores.values()) else "general"

    return {
        "entities": entities,
        "topic": topic
    }

