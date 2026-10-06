# Deployment Guide

## BloodLink — Production Deployment on Render + Aiven MySQL

---

## Table of Contents

- [Overview](#overview)
- [Infrastructure Architecture](#infrastructure-architecture)
- [Prerequisites](#prerequisites)
- [Aiven MySQL Setup](#aiven-mysql-setup)
- [Render Deployment](#render-deployment)
- [Environment Variables Configuration](#environment-variables-configuration)
- [Static Files](#static-files)
- [Database Migrations](#database-migrations)
- [Email Configuration](#email-configuration)
- [Security Checklist](#security-checklist)
- [Post-Deployment Verification](#post-deployment-verification)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Rollback Procedure](#rollback-procedure)
- [Local Development Setup](#local-development-setup)
- [Known Issues and Troubleshooting](#known-issues-and-troubleshooting)

---

## Overview

BloodLink is deployed as a Python/Django web application on **Render** (cloud platform) with **Aiven MySQL** as the managed cloud database. Static files are served directly by the application using **WhiteNoise** middleware, eliminating the need for a separate CDN or object storage service.

| Component | Service | Notes |
|---|---|---|
| Web Application | Render Web Service | Gunicorn WSGI server |
| Primary Database | Aiven MySQL (cloud) | Managed, SSL-enabled |
| Legacy Database | Local MySQL | Development only |
| Static Files | WhiteNoise (in-process) | Compressed + manifest |
| Email | Gmail SMTP | App Password authentication |

---

## Infrastructure Architecture

```
Internet
    │
    ▼
Render Web Service
    ├── Gunicorn (WSGI)
    │       └── Django Application
    │               ├── WhiteNoise (static files)
    │               ├── django-axes (brute-force protection)
    │               └── Django ORM
    │                       ├── default DB → Aiven MySQL (cloud)
    │                       └── legacy DB  → Local MySQL (dev only)
    │
    └── Environment Variables (Render Dashboard)
```

---

## Prerequisites

Before deploying, ensure you have:

- A [Render](https://render.com) account
- An [Aiven](https://aiven.io) account with a MySQL service provisioned
- A Gmail account with an App Password generated
- The BloodLink repository pushed to GitHub or GitLab
- Python 3.10+ and pip installed locally for testing

---

## Aiven MySQL Setup

### 1. Create a MySQL Service on Aiven

1. Log in to [Aiven Console](https://console.aiven.io)
2. Click **Create Service** → Select **MySQL**
3. Choose a cloud provider and region (select one close to your users)
4. Select a plan (Hobbyist for development, Startup or higher for production)
5. Name the service (e.g., `mysql-bloodlink`)
6. Click **Create Service** and wait for it to start

### 2. Retrieve Connection Details

From the Aiven service overview page, copy:

- **Service URI** (this is your `DATABASE_URL`)
- Host, Port, Database name, Username, Password (for individual variables)

The Service URI format is:
```
mysql://avnadmin:<password>@<host>:<port>/defaultdb?ssl-mode=REQUIRE
```

### 3. SSL Configuration

Aiven MySQL requires SSL. The `dj-database-url` parser handles this automatically when the `?ssl-mode=REQUIRE` parameter is included in the `DATABASE_URL`.

### 4. Create the Application Database

Connect to Aiven MySQL using a client:

```bash
mysql --host=<aiven-host> --port=<port> --user=avnadmin --password --ssl-mode=REQUIRED
```

The default database `defaultdb` is used directly. No additional database creation is needed.

---

## Render Deployment

### 1. Connect Repository

1. Log in to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub/GitLab repository
4. Select the repository containing BloodLink

### 2. Configure the Web Service

| Setting | Value |
|---|---|
| **Name** | `bloodlink-final` |
| **Region** | Choose closest to Nepal (e.g., Singapore) |
| **Branch** | `main` (or your production branch) |
| **Root Directory** | `BloodLink/miniProject` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --noinput` |
| **Start Command** | `gunicorn miniProject.wsgi:application` |

### 3. Set Environment Variables

In the Render dashboard, navigate to **Environment** and add all required variables (see [Environment Variables Configuration](#environment-variables-configuration) below).

### 4. Deploy

Click **Create Web Service**. Render will:
1. Clone the repository
2. Run the build command (install dependencies + collect static files)
3. Start the Gunicorn server
4. Assign a public URL (e.g., `https://bloodlink-final.onrender.com`)

### 5. Run Database Migrations

After the first deployment, open the Render **Shell** tab and run:

```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## Environment Variables Configuration

Set these in the Render dashboard under **Environment → Environment Variables**.

### Required Variables

| Variable | Value | Notes |
|---|---|---|
| `SECRET_KEY` | A long random string | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` | Must be `False` in production |
| `ALLOWED_HOSTS` | `bloodlink-final.onrender.com` | Your Render domain |
| `DATABASE_URL` | `mysql://avnadmin:<pass>@<host>:<port>/defaultdb?ssl-mode=REQUIRE` | From Aiven service URI |
| `EMAIL_HOST_USER` | `yourapp@gmail.com` | Gmail address |
| `EMAIL_HOST_PASSWORD` | `xxxx xxxx xxxx xxxx` | Gmail App Password |
| `CSRF_TRUSTED_ORIGINS` | `https://bloodlink-final.onrender.com` | Required for CSRF with HTTPS |

### Optional Variables

| Variable | Value | Notes |
|---|---|---|
| `LEGACY_DB_NAME` | `old_blood_system_db` | Only needed if legacy DB is accessible from production |
| `LEGACY_DB_USER` | `root` | Legacy DB credentials |
| `LEGACY_DB_PASSWORD` | `yourpassword` | Legacy DB credentials |
| `LEGACY_DB_HOST` | `127.0.0.1` | Legacy DB host |
| `LEGACY_DB_PORT` | `3306` | Legacy DB port |

> **Note:** In production, the legacy database is typically only accessible locally. If the legacy DB is not reachable from Render, queries to `LegacyBloodStock` will fail silently or raise connection errors. Ensure the `bloodbank` views handle this gracefully.

---

## Static Files

BloodLink uses **WhiteNoise** for static file serving. No separate CDN or S3 bucket is required.

### How It Works

1. During the build step, `python manage.py collectstatic --noinput` copies all static files to `staticfiles/`
2. WhiteNoise middleware serves these files directly from the Django process
3. Files are compressed (gzip) and fingerprinted (content hash in filename) for cache busting

### Configuration in `settings.py`

```python
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

WhiteNoise middleware is placed immediately after `SecurityMiddleware`:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    ...
]
```

---

## Database Migrations

### First Deployment

```bash
# Via Render Shell
python manage.py migrate
```

### Subsequent Deployments

Migrations run automatically if included in the build command. To add migrations to the build:

```
Build Command: pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```

### Creating a Superuser

```bash
# Via Render Shell
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

### Creating Hospital Accounts

Hospital accounts must be created via the Django admin panel:

1. Navigate to `https://bloodlink-final.onrender.com/admin/`
2. Log in with the superuser credentials
3. Create a new `auth_user` with a username and password
4. Create a `HospitalProfile` linked to that user

---

## Email Configuration

BloodLink uses Gmail SMTP for sending blood request notification emails.

### Gmail App Password Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Go to **Google Account → Security → App Passwords**
3. Generate an App Password for "Mail" on "Other (Custom name)"
4. Copy the 16-character password and set it as `EMAIL_HOST_PASSWORD`

### Email Settings in `settings.py`

```python
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
```

### Email Template

The blood request notification email uses the template at:
```
notifications/templates/emails/blood_request_notification.txt
```

> **Important:** The `dashboard_url` in `email_utils.py` is currently hardcoded to `http://127.0.0.1:8000/dashboard/`. Update this to the production URL before deploying:
> ```python
> "dashboard_url": "https://bloodlink-final.onrender.com/dashboard/"
> ```

---

## Security Checklist

The following security settings are automatically applied when `DEBUG=False`:

| Setting | Production Value | Purpose |
|---|---|---|
| `DEBUG` | `False` | Disables debug error pages |
| `SESSION_COOKIE_SECURE` | `True` | Session cookie only sent over HTTPS |
| `SESSION_COOKIE_HTTPONLY` | `True` | Session cookie not accessible via JavaScript |
| `CSRF_COOKIE_SECURE` | `True` | CSRF cookie only sent over HTTPS |
| `CSRF_COOKIE_HTTPONLY` | `True` | CSRF cookie not accessible via JavaScript |
| `SECURE_SSL_REDIRECT` | `True` | All HTTP requests redirected to HTTPS |
| `SECURE_HSTS_SECONDS` | `31536000` (1 year) | HTTP Strict Transport Security |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | `True` | HSTS applies to all subdomains |
| `SECURE_HSTS_PRELOAD` | `True` | Eligible for HSTS preload list |
| `SECURE_PROXY_SSL_HEADER` | `HTTP_X_FORWARDED_PROTO: https` | Trust Render's SSL termination proxy |

### django-axes (Brute-Force Protection)

| Setting | Value | Description |
|---|---|---|
| `AXES_FAILURE_LIMIT` | `5` | Lock after 5 failed login attempts |
| `AXES_COOLOFF_TIME` | `1` (hour) | Lockout duration |
| `AXES_RESET_ON_SUCCESS` | `True` | Reset failure count on successful login |

---

## Post-Deployment Verification

After deploying, verify the following:

### 1. Application Health

```bash
curl https://bloodlink-final.onrender.com/
# Should return HTTP 200 with the home page HTML
```

### 2. Admin Panel

Navigate to `https://bloodlink-final.onrender.com/admin/` and log in with superuser credentials.

### 3. Database Connectivity

In the Render Shell:

```bash
python manage.py dbshell
# Should connect to Aiven MySQL without errors
```

### 4. Static Files

Check that CSS is loading correctly on the home page. WhiteNoise serves files from `/static/`.

### 5. Email

Register a test donor account and create a blood request. Verify that the notification email is received.

### 6. Security Headers

Use [securityheaders.com](https://securityheaders.com) to verify HSTS, X-Frame-Options, and other headers are correctly set.

---

## Monitoring and Maintenance

### Render Logs

Access application logs from the Render dashboard under **Logs**. Key log entries to monitor:

- `✅ EMAIL SENT TO:` — Successful email dispatch
- `❌ EMAIL FAILED FOR:` — Email delivery failure
- Django error tracebacks — Application errors

### Database Maintenance (Aiven)

- Monitor connection count and query performance in the Aiven console
- Set up automated backups in Aiven (available on paid plans)
- Monitor disk usage — blood stock and donation records grow over time

### Dependency Updates

Regularly update dependencies to patch security vulnerabilities:

```bash
pip list --outdated
pip install --upgrade <package>
# Test locally before deploying
```

---

## Rollback Procedure

### Render Rollback

1. Navigate to the Render dashboard → **Deploys**
2. Find the last known-good deployment
3. Click **Rollback to this deploy**

### Database Rollback

If a migration needs to be reversed:

```bash
# Via Render Shell
python manage.py migrate <app_name> <previous_migration_number>
# Example: python manage.py migrate donors 0003
```

---

## Local Development Setup

### 1. Clone and Install

```bash
git clone <repository-url>
cd BloodLink/miniProject
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure `.env`

Create `miniProject/.env` with:

```env
SECRET_KEY=your-local-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=bloodlink_db
DB_USER=root
DB_PASSWORD=yourpassword
DB_HOST=127.0.0.1
DB_PORT=3306

LEGACY_DB_NAME=old_blood_system_db
LEGACY_DB_USER=root
LEGACY_DB_PASSWORD=yourpassword
LEGACY_DB_HOST=127.0.0.1
LEGACY_DB_PORT=3306

EMAIL_HOST_USER=yourapp@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 3. Create Databases and Migrate

```bash
mysql -u root -p -e "CREATE DATABASE bloodlink_db;"
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
python manage.py runserver
```

---

## Known Issues and Troubleshooting

### Issue: `SECRET_KEY is not configured` on startup

**Cause:** The `.env` file is not being loaded or `SECRET_KEY` is missing.

**Fix:** Ensure `.env` exists at `miniProject/.env` and contains a valid `SECRET_KEY`.

---

### Issue: Database connection refused

**Cause:** MySQL is not running or credentials are incorrect.

**Fix:**
```bash
# Check MySQL is running
mysql -u root -p
# Verify DB_NAME, DB_USER, DB_PASSWORD in .env
```

---

### Issue: Static files not loading in production

**Cause:** `collectstatic` was not run during the build.

**Fix:** Ensure the build command includes `python manage.py collectstatic --noinput`.

---

### Issue: Email not sending

**Cause:** Gmail App Password is incorrect or 2FA is not enabled.

**Fix:** Regenerate the App Password in Google Account settings and update `EMAIL_HOST_PASSWORD`.

---

### Issue: Legacy DB queries failing

**Cause:** The legacy database is not accessible from the deployment environment, or the table name `old_blood_table` does not match the actual legacy schema.

**Fix:**
1. Run `python manage.py inspectdb --database=legacy` to inspect the actual schema
2. Update `LegacyBloodStock.Meta.db_table` to match the actual table name
3. If the legacy DB is not accessible in production, wrap legacy queries in try/except blocks

---

### Issue: CSRF verification failed

**Cause:** `CSRF_TRUSTED_ORIGINS` does not include the production domain.

**Fix:** Add the production URL to `CSRF_TRUSTED_ORIGINS` in environment variables:
```
CSRF_TRUSTED_ORIGINS=https://bloodlink-final.onrender.com
```
