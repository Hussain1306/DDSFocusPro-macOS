import openai
import os
from .veritabani_yoneticisi import VeritabaniYoneticisi

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_ai_response(prompt: str):
    response = openai.ChatCompletion.create(
        model="gpt-4",  # or "gpt-3.5-turbo" if preferred
        messages=[
            {"role": "system", "content": "You are an assistant that converts user questions into SQL queries for a Perfex CRM database."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

def execute_sql_from_prompt(prompt):
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    port = int(os.getenv("DB_PORT"))

    veritabani = VeritabaniYoneticisi(db_host, db_user, db_password, db_name, port)
    veritabani.baglanti_olustur()

    sql_prompt = f"""
    Given this user request, generate a simple SQL SELECT statement using tblprojects, tbltasks, and tblstaff.
    Ensure WHERE clauses filter by email, username, or staffid where appropriate.
    ---
    {prompt}
    ---
    Just return SQL only. No explanation.
    """

    sql_query = get_ai_response(sql_prompt)

    try:
        result = veritabani.sorgu_calistir(sql_query)

        #  Print results in terminal
        print(f"[AI SQL Query]: {sql_query}")
        print("[Query Results]:")
        if isinstance(result, list):
            for row in result:
                print(row)
        else:
            print(result)

        return {"query": sql_query, "result": result}
    except Exception as e:
        print(f"[ERROR executing query]: {sql_query}")
        print(f"[ERROR Message]: {str(e)}")
        return {"error": str(e), "query": sql_query}

