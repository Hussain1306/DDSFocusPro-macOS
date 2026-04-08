import os
import sys
from flask import jsonify
from openai import OpenAI
from .veritabani_yoneticisi import VeritabaniYoneticisi
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ✅ Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Schema-aware AI SQL generator
def ask_openai(prompt: str) -> str:
    schema_instruction = """
You are a SQL assistant for a CRM system. Use only these ACTUAL tables and columns:

- tblprojects: id, name, start_date, deadline, status, addedfrom
- tblproject_members: id, project_id, staff_id
- tbltasks: id, name, rel_id, rel_type, status, staffid
- tblstaff: staffid, firstname, lastname, email
- Always SELECT tblprojects.status in the output

Rules:
- Return only SELECT statements.
- DO NOT invent column names.
- Use correct JOINs.
- Match user with: email or CONCAT(firstname, ' ', lastname)
- Project is active if status NOT IN ('finished', 'completed', 'cancelled', 'bitti', 'tamamlandı', 'bitirildi')
"""
    final_prompt = schema_instruction + "\n" + prompt

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": schema_instruction},
            {"role": "user", "content": final_prompt}
        ]
    )
    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    if not sql.lower().startswith("select"):
        raise ValueError("Returned SQL is invalid")
    return sql

# ✅ Execute SQL safely
def execute_sql(sql_query: str, veritabani) -> list:
    try:
        return veritabani.sorgu_calistir(sql_query)
    except Exception as e:
        print(f"[ SQL Error] {e}")
        return []

# ✅ Filter function for active projects
def is_active(status) -> bool:
    """Return True only if project status is active (status = 2)."""
    return status == 2


# ✅ Main project fetching function
def get_ai_filtered_projects(email: str, username: str):
    """Get at least 2 active projects by searching the entire DB using AI-generated queries."""
    if not email and not username:
        return jsonify({"status": "error", "message": "No user info provided."}), 400

    # Database configuration
    db_host = "92.113.22.65"
    db_user = "u906714182_sqlrrefdvdv"
    db_password = "3@6*t:lU"
    db_name = "u906714182_sqlrrefdvdv"
    port = 3306

    # Connect to DB
    veritabani = VeritabaniYoneticisi(db_host, db_user, db_password, db_name, port)
    veritabani.baglanti_olustur()

    print(f"\n AI-driven DB search for: {email or username}")
    active_projects = []
    loop_counter = 0
    max_attempts = 7

    while len(active_projects) < 2 and loop_counter < max_attempts:
        prompt = f"""
Find all active projects where user is involved.
Email: '{email}', Name: '{username}'.
Use correct JOINs (addedfrom, tblproject_members, tbltasks.staffid).
Exclude cancelled, finished, completed projects.
"""
        try:
            sql = ask_openai(prompt)
            print(f"\n🤖 [AI Attempt {loop_counter + 1}]\n{sql}")
            rows = execute_sql(sql, veritabani)

            for row in rows:
                print(f"[RAW ROW] id: {row.get('id')} | status: {row.get('status')}")
                if is_active(row.get("status")):
                    if row.get("id") not in [p.get("id") for p in active_projects]:
                        active_projects.append(row)

        except Exception as e:
            print(f" Error in AI attempt #{loop_counter + 1}: {e}")

        loop_counter += 1

    print(f"\n Final active project count: {len(active_projects)}")
    return jsonify({"status": "success", "projects": active_projects})
