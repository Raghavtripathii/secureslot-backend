import uuid
from pydantic import BaseModel

class DoctorCreate(BaseModel):
    specialty: str

class DoctorOut(BaseModel):
    id: uuid.UUID
    specialty: str
    full_name: str

    class Config:
        from_attributes = True