# Deployment

## Current state: fully containerized, cloud-deployment-ready

The full stack FastAPI, PostgreSQL, Redis runs as three orchestrated
Docker containers via `docker-compose.yml`. This is the same artifact that
would be deployed to a cloud VM unchanged: `docker compose up -d --build`
is the entire deployment step, with no cloud-specific configuration baked
into the application itself.

```bash
docker compose up -d --build
docker compose run --rm api alembic upgrade head
docker ps   # api, postgres, redis all "Up"
curl http://localhost:8000/health   # {"status":"ok"}
```

## Why this isn't deployed to a public cloud VM right now

Every major cloud provider (AWS, Oracle Cloud, GCP, Azure) requires a
credit or debit card for identity verification on signup, even for
permanently-free tiers, as standard fraud prevention. I don't currently
have access to a card, and made a deliberate decision not to complete
signup using someone else's card details for a personal learning project.
AWS's India-specific account flow additionally requires Aadhaar-linked
KYC verification through DigiLocker, which I chose not to complete for
the same reason — linking a government identity document to a personal
side project wasn't worth it just to get a badge on a portfolio.

This is a real constraint outside the codebase, not a gap in the
engineering — the architecture below is fully designed and the
containerized artifact is deployment-ready as-is.

## Intended cloud deployment architecture

**Compute:** a single Ubuntu 24.04 VM (AWS EC2 t2.micro or Oracle Cloud's
Always Free tier VM.Standard.E2.1.Micro — either is a drop-in target,
since the deployment step is identical Docker Compose commands).

**Networking — layered firewall, defense in depth:**
- Cloud-level security group / security list: SSH (port 22) restricted to
  a known IP only; API port (8000, or 80 behind a reverse proxy) open
- OS-level firewall (iptables) on the VM itself as a second layer,
  independent of the cloud provider's rules

**Secrets:** a distinct, freshly generated JWT secret and database
credentials live only on the server (`.env`, never committed), separate
from local development secrets.

**Data:** either a managed database (AWS RDS) for automated backups and
patching, or self-hosted Postgres in the same Docker Compose stack for a
project at this scale — a deliberate cost/maintenance tradeoff, not an
oversight.

**Deployment step, identical to local:**
```bash
git clone https://github.com/Raghavtripathii/secureslot-backend.git
cd secureslot-backend
nano .env   # production secrets, not committed
docker compose up -d --build
docker compose run --rm api alembic upgrade head
```

The moment card access is available, deployment is a same-day task — the
containerization and architecture are already built and tested; only the
target machine changes.