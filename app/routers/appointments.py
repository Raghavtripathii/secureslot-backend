from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_role, get_current_user
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentCreate, AppointmentOut
from app.services.booking import book_appointment
from app.models.appointment import Appointment

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.post("/", response_model=AppointmentOut, status_code=201)
def create_appointment(
    payload: AppointmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.patient)),
):
    return book_appointment(
        db=db,
        patient_id=current_user.id,
        doctor_id=payload.doctor_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        ip_address=request.client.host,
    )

@router.get("/me", response_model=list[AppointmentOut])
def my_appointments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # a patient sees only their own; a doctor sees only their own schedule
    if current_user.role == UserRole.patient:
        return db.query(Appointment).filter(Appointment.patient_id == current_user.id).all()
    return db.query(Appointment).filter(Appointment.doctor_id == current_user.id).all()