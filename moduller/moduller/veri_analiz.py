# moduller/veri_analiz.py

import os
from collections import Counter
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError(" OPENAI_API_KEY not found in environment.")
    return OpenAI(api_key=key)

def run_log_analysis(logs):
    """
    Analyze conversation logs: show top keywords and summarize user interest.
    """
    if not logs:

        
        return {
            "most_frequent_words": [],
            "top_questions": [],
            "summary": " No logs available to analyze."
        }

    # Extract user messages
    questions = [entry['user'].lower() for entry in logs if 'user' in entry]

    # Word frequency analysis
    words = ' '.join(questions).split()
    word_freq = Counter(words).most_common(10)

    # Most asked full questions
    top_questions = Counter(questions).most_common(5)

    # Prepare for LLM summary
    try:
        prompt_questions = "\n".join(q for q, _ in top_questions)
        prompt = (
            "You're an AI assistant that analyzes logs.\n"
            "Here are some frequent questions from users:\n"
            f"{prompt_questions}\n\n"
            " Please provide a short summary of user interest in 3 bullet points."
        )

        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful log analytics assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        summary = response.choices[0].message.content.strip()
    except Exception as e:
        print(" Summary generation failed:", e)
        summary = " Could not generate summary."

    return {
        "most_frequent_words": word_freq,
        "top_questions": top_questions,
        "summary": summary
    }

