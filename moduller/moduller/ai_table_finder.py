import os
import openai
from dotenv import load_dotenv
from veritabani_yoneticisi import VeritabaniYoneticisi  # Make sure this uses pymysql
import re

# --- Load environment variables ---
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("DB_PORT", 3306))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# --- Ask GPT if a specific table matches ---
def ask_openai_about_table(table_name, columns):
    prompt = f"""
You are a MySQL expert.

The app interface shows this table:

| Member | Start Time | End Time | Time Spent |

Here is one candidate:
- Table name: {table_name}
- Columns: {columns}

Does this table store timesheet data for the UI above?

 If YES, reply only: YES: {table_name}  
 If NO, reply only: NO
(No explanation, no markdown.)
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Only reply YES: <table_name> or NO."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content'].strip()

# --- Let GPT suggest the best table and SQL ---
def ask_openai_for_query(all_table_names):
    prompt = f"""
You're a MySQL database assistant.

I need to show a table in the UI with columns:
- Member
- Start Time
- End Time
- Time Spent

Here are all available tables: {all_table_names}

Please write a SELECT query that fetches these fields from the most relevant table.

If column names differ, use aliases (AS). 
Return ONLY the SQL query  no explanation, no markdown.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You're a helpful SQL generator. Only return raw SQL SELECT queries."},
            {"role": "user", "content": prompt}
        ]
    )
    sql = response['choices'][0]['message']['content'].strip()
    print(f"\n GPT-Generated SQL:\n{sql}")
    return sql

# --- Extract table name from GPT's SQL ---
def extract_table_name(sql_query):
    match = re.search(r'FROM\s+`?(\w+)`?', sql_query, re.IGNORECASE)
    return match.group(1) if match else None

# --- Main Table Detection ---
def find_timesheet_table():
    print(" Starting AI-based Timesheet Table Detection...")

    db = VeritabaniYoneticisi(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
    db.baglanti_olustur()

    if not db.baglanti_testi():
        print(" Failed to connect to the database.")
        return None

    try:
        tables = db.sorgu_calistir("SHOW TABLES")
        table_names = [list(row.values())[0] for row in tables]
        print(f" Tables found: {table_names}")
    except Exception as e:
        print(f" Error retrieving tables: {e}")
        return None

    # First: try to find based on structure
    for idx, table in enumerate(table_names):
        try:
            columns_result = db.sorgu_calistir(f"SHOW COLUMNS FROM `{table}`")
            columns = [col["Field"] for col in columns_result]
            print(f" ({idx+1}/{len(table_names)}) Checking: {table}  {columns}")

            ai_response = ask_openai_about_table(table, columns)
            print(f" GPT Response: {ai_response}")

            if ai_response.startswith("YES:"):
                selected_table = ai_response.split("YES:")[1].strip()
                print(f"\n GPT Selected Timesheet Table by structure: {selected_table}")
                return selected_table

        except Exception as e:
            print(f" Error processing table '{table}': {e}")

    print(" No direct match found. Trying smart SQL guess...\n")

    # Fallback: Let GPT generate SELECT query and infer table
    try:
        generated_sql = ask_openai_for_query(table_names)
        guessed_table = extract_table_name(generated_sql)
        if guessed_table:
            print(f"\n GPT Guessed Timesheet Table from SQL: {guessed_table}")
            return guessed_table
        else:
            print(" Couldn't detect table name from SQL.")
    except Exception as e:
        print(f" GPT SQL generation failed: {e}")

    return None

# --- CLI Runner ---
if __name__ == "__main__":
    try:
        selected_table = find_timesheet_table()
        if selected_table:
            print(f"\n Final Selected Table: {selected_table}")
        else:
            print("\n No table matched the required structure.")
    except Exception as e:
        print(f" Fatal error: {e}")
    input("\nPress ENTER to exit...")

