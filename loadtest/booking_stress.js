import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 30,
  iterations: 30,
};

const BASE_URL = 'http://localhost:8000';
const TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMGFiYTA4ZC0xYTQwLTQ3MTItOWJhOS04NGVhNWNiOWQzODIiLCJyb2xlIjoicGF0aWVudCIsImV4cCI6MTc4NDcxNTI1Nn0.p0fQxm0oB7go8BkDV8NJV2mEYNn53AwaQrkQ_N5opaU';
const DOCTOR_ID = 'c11e60c4-e0ed-4588-a965-5868fe0d26a3';

export default function () {
  const payload = JSON.stringify({
    doctor_id: DOCTOR_ID,
    start_time: '2026-12-01T15:00:00Z',
    end_time: '2026-12-01T15:30:00Z',
  });
  const params = {
    headers: { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json' },
  };
  const res = http.post(`${BASE_URL}/appointments/`, payload, params);
  check(res, { 'status is 201 or 409': (r) => r.status === 201 || r.status === 409 });
}