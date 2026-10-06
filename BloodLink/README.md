# BloodLink

**BloodLink** is a full-stack blood donation management platform built with Django, designed for the healthcare ecosystem of Nepal. It bridges the gap between blood donors and hospitals by automating donor matching, real-time notifications, donation lifecycle tracking, and blood stock management — including integration with a legacy blood bank system.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Application Modules](#application-modules)
- [Data Flow Summary](#data-flow-summary)
- [Documentation Index](#documentation-index)

---

## Project Overview

BloodLink solves a critical problem in Nepal's healthcare system: the lack of a centralized, real-time platform to connect blood donors with hospitals in need. The system:

- Allows donors to register with their blood group, location, and availability status
- Allows hospitals to post blood requests with urgency levels
- Automatically matches and notifies the nearest eligible donors using GPS-based proximity matching
- Tracks the full donation journey from collection through delivery
- Awards gamification badges to encourage repeat donations
- Integrates with a legacy blood bank database for historical stock data

---

## Key Features

| Feature | Description |
|---|---|
| Donor Registration & Profiles | Full donor onboarding with blood group, location, gender, DOB |
| Hospital Accounts | Separate hospital login and dashboard |
| Blood Request Management | Hospitals post requests with urgency (Normal / Urgent / Critical) |
| GPS-Based Donor Matching | Haversine formula matches nearest eligible donors within Nepal |
| Automated Notifications | In-app + email notifications sent to top 10 matched donors |
| Donation Lifecycle Tracking | 5-stage pipeline: Collected → Processing → Testing → Shipped → Delivered |
| Batch Code Generation | Every donation gets a unique `BL-XXXXXXXXXX` batch code |
| Badge System | Gamification badges: First Timer, Gallon Grad, Decade Donor |
| 90-Day Eligibility Enforcement | Donors cannot donate again within 90 days |
| Blood Stock Management | Track blood inventory with new + legacy system combined view |
| Legacy DB Integration | Read-only access to old blood bank system via Django DB router |
| Brute-Force Protection | django-axes: 5 failed logins trigger a 1-hour lockout |
| Production-Ready Security | HTTPS, HSTS, secure cookies, CSRF protection |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend Framework | Django 6.0.7 |
| REST API | Django REST Framework 3.17.1 |
| Database (Primary) | MySQL (Aiven Cloud in production, local MySQL in development) |
| Database (Legacy) | MySQL (local, read-only) |
| Geocoding | geopy 2.5.0 (Nominatim / OpenStreetMap) |
| Email | Gmail SMTP via Django email backend |
| Static Files | WhiteNoise 6.12.0 (compressed + manifest) |
| WSGI Server | Gunicorn |
| Deployment | Render (cloud platform) |
| Auth Security | django-axes 7.0.1 |
| Environment Config | python-dotenv 1.2.2 |
| Image Handling | Pillow 12.3.0 |

---

## Project Structure

```
BloodLink/
├── miniProject/                  # Django project root
│   ├── accounts/                 # User auth, registration, login
│   ├── blood_requests/           # Hospital blood request management
│   ├── bloodbank/                # Blood stock + legacy DB integration
│   ├── dashboard/                # Donor dashboard and availability toggle
│   ├── donors/                   # Donor profiles, donations, badges
│   ├── hospitals/                # Hospital profiles and dashboard
│   ├── notifications/            # In-app + email notification system
│   ├── miniProject/              # Django settings, URLs, DB router
│   ├── templates/                # HTML templates
│   ├── static/                   # CSS and static assets
│   ├── staticfiles/              # Collected static files (production)
│   ├── .env                      # Environment variables
│   ├── manage.py
│   └── requirements.txt
├── README.md
├── introduction.md
├── api_documentation.md
├── database_design.md
├── deployment.md
├── methodology.md
├── literature_review.md
├── testing.md
└── meeting_notes.md
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- MySQL 8.0+
- pip

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd BloodLink/miniProject

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
# Copy .env.example to .env and fill in your values
# See Environment Variables section below

# 5. Create the MySQL databases
mysql -u root -p
CREATE DATABASE bloodlink_db;
CREATE DATABASE old_blood_system_db;  -- only if using legacy DB locally
EXIT;

# 6. Run migrations
python manage.py migrate

# 7. Create a superuser
python manage.py createsuperuser

# 8. Collect static files
python manage.py collectstatic

# 9. Start the development server
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`.

---

## Environment Variables

All configuration is managed through the `.env` file located at `miniProject/.env`.

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key (required) | `27#sqhk^od5na...` |
| `DEBUG` | Debug mode (`True` / `False`) | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | Full DB URL (overrides individual DB vars) | `mysql://user:pass@host:port/db` |
| `DB_NAME` | Local MySQL database name | `bloodlink_db` |
| `DB_USER` | Local MySQL username | `root` |
| `DB_PASSWORD` | Local MySQL password | `yourpassword` |
| `DB_HOST` | Local MySQL host | `127.0.0.1` |
| `DB_PORT` | Local MySQL port | `3306` |
| `LEGACY_DB_NAME` | Legacy database name | `old_blood_system_db` |
| `LEGACY_DB_USER` | Legacy database username | `root` |
| `LEGACY_DB_PASSWORD` | Legacy database password | `yourpassword` |
| `LEGACY_DB_HOST` | Legacy database host | `127.0.0.1` |
| `LEGACY_DB_PORT` | Legacy database port | `3306` |
| `EMAIL_HOST_USER` | Gmail address for sending emails | `yourapp@gmail.com` |
| `EMAIL_HOST_PASSWORD` | Gmail App Password | `xxxx xxxx xxxx xxxx` |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF | `https://yourdomain.com` |

> **Note:** When `DATABASE_URL` is set, it takes priority over the individual `DB_*` variables. This is used in production on Render.

---

## Application Modules

| Module | Responsibility |
|---|---|
| `accounts` | User registration, login, logout, role detection |
| `donors` | Donor profiles, donation records, badge awards, geocoding |
| `hospitals` | Hospital profiles, hospital-specific dashboard |
| `blood_requests` | Blood request CRUD, donor accept/decline/complete flow |
| `notifications` | In-app notification records, email dispatch |
| `dashboard` | Donor dashboard aggregation, availability toggle |
| `bloodbank` | Blood stock inventory, legacy DB read, import tool |
| `miniProject` | Settings, root URLs, database router |

---

## Data Flow Summary

```
Hospital creates BloodRequest
        ↓
post_save signal fires (blood_requests/signals.py)
        ↓
GPS proximity matching (Haversine) OR district fallback
        ↓
Top 10 eligible donors selected (blood group + 90-day check)
        ↓
Notification created + Email sent to each donor
        ↓
Donor accepts → marks donation complete
        ↓
Hospital confirms blood received
        ↓
Donation record created with batch code BL-XXXXXXXXXX
        ↓
Donor last_donation_date updated, badges awarded
        ↓
BloodRequest units_fulfilled incremented → status = Fulfilled
```

---

## Documentation Index

| Document | Contents |
|---|---|
| [introduction.md](introduction.md) | Project background, problem statement, objectives, scope |
| [methodology.md](methodology.md) | Development methodology, system design, architecture decisions |
| [database_design.md](database_design.md) | Full schema, ER relationships, DB routing strategy |
| [api_documentation.md](api_documentation.md) | All REST API endpoints, request/response formats |
| [deployment.md](deployment.md) | Production deployment guide for Render + Aiven MySQL |
| [testing.md](testing.md) | Test strategy, test cases, results |
| [literature_review.md](literature_review.md) | Related work, existing systems, research background |
| [meeting_notes.md](meeting_notes.md) | Project meeting logs and decisions |
