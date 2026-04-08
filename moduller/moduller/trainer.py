from logger import get_recent_examples
import re

def extract_intents_and_keywords():
    examples = get_recent_examples(limit=10)
    keywords = {}

    for ex in examples:
        user_msg = ex['user'].lower()

        # naive pattern examples
        if 'task' in user_msg:
            keywords.setdefault('task_related', []).append(user_msg)
        if 'status' in user_msg or 'durum' in user_msg:
            keywords.setdefault('status_check', []).append(user_msg)
        if 'summary' in user_msg or 'zet' in user_msg:
            keywords.setdefault('summary', []).append(user_msg)

    return keywords

