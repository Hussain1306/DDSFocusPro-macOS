import os
from flask import jsonify
from .veritabani_yoneticisi import VeritabaniYoneticisi

def is_active(status):
    return True  # Ya use `status == 2` if needed

def get_ai_filtered_projects(email: str, username: str):
    if not email and not username:
        return jsonify({"status": "error", "message": "No user info provided."}), 400

    db_host = "92.113.22.65"
    db_user = "u906714182_sqlrrefdvdv"
    db_password = "3@6*t:lU"
    db_name = "u906714182_sqlrrefdvdv"
    port = 3306

    veritabani = VeritabaniYoneticisi(db_host, db_user, db_password, db_name, port)
    veritabani.baglanti_olustur()

    print(f"\n Searching projects for: {email or username}")
    active_projects = []
    seen_ids = set()

    try:
        queries = [
            # 1. Projects created by user
            """
            SELECT DISTINCT tblprojects.*, 'CreatedByUser' as source
            FROM tblprojects
            JOIN tblstaff ON tblprojects.addedfrom = tblstaff.staffid
            WHERE tblstaff.email = %s OR CONCAT(tblstaff.firstname, ' ', tblstaff.lastname) = %s
            """,

            # 2. Projects where user is a member
            """
            SELECT DISTINCT tblprojects.*, 'ProjectMember' as source
            FROM tblprojects
            JOIN tblproject_members ON tblprojects.id = tblproject_members.project_id
            JOIN tblstaff ON tblproject_members.staff_id = tblstaff.staffid
            WHERE tblstaff.email = %s OR CONCAT(tblstaff.firstname, ' ', tblstaff.lastname) = %s
            """,

            # 3. Projects where user created tasks
            """
            SELECT DISTINCT tblprojects.*, 'TaskCreator' as source
            FROM tblprojects
            JOIN tbltasks ON tblprojects.id = tbltasks.rel_id AND tbltasks.rel_type = 'project'
            JOIN tblstaff ON tbltasks.addedfrom = tblstaff.staffid
            WHERE tblstaff.email = %s OR CONCAT(tblstaff.firstname, ' ', tblstaff.lastname) = %s
            """,

            # 4. Projects where user is assigned to a task
            """
            SELECT DISTINCT tblprojects.*, 'AssignedToTask' as source
            FROM tblprojects
            JOIN tbltasks ON tblprojects.id = tbltasks.rel_id AND tbltasks.rel_type = 'project'
            JOIN tbltask_assigned ON tbltasks.id = tbltask_assigned.taskid
            JOIN tblstaff ON tbltask_assigned.staffid = tblstaff.staffid
            WHERE tblstaff.email = %s OR CONCAT(tblstaff.firstname, ' ', tblstaff.lastname) = %s
            """
        ]

        for idx, query in enumerate(queries):
            rows = veritabani.sorgu_calistir(query, (email, username))
            print(f"🔎 Query {idx+1} returned: {len(rows)} rows")

            for row in rows:
                project_id = row.get("id")
                status = row.get("status")

                if project_id not in seen_ids and is_active(status):
                    active_projects.append(row)
                    seen_ids.add(project_id)

    except Exception as e:
        print(f" DB Error: {e}")
        return jsonify({"status": "error", "message": str(e)})

    print(f"\n Final project count: {len(active_projects)}")
    return jsonify({"status": "success", "projects": active_projects})
