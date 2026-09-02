# Docker Deployment Guide

## Quick Start (Docker)

### Prerequisites
- Docker installed: https://www.docker.com/products/docker-desktop
- Docker Compose installed (comes with Docker Desktop)
- Git repository pushed to GitHub

### Option 1: Using Neon PostgreSQL (Recommended - Production)

**Best for:** Production, staging, or development with real data

1. **Build and start containers:**
```bash
docker-compose up -d
```

2. **Run migrations:**
```bash
docker exec service-management-api python manage.py migrate
```

3. **Create superuser (optional):**
```bash
docker exec -it service-management-api python manage.py createsuperuser
```

4. **Access your app:**
- Django admin: http://localhost:8000/admin/
- API docs: http://localhost:8000/api/docs/
- Dashboard: http://localhost:8000/

5. **View logs:**
```bash
docker logs -f service-management-api
```

6. **Stop containers:**
```bash
docker-compose down
```

---

### Option 2: Using Local PostgreSQL with Docker

**Best for:** Full local development without external database

The `docker-compose.yml` includes a PostgreSQL service by default. No changes needed - just run:

```bash
docker-compose up -d
```

This will:
- Start Django web service
- Start local PostgreSQL database
- Connect them automatically

---

## Detailed Docker Commands

### Build Image
```bash
docker build -f backend/Dockerfile -t service-management:latest .
```

### Run Container (without docker-compose)
```bash
docker run -p 8000:8000 \
  -e DEBUG=False \
  -e SECRET_KEY=your-secret-key \
  -e DB_HOST=your-neon-host \
  -e DB_USER=neondb_owner \
  -e DB_PASSWORD=your-password \
  -e DB_NAME=neondb \
  --env-file backend/.env \
  service-management:latest
```

### View Container Logs
```bash
docker-compose logs -f web
docker-compose logs -f postgres
```

### Execute Django Commands in Container
```bash
# Migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Check Django health
docker-compose exec web python manage.py check

# Run shell
docker-compose exec web python manage.py shell
```

### Clean Up
```bash
# Stop and remove containers
docker-compose down

# Remove all containers, images, and volumes
docker-compose down -v
```

---

## Docker File Structure

### Dockerfile
- Python 3.11 slim base image
- Installs system dependencies (PostgreSQL client)
- Installs Python requirements from requirements.txt
- Runs collectstatic for static files
- Exposes port 8000
- Runs Gunicorn with 4 workers

### docker-compose.yml
- **web service:** Django application
  - Port: 8000
  - Volumes: Code and static files
  - Environment: Loaded from .env
  - Depends on: postgres service

- **postgres service:** Local PostgreSQL
  - Port: 5432
  - Volume: postgres_data (persistent)
  - Environment: DB credentials from .env

---

## Environment Variables

The `docker-compose.yml` automatically loads from `backend/.env`. Required variables:

```
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,web
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=your-neon-password
DB_HOST=your-neon-host.neon.tech
DB_PORT=5432
PGSSLMODE=require
PGCHANNELBINDING=require
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME_DAYS=1
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

---

## Using Local PostgreSQL Only

If you want to use **only the local PostgreSQL** (not Neon), update your `.env`:

```
DB_HOST=postgres  # Docker service name
DB_PASSWORD=localdevpassword
```

Then run:
```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
```

---

## Pushing to Docker Hub (Optional)

### 1. Create Docker Hub Account
Go to https://hub.docker.com/signup

### 2. Login to Docker
```bash
docker login
```

### 3. Tag Image
```bash
docker tag service-management:latest YOUR_DOCKER_USERNAME/service-management:latest
```

### 4. Push to Hub
```bash
docker push YOUR_DOCKER_USERNAME/service-management:latest
```

### 5. Run from Docker Hub Anywhere
```bash
docker run -p 8000:8000 \
  --env-file backend/.env \
  YOUR_DOCKER_USERNAME/service-management:latest
```

---

## Troubleshooting

### "Connection refused" to database
- If using Neon: Verify DB_HOST, DB_USER, DB_PASSWORD in .env
- If using local PostgreSQL: Wait for postgres container to start (10-15 seconds)

### Static files not loading (CSS missing)
```bash
docker-compose exec web python manage.py collectstatic --no-input
```

### Permission denied errors
Run docker-compose with sudo:
```bash
sudo docker-compose up -d
```

### Clear everything and start fresh
```bash
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

---

## Next Steps

After Docker deployment, test the same URLs:
- Admin: http://localhost:8000/admin/
- Swagger: http://localhost:8000/api/docs/
- Dashboard: http://localhost:8000/

Everything should work exactly like local development!
