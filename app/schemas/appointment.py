import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.appointment import AppointmentStatus

class AppointmentCreate(BaseModel):
    doctor_id: uuid.UUID
    start_time: datetime
    end_time: datetime

class AppointmentOut(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    patient_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus

    class Config:
        from_attributes = True