# SecureSlot Backend

A security-hardened, concurrency-safe clinic appointment booking API. Built
to answer one specific question: what happens when two patients try to
book the same doctor's slot at the exact same instant — and prove, not
just claim, that the answer is "exactly one of them wins."

`FastAPI` `PostgreSQL` `SQLAlchemy` `Redis` `Celery` `Docker` `GitHub Actions` `k6`

---

## The core problem this project solves

Most CRUD APIs never get tested under real concurrent load. This one is
built around a single hard engineering problem — **preventing double
bookings under race conditions** — and every other piece (auth, RBAC,
audit logging, background jobs, CI, load testing) exists to support that
core guarantee being genuinely trustworthy, not just claimed.

### The fix — two independent layers

```python
existing = (
    db.query(Appointment)
    .filter(Appointment.doctor_id == doctor_id, Appointment.start_time == start_time)
    .with_for_update()
    .first()
)
```

1. **Row-level locking** (`SELECT ... FOR UPDATE`) — when checking slot
   availability, Postgres locks any existing row for that doctor/time so
   a second concurrent request has to wait its turn instead of racing.
2. **A database-enforced unique constraint** — `UniqueConstraint("doctor_id", "start_time")`
   is the last line of defense: even if two transactions somehow both get
   past the lock check, Postgres itself physically refuses the second
   `INSERT`. The application catches that as an `IntegrityError` and
   returns a clean `409 Conflict`.

Both layers exist deliberately — locking early avoids wasted work and
gives a predictable error path; the constraint guarantees correctness
even if the locking logic were ever weakened by a future change.

### Proof, not a claim — three independent levels of evidence

**1. Manual, real concurrent requests** (two different patients, same
slot, fired at the same instant via backgrounded `curl`):
```
HTTP/1.1 201 Created
HTTP/1.1 409 Conflict
```
Verified directly against the database afterward — exactly one row
exists for that slot, not zero, not two.

**2. Automated regression test**, run on every push via CI:
```python
responses = await asyncio.gather(
    client.post("/appointments/", json=payload, headers={"Authorization": f"Bearer {patient_tokens[0]}"}),
    client.post("/appointments/", json=payload, headers={"Authorization": f"Bearer {patient_tokens[1]}"}),
)
assert sorted(r.status_code for r in responses) == [201, 409]
```
`app/tests/test_booking_concurrency.py::test_only_one_of_two_simultaneous_bookings_succeeds — PASSED`

**3. Load test at real scale** — 30 simultaneous requests to the exact
same slot, via k6:
```
checks_succeeded: 100.00%   30 out of 30
✓ status is 201 or 409
```
One winner, twenty-nine correctly rejected, zero crashes, zero duplicate
bookings — under genuine concurrent load, not a two-request toy example.

---

## Architecture

**Auth & RBAC.** JWT-based auth (`python-jose`), bcrypt password hashing,
three roles (patient / doctor / admin) enforced through a reusable
FastAPI dependency:
```python
def require_role(*allowed_roles: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return current_user
    return role_checker
```
RBAC is enforced at the **data query level**, not just the endpoint —
`GET /appointments/me` filters by `patient_id` or `doctor_id` depending
on the caller's role, so one patient's SQL query can never return another
patient's data. Verified in `app/tests/test_rbac.py`.

Doctor profiles are self-service — a registered doctor calls
`POST /doctors/` to create their own listing, and any authenticated user
can browse the roster via `GET /doctors/`, no manual database access
required.

