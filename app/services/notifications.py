from app.core.celery_app import celery_app

@celery_app.task(name="send_appointment_reminder")
def send_appointment_reminder(appointment_id: str, patient_email: str, start_time: str):
    # In a real deployment this calls an email provider (e.g. Resend, SES).
    # For now, logging it proves the async pipeline works end-to-end.
    print(f"[REMINDER] Appointment {appointment_id} for {patient_email} at {start_time}")