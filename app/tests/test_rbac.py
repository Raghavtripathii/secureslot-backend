import httpx
import pytest

BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_patient_cannot_see_another_patients_appointment(patient_tokens, sample_doctor_id):
    
    token_a, token_b = patient_tokens
    payload = {
        "doctor_id": sample_doctor_id,
        "start_time": "2026-11-01T15:00:00Z",
        "end_time": "2026-11-01T15:30:00Z",
    }

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        book_response = await client.post(
            "/appointments/", json=payload, headers={"Authorization": f"Bearer {token_a}"}
        )
        assert book_response.status_code == 201
        appointment_id = book_response.json()["id"]

        a_appointments = await client.get("/appointments/me", headers={"Authorization": f"Bearer {token_a}"})
        b_appointments = await client.get("/appointments/me", headers={"Authorization": f"Bearer {token_b}"})

    a_ids = [a["id"] for a in a_appointments.json()]
    b_ids = [a["id"] for a in b_appointments.json()]

    assert appointment_id in a_ids
    assert appointment_id not in b_ids


@pytest.mark.asyncio
async def test_rate_limit_blocks_after_five_login_attempts():
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        for _ in range(5):
            await client.post("/auth/login", params={"email": "nonexistent@test.com", "password": "wrongpass"})
        sixth = await client.post("/auth/login", params={"email": "nonexistent@test.com", "password": "wrongpass"})

    assert sixth.status_code == 429