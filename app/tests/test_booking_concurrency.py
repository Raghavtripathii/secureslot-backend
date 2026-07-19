import asyncio
import httpx
import pytest

BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_only_one_of_two_simultaneous_bookings_succeeds(patient_tokens, sample_doctor_id):
    """
    Fires two identical booking requests for the same doctor/slot at
    the same time. Exactly one must succeed (201), the other must be
    rejected (409) — never both succeeding, never both failing.
    """
    payload = {
        "doctor_id": sample_doctor_id,
        "start_time": "2026-09-01T15:00:00Z",
        "end_time": "2026-09-01T15:30:00Z",
    }

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        responses = await asyncio.gather(
            client.post("/appointments/", json=payload, headers={"Authorization": f"Bearer {patient_tokens[0]}"}),
            client.post("/appointments/", json=payload, headers={"Authorization": f"Bearer {patient_tokens[1]}"}),
        )

    status_codes = sorted(r.status_code for r in responses)
    assert status_codes == [201, 409]