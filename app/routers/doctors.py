from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.schemas.doctor import DoctorCreate, DoctorOut

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("/", response_model=list[DoctorOut])
def list_doctors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doctors = db.query(Doctor).join(User, Doctor.user_id == User.id).all()
    return [
        DoctorOut(id=d.id, specialty=d.specialty, full_name=d.user.full_name)
        for d in doctors
    ]


@router.post("/", response_model=DoctorOut, status_code=201)
def create_doctor_profile(
    payload: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.doctor)),
):
    existing = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if existing:
        return DoctorOut(id=existing.id, specialty=existing.specialty, full_name=current_user.full_name)

    doctor = Doctor(user_id=current_user.id, specialty=payload.specialty)
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return DoctorOut(id=doctor.id, specialty=doctor.specialty, full_name=current_user.full_name)