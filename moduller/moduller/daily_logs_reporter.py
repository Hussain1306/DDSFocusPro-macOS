"""
Daily Logs Reporter Module

This module handles the generation and upload of daily logs reports for employees.
It creates structured JSON reports and uploads them to S3 with the folder structure:
logs/{date}/{email}/daily_activity_report_{timestamp}.json
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from .s3_uploader import upload_daily_logs_report
from .veritabani_yoneticisi import VeritabaniYoneticisi

logger = logging.getLogger(__name__)

class DailyLogsReporter:
    def __init__(self):
        self.db = VeritabaniYoneticisi()
        
    def get_employee_daily_logs(self, email, target_date=None):
        """
        Get all logs for a specific employee for a specific date
        
        Args:
            email: Employee email
            target_date: Date string (YYYY-MM-DD), defaults to today
            
        Returns:
            dict: Structured logs data
        """
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(" Fetching daily logs for %s on %s", email, target_date)
        
        try:
            # Get employee info
            staff_query = "SELECT id, name, email FROM staff WHERE email = ?"
            staff_result = self.db.sorgu_calistir(staff_query, (email,))
            
            if not staff_result:
                logger.warning(" Employee not found: %s", email)
                return None
            
            staff_info = staff_result[0]
            staff_id = staff_info[0]
            staff_name = staff_info[1]
            
            # Get all tasks for the date
            start_date = f"{target_date} 00:00:00"
            end_date = f"{target_date} 23:59:59"
            
            tasks_query = """
            SELECT 
                t.id,
                t.task_id,
                t.staff_id,
                t.start_time,
                t.end_time,
                t.note,
                t.hourly_rate,
                tasks.task_name
            FROM timesheets t
            LEFT JOIN tasks ON t.task_id = tasks.id
            WHERE t.staff_id = ? 
            AND datetime(t.start_time) >= datetime(?)
            AND datetime(t.start_time) <= datetime(?)
            ORDER BY t.start_time ASC
            """
            
            tasks_result = self.db.sorgu_calistir(tasks_query, (staff_id, start_date, end_date))
            
            # Structure the data
            daily_report = {
                "report_metadata": {
                    "employee_email": email,
                    "employee_name": staff_name,
                    "employee_id": staff_id,
                    "report_date": target_date,
                    "generated_at": datetime.now().isoformat(),
                    "total_tasks": len(tasks_result) if tasks_result else 0
                },
                "daily_summary": {
                    "total_working_hours": 0,
                    "total_tasks_completed": len(tasks_result) if tasks_result else 0,
                    "first_task_start": None,
                    "last_task_end": None,
                    "total_earnings": 0
                },
                "tasks": []
            }
            
            if tasks_result:
                total_seconds = 0
                total_earnings = 0
                
                for task in tasks_result:
                    task_id, task_ref_id, staff_id, start_time, end_time, note, hourly_rate, task_name = task
                    
                    # Calculate duration
                    if start_time and end_time:
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        duration_seconds = (end_dt - start_dt).total_seconds()
                        duration_hours = duration_seconds / 3600
                        total_seconds += duration_seconds
                        
                        # Calculate earnings
                        if hourly_rate:
                            task_earnings = duration_hours * float(hourly_rate)
                            total_earnings += task_earnings
                        else:
                            task_earnings = 0
                    else:
                        duration_seconds = 0
                        duration_hours = 0
                        task_earnings = 0
                    
                    # Add task details
                    task_data = {
                        "task_id": task_id,
                        "task_reference_id": task_ref_id,
                        "task_name": task_name,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_seconds": duration_seconds,
                        "duration_hours": round(duration_hours, 2),
                        "note": note,
                        "hourly_rate": float(hourly_rate) if hourly_rate else 0,
                        "task_earnings": round(task_earnings, 2)
                    }
                    
                    daily_report["tasks"].append(task_data)
                
                # Update summary
                daily_report["daily_summary"]["total_working_hours"] = round(total_seconds / 3600, 2)
                daily_report["daily_summary"]["total_earnings"] = round(total_earnings, 2)
                daily_report["daily_summary"]["first_task_start"] = tasks_result[0][3]
                daily_report["daily_summary"]["last_task_end"] = tasks_result[-1][4]
            
            logger.info(" Generated daily report for %s: %d tasks, %.2f hours", 
                       email, daily_report["daily_summary"]["total_tasks_completed"],
                       daily_report["daily_summary"]["total_working_hours"])
            
            return daily_report
            
        except Exception as e:
            logger.error(" Error generating daily logs for %s: %s", email, e)
            return None
    
    def generate_and_upload_daily_report(self, email, target_date=None):
        """
        Generate and upload daily report for a specific employee
        
        Args:
            email: Employee email
            target_date: Date string (YYYY-MM-DD), defaults to today
            
        Returns:
            dict: Upload result with status and URL
        """
        logger.info(" Generating and uploading daily report for %s", email)
        
        try:
            # Generate the report
            daily_logs = self.get_employee_daily_logs(email, target_date)
            
            if not daily_logs:
                return {
                    "status": "error",
                    "message": f"No data found for {email} on {target_date or 'today'}",
                    "url": None
                }
            
            # Upload to S3
            url = upload_daily_logs_report(email, daily_logs, "daily_activity")
            
            if url:
                return {
                    "status": "success",
                    "message": f"Daily report uploaded successfully for {email}",
                    "url": url,
                    "report_summary": daily_logs["daily_summary"]
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to upload daily report for {email}",
                    "url": None
                }
                
        except Exception as e:
            logger.error(" Error in generate_and_upload_daily_report: %s", e)
            return {
                "status": "error",
                "message": f"Error processing daily report: {str(e)}",
                "url": None
            }
    
    def generate_all_employees_daily_reports(self, target_date=None):
        """
        Generate and upload daily reports for all employees
        
        Args:
            target_date: Date string (YYYY-MM-DD), defaults to today
            
        Returns:
            list: List of upload results for each employee
        """
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(" Generating daily reports for all employees on %s", target_date)
        
        try:
            # Get all active employees
            employees_query = "SELECT DISTINCT email, name FROM staff WHERE email IS NOT NULL AND email != ''"
            employees_result = self.db.sorgu_calistir(employees_query)
            
            if not employees_result:
                logger.warning(" No employees found in database")
                return []
            
            results = []
            employees_data = {}
            
            # Generate reports for each employee
            for employee in employees_result:
                email, name = employee
                logger.info(" Processing employee: %s (%s)", name, email)
                
                daily_logs = self.get_employee_daily_logs(email, target_date)
                
                if daily_logs:
                    employees_data[email] = daily_logs
                else:
                    logger.info(" No data found for %s on %s", email, target_date)
            
            # Upload to S3 individually
            if employees_data:
                for email, logs_data in employees_data.items():
                    try:
                        enhanced_logs = {
                            "report_date": target_date,
                            "employee_email": email,
                            "generated_at": datetime.now().isoformat(),
                            "total_entries": len(logs_data) if isinstance(logs_data, list) else 1,
                            "data": logs_data
                        }
                        
                        url = upload_daily_logs_report(email, enhanced_logs, "daily_activity")
                        
                        if url:
                            results.append({
                                "email": email,
                                "status": "success",
                                "url": url,
                                "entries_count": enhanced_logs["total_entries"]
                            })
                            logger.info("Uploaded logs for %s: %d entries", email, enhanced_logs["total_entries"])
                        else:
                            results.append({
                                "email": email,
                                "status": "failed",
                                "url": None,
                                "error": "Upload failed"
                            })
                            logger.error("Failed to upload logs for %s", email)
                    except Exception as e:
                        results.append({
                            "email": email,
                            "status": "error",
                            "url": None,
                            "error": str(e)
                        })
                        logger.error("Error uploading logs for %s: %s", email, e)
            
            logger.info(" Daily reports generation complete: %d employees processed", len(results))
            return results
            
        except Exception as e:
            logger.error(" Error generating all employees daily reports: %s", e)
            return []
    
    def get_employee_logs_summary(self, email, days_back=7):
        """
        Get summary of employee logs for the last N days
        
        Args:
            email: Employee email
            days_back: Number of days to look back (default: 7)
            
        Returns:
            dict: Summary data
        """
        logger.info(" Getting %d-day summary for %s", days_back, email)
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Get employee info
            staff_query = "SELECT id, name, email FROM staff WHERE email = ?"
            staff_result = self.db.sorgu_calistir(staff_query, (email,))
            
            if not staff_result:
                return None
            
            staff_info = staff_result[0]
            staff_id = staff_info[0]
            staff_name = staff_info[1]
            
            # Get tasks summary
            summary_query = """
            SELECT 
                DATE(t.start_time) as work_date,
                COUNT(*) as tasks_count,
                SUM(
                    CASE 
                        WHEN t.end_time IS NOT NULL 
                        THEN (julianday(t.end_time) - julianday(t.start_time)) * 24 
                        ELSE 0 
                    END
                ) as total_hours,
                SUM(
                    CASE 
                        WHEN t.end_time IS NOT NULL AND t.hourly_rate IS NOT NULL
                        THEN ((julianday(t.end_time) - julianday(t.start_time)) * 24) * t.hourly_rate
                        ELSE 0 
                    END
                ) as total_earnings
            FROM timesheets t
            WHERE t.staff_id = ? 
            AND DATE(t.start_time) >= DATE(?)
            AND DATE(t.start_time) <= DATE(?)
            GROUP BY DATE(t.start_time)
            ORDER BY work_date DESC
            """
            
            summary_result = self.db.sorgu_calistir(summary_query, (
                staff_id, 
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            ))
            
            daily_summaries = []
            total_hours = 0
            total_earnings = 0
            total_tasks = 0
            
            if summary_result:
                for row in summary_result:
                    work_date, tasks_count, hours, earnings = row
                    daily_summaries.append({
                        "date": work_date,
                        "tasks_count": tasks_count or 0,
                        "hours": round(hours or 0, 2),
                        "earnings": round(earnings or 0, 2)
                    })
                    total_hours += hours or 0
                    total_earnings += earnings or 0
                    total_tasks += tasks_count or 0
            
            summary = {
                "employee_email": email,
                "employee_name": staff_name,
                "period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "days_back": days_back
                },
                "totals": {
                    "total_working_days": len(daily_summaries),
                    "total_hours": round(total_hours, 2),
                    "total_earnings": round(total_earnings, 2),
                    "total_tasks": total_tasks,
                    "average_hours_per_day": round(total_hours / max(len(daily_summaries), 1), 2)
                },
                "daily_breakdown": daily_summaries
            }
            
            return summary
            
        except Exception as e:
            logger.error(" Error getting employee logs summary: %s", e)
            return None


# Convenience functions for easy use
def generate_daily_report_for_employee(email, target_date=None):
    """Convenience function to generate daily report for one employee"""
    reporter = DailyLogsReporter()
    return reporter.generate_and_upload_daily_report(email, target_date)

def generate_daily_reports_for_all_employees(target_date=None):
    """Convenience function to generate daily reports for all employees"""
    reporter = DailyLogsReporter()
    return reporter.generate_all_employees_daily_reports(target_date)

def get_employee_weekly_summary(email, days_back=7):
    """Convenience function to get employee weekly summary"""
    reporter = DailyLogsReporter()
    return reporter.get_employee_logs_summary(email, days_back)


if __name__ == "__main__":
    # Test the module
    logging.basicConfig(level=logging.INFO)
    
    reporter = DailyLogsReporter()
    
    # Test with a sample email (replace with actual email from your database)
    test_email = "haseebcodejourney@gmail.com"
    
    # Generate today's report
    result = reporter.generate_and_upload_daily_report(test_email)
    print(f"Single employee result: {result}")
    
    # Generate reports for all employees
    all_results = reporter.generate_all_employees_daily_reports()
    print(f"All employees results: {all_results}")
