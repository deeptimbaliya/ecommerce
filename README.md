# Ecommerce API

A FastAPI-based ecommerce backend with JWT authentication, user management, profile avatar uploads, Redis-backed caching/rate limiting, Celery background jobs, email support, Cloudinary uploads, and Alembic database migrations.

## Tech Stack

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL or any SQLAlchemy-compatible database
- Redis
- Celery
- Cloudinary
- Pytest
- Docker and Docker Compose

## Project Structure



```text
.
+-- app/
|   +-- api/v1/          # API route handlers
|   +-- core/            # config, database, auth, middleware, celery, logging
|   +-- models/          # SQLAlchemy models
|   +-- schemas/         # Pydantic schemas
|   +-- services/        # business logic
|   +-- tasks/           # Celery tasks
|   +-- utils/           # helper utilities
+-- alembic/             # database migrations
+-- tests/               # test suite
+-- main.py              # FastAPI app entrypoint
+-- docker-compose.yml
+-- Dockerfile
+-- requirements.txt
```

## Requirements

- Python 3.13+
- Redis
- A configured database
- Cloudinary account credentials
- SMTP credentials for email sending

## Environment Variables

Create a `.env` file in the project root. Do not commit this file.

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ecommerce
APP_NAME=E-commerce API
DEBUG=True

SECRET_KEY=change-this-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

REDIS_URL=redis://localhost:6379/0

CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_FROM=your-email@example.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run database migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API docs:

```text
http://localhost:8000/docs
```

## Docker Setup

Start the API, Redis, Celery worker, and Celery beat:

```bash
docker compose up --build
```

The API runs on:

```text
http://localhost:8000
```

## Celery

Run the worker manually:

```bash
celery -A app.core.celery_app worker --loglevel=info
```

Run Celery beat manually:

```bash
celery -A app.core.celery_app beat --loglevel=info
```

## Main Endpoints

- `GET /` - root health message
- `GET /api/v1/health` - app and database health check
- `POST /api/v1/auth/register` - register a user
- `POST /api/v1/auth/login` - login and receive tokens
- `POST /api/v1/auth/refresh` - refresh access token
- `POST /api/v1/auth/logout` - revoke refresh token
- `POST /api/v1/auth/forgot-password` - request password reset
- `POST /api/v1/auth/reset-password` - reset password
- `GET /api/v1/users/me` - get current user
- `GET /api/v1/users` - list users, admin only
- `GET /api/v1/users/{user_id}` - get user by ID, admin only
- `POST /api/v1/users` - create user, admin only
- `PUT /api/v1/users/{user_id}` - update user, admin only
- `DELETE /api/v1/users/{user_id}` - delete user, admin only
- `POST /api/v1/users/setavatar` - upload or update profile avatar

## Testing

Run the test suite:

```bash
pytest
```

## Notes

- Local files such as `.env`, `.venv`, logs, cache folders, databases, and archives are ignored by `.gitignore`.
- Keep real secrets out of source control.
- Use Alembic migrations for database schema changes.