**Security hardening, informed by hands-on offensive testing.** Every
decision below traces back to a specific vulnerability I found and
exploited while building
[vault-notes-vapt](https://github.com/Raghavtripathii/vault-notes-vapt),
a companion project where I deliberately broke a secure app to write a
real penetration-test report:
- **UUID primary keys**, not sequential integers — makes IDOR-style
  enumeration (`/users/2` → `/users/3`) impossible by design
- **bcrypt**, never SHA-256, for password hashing — deliberately slow,
  built-in salting, resistant to brute-force at scale
- **Rate-limited login** (`5/minute` via `slowapi`) — the exact brute-force
  surface from a login endpoint with no limit, now closed
- **Atomic audit logging** — every appointment creation writes an audit
  log entry in the *same transaction* as the action itself, so the log
  and the action succeed or fail together, never drifting out of sync

**Async background work.** Booking reminders run via Celery + Redis,
decoupled from the request/response cycle — the API responds instantly
to the patient; the reminder job runs separately, in its own worker
process, verified end-to-end with real logs showing the task received,
processed, and succeeded independently of the booking request.

**Testing.** Real integration tests running against a genuine Postgres
instance (not SQLite) — required, since the `FOR UPDATE` locking behavior
this project depends on is Postgres-specific and would silently pass
under SQLite even if broken. Covers booking concurrency, RBAC data
isolation, and rate-limit enforcement.

**CI.** GitHub Actions spins up a disposable Postgres service container
on every push, runs Alembic migrations against it, starts the API, and
runs the full test suite — a step up from testing only against SQLite,
since CI now exercises the exact locking behavior the whole project is
built around.

---

## Tech stack

| Layer | Choice |
|---|---|
| API framework | FastAPI 0.115, Uvicorn |
| Database | PostgreSQL 16, SQLAlchemy 2.0, Alembic |
| Auth | python-jose (JWT), passlib + bcrypt |
| Rate limiting | slowapi |
| Background jobs | Celery 5.4, Redis 7 |
| Testing | Pytest, pytest-asyncio, httpx |
| Load testing | k6 |
| CI | GitHub Actions (Postgres + Redis service containers) |
| Containerization | Docker, Docker Compose |

---

## Load test results (measured, not estimated)

**Baseline — 50 concurrent users, ramping over 40s, hitting `/health`:**
```
checks_succeeded: 100.00%   1067 out of 1067
http_req_duration: avg=2.25ms  p(95)=3.56ms  max=20.7ms
http_req_failed:   0.00%
```

**Concurrency stress — 30 simultaneous identical booking requests to the
same doctor/slot:**
```
checks_succeeded: 100.00%   30 out of 30   (✓ status is 201 or 409)
http_req_duration: avg=136.64ms  p(95)=159.62ms  max=212.53ms
```
Note: k6's built-in `http_req_failed` metric counts any non-2xx response
as "failed" by default, which is why it shows ~97% here — that's counting
the 29 correctly-issued `409 Conflict` rejections, not real failures. The
custom `check()` above (`status is 201 or 409`) is the metric that
actually reflects correctness, and it's 100%.

Run locally:
```bash
k6 run loadtest/booking_load.js
k6 run loadtest/booking_stress.js
```

---

## Running it locally

```bash
git clone https://github.com/Raghavtripathii/secureslot-backend.git
cd secureslot-backend
cp .env.example .env   # fill in a generated JWT secret
docker compose up -d --build
docker compose run --rm api alembic upgrade head
curl http://localhost:8000/health   # {"status":"ok"}
```
API docs: `http://localhost:8000/docs`

Run the test suite:
```bash
pytest -v
```

---

## Deployment

The full stack is fully containerized and deployment-ready as-is —
`docker compose up -d --build` is the entire deployment step, with no
cloud-specific configuration in the application itself. It is **not
currently deployed to a public cloud VM**: every major provider (AWS,
Oracle Cloud, GCP, Azure) requires card-based identity verification even
for free tiers, and AWS's India account flow additionally requires
Aadhaar-linked KYC. I made a deliberate call not to work around either
constraint for a personal project. The full intended architecture —
layered firewall rules, SSH key management, secrets handling, deployment
commands — is documented in [`DEPLOYMENT.md`](./DEPLOYMENT.md).

---

## What I'd build next

- Real email delivery (Resend/SES) instead of the current logged
  placeholder reminder
- Frontend: in progress at
  [secureslot-frontend](https://github.com/Raghavtripathii/secureslot-frontend) —
  Next.js + TypeScript, consuming this API directly through server-side
  proxy routes so the JWT never touches client-side JavaScript

## License

Copyright © 2026 Raghvendra Tripathi. This project is licensed under the
[MIT License](./LICENSE) — free to use, modify, and distribute with
attribution.