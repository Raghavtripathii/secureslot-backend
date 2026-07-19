import uuid
import httpx
import pytest
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.doctor import Doctor

BASE_URL = "http://localhost:8000"


async def _register_and_login(client: httpx.AsyncClient, role: str) -> str:
    """Registers a fresh, uniquely-emailed user of the given role and
    returns their access token. Unique email per call means this test
    can be re-run any number of times without hitting a 'already
    registered' error."""
    email = f"{role}-{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123"
    await client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": f"Test {role.title()}", "role": role},
    )
    response = await client.post("/auth/login", params={"email": email, "password": password})
    return response.json()["access_token"]


@pytest.fixture
async def patient_tokens():
    """Two independently registered and logged-in patients, used to
    simulate two different real users racing for the same slot."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        token_a = await _register_and_login(client, "patient")
        token_b = await _register_and_login(client, "patient")
    return (token_a, token_b)


@pytest.fixture
def sample_doctor_id():
    """Creates a doctor directly via the database, since no
    create-doctor-profile endpoint exists yet. Returns the doctors.id
    (not the user id) needed for the doctor_id field on a booking."""
    db = SessionLocal()
    try:
        email = f"doctor-{uuid.uuid4().hex[:8]}@test.com"
        user = User(
            email=email,
            hashed_password=hash_password("DoctorPass123"),
            full_name="Test Doctor",
            role=UserRole.doctor,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        doctor = Doctor(user_id=user.id, specialty="Cardiology")
        db.add(doctor)
        db.commit()
        db.refresh(doctor)

        return str(doctor.id)
    finally:
        db.close()