from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.routers.auth import router as auth_router, limiter
from app.routers.appointments import router as appointments_router
from app.routers.doctors import router as doctors_router

app = FastAPI(title="SecureSlot API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(auth_router)
app.include_router(appointments_router)
app.include_router(doctors_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}