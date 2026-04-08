import openai
import os

# Automatically load from environment (recommended)
openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_program_usage(program_history):
    """
    Given a list of program usage entries, return a short AI summary.
    """
    prompt = f"""
You are a productivity assistant. Given this raw program usage log:
{program_history}

Summarize the user activity in 3–5 bullet points. Group similar programs (e.g. Chrome + Gmail = Emailing).
Mention what the user was likely doing and for how long. Be clear and professional.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a smart work summarizer bot."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content'].strip()

    except Exception as e:
        return f"[AI Summary Error]: {str(e)}"
