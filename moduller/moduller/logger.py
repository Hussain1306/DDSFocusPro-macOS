# logger.py
import os, json
from datetime import datetime

def load_json(path):
    try:
        return json.load(open(path, encoding='utf-8'))
    except:
        return []

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_conversation(user_msg, ai_response):
    os.makedirs('logs', exist_ok=True)
    log_path = 'logs/conversations.json'
    data = load_json(log_path)
    data.append({
        "user": user_msg,
        "ai": ai_response,
        "timestamp": datetime.now().isoformat()
    })
    save_json(log_path, data)

