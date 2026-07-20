from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.appointment import Appointment
from app.services.audit import write_audit_log
from app.services.notifications import send_appointment_reminder


def book_appointment(db: Session, patient_id, doctor_id, start_time, end_time, ip_address=None) -> Appointment:

    existing = (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doctor_id, Appointment.start_time == start_time)
        .with_for_update()
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This slot is already booked")

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        start_time=start_time,
        end_time=end_time,
    )
    db.add(appointment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This slot is already booked")

    db.refresh(appointment)
    write_audit_log(db, actor_user_id=patient_id, action="appointment.create", resource_id=str(appointment.id), ip_address=ip_address)
    db.commit()

    send_appointment_reminder.delay(str(appointment.id), "patient@example.com", str(start_time))

    return appointment