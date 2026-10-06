# BloodLink System — Detailed Technical Report

---

## 1. System Overview

BloodLink is a Django-based blood donation management platform for Nepal. It connects blood donors with hospitals, tracks the full lifecycle of a blood donation, and integrates with a legacy blood bank system.

---

## 2. Architecture

```
Django 6.0.7 (Python)
├── 8 Django Apps
├── 2 Databases (default + legacy)
├── REST API (DRF)
├── Email Notifications (Gmail SMTP)
└── Deployed on Render (Aiven MySQL cloud DB)
```

---

## 3. Database Architecture & Routing

### Two Databases

| Database | Variable | Purpose |
|---|---|---|
| `default` | `DATABASE_URL` (Aiven MySQL cloud) or local MySQL | All app data |
| `legacy` | `LEGACY_DB_*` env vars (local MySQL) | Read-only legacy blood bank |

### Database Router — `LegacyRouter`

The [db_routers.py](c:\Users\HP\Downloads\bloodlink-final\BloodLink\miniProject\miniProject\db_routers.py) controls routing:

- Models with `managed = False` → read from `legacy` DB, writes blocked
- All other models → read/write on `default` DB
- Migrations for `bloodbank` and `myapp` only run on `default`

---

## 4. Data Flow & Tracing

### Full Donation Lifecycle

```
[Hospital creates BloodRequest]
        │
        ▼
[post_save signal fires] ← blood_requests/signals.py
        │
        ├─ Has lat/lon? → Haversine distance matching (donors.utils.calculate_distance)
        └─ No lat/lon?  → Same-district fallback filter
        │
        ▼
[Top 10 eligible donors selected]
  - blood_group match
  - is_available = True
  - last_donation_date >= 90 days ago (is_eligible())
        │
        ▼
[Notification created] ← notifications/services.py → Notification table
[Email sent]           ← notifications/email_utils.py → Gmail SMTP
        │
        ▼
[Donor sees notification on dashboard]
        │
        ├─ Accepts → notification.response = "Accepted", donor.is_available = False
        ├─ Declines → notification.response = "Declined"
        │
        ▼
[Donor marks donation complete]
  → notification.response = "Completed"
        │
        ▼
[Hospital confirms blood received] ← ConfirmBloodReceivedView
  → Donation record created (with auto-generated batch_code BL-XXXXXXXXXX)
  → donor.last_donation_date = today
  → blood_request.units_fulfilled += 1
  → If units_fulfilled >= units_required → status = "Fulfilled"
        │
        ▼
[Donation status tracking] ← Donation.journey_steps property
  collected → processing → testing → shipped → delivered
        │
        ▼
[Badge awarded on "delivered"] ← DonorProfile.award_badges()
  - first_timer (1 donation)
  - gallon_grad (8 donations)
  - decade_donor (logic placeholder)
```

### Geolocation Flow

```
[DonorProfile.save() or BloodRequest.save()]
        │
        ▼
[Location fields changed?]
        │
        ▼
[donors/services.py → get_coordinates()]
  Uses geopy/Nominatim (OpenStreetMap)
  Tries: area+municipality+district → area+district → municipality+district
        │
        ▼
[latitude/longitude stored on model]
        │
        ▼
[Used in signal for proximity-based donor matching]
```

### Legacy Blood Bank Data Flow

```
[bloodbank/views.py → stock_list()]
        │
        ├─ BloodStock.objects.all()       → default DB (new system)
        └─ LegacyBloodStock.objects.all() → legacy DB (read-only, unmanaged)
        │
        ▼
[Combined view: new_qty + legacy_qty = total_qty]
        │
        ▼
[import_legacy_to_new()] → copies legacy records into BloodStock (default DB)
```

---

## 5. App-by-App Breakdown

### `accounts`
- Models: `UserProfile` (OneToOne → Django `User`, stores role)
- Views: register, login, logout, home
- On register: creates `User` + `UserProfile` + `DonorProfile` atomically

### `donors`
- Models: `DonorProfile` (OneToOne → User), `Donation`, `DonorBadge`
- Key logic:
  - `is_eligible()` — 90-day cooldown check
  - `award_badges()` — triggered when Donation status = "delivered"
  - `save()` — auto-geocodes on location field change
  - `journey_steps` / `progress_percentage` — donation tracking pipeline
  - `batch_code` — auto-generated UUID `BL-XXXXXXXXXX`

### `hospitals`
- Models: `HospitalProfile` (OneToOne → User)
- Views: hospital login, hospital dashboard (shows all requests + donor responses)

### `blood_requests`
- Models: `BloodRequest` (FK → HospitalProfile)
- Signal: on creation, triggers donor matching + notification + email
- Views (REST API + redirects):
  - Accept / Decline / Complete / Confirm Received / Cancel / Delete / Remove Donor

### `notifications`
- Models: `Notification` (FK → DonorProfile + BloodRequest)
- Tracks donor response: Pending → Accepted → Completed → Received / Declined
- REST API: list, detail, mark-as-read

### `dashboard`
- No models
- Donor dashboard: aggregates notifications, donations, badges, eligibility status
- `toggle_availability` — donor can manually toggle availability

### `bloodbank`
- Models: `BloodStock` (managed, default DB), `BloodRequest` (bloodbank-specific, not the same as `blood_requests.BloodRequest`), `LegacyBloodStock` (unmanaged, legacy DB)
- Views: stock list (combined), add stock, request blood, fulfill pending, import legacy

### `notifications` (email)
- `email_utils.py` → sends HTML/text email via Gmail SMTP using Django template `emails/blood_request_notification.txt`

---

## 6. Dependencies

| Package | Version | Purpose |
|---|---|---|
| Django | 6.0.7 | Core framework |
| djangorestframework | 3.17.1 | REST API |
| djangorestframework_simplejwt | 5.5.1 | JWT auth (configured, available) |
| django-axes | 7.0.1 | Brute-force login protection (5 attempts, 1hr cooldown) |
| mysqlclient | 2.2.8 | MySQL database driver |
| dj-database-url | latest | Parse `DATABASE_URL` for cloud DB |
| python-dotenv | 1.2.2 | Load `.env` variables |
| geopy | 2.5.0 | Geocoding via Nominatim (OpenStreetMap) |
| geographiclib | 2.1 | Geopy dependency |
| whitenoise | 6.12.0 | Static file serving (compressed + manifest) |
| gunicorn | latest | WSGI server for production (Render) |
| pillow | 12.3.0 | Profile picture image handling |
| cryptography / pyOpenSSL | 50.0 / 26.4 | SSL/crypto support |
| PyJWT | 2.13.0 | JWT token handling |
| Werkzeug | 3.1.8 | Security utilities |

---

## 7. Security Configuration

| Feature | Setting |
|---|---|
| Brute-force protection | django-axes: 5 failures → 1hr lockout, reset on success |
| Auth backends | AxesStandaloneBackend + ModelBackend |
| Session cookies | Secure + HttpOnly in production |
| CSRF cookies | Secure + HttpOnly in production |
| HTTPS redirect | `SECURE_SSL_REDIRECT = True` in production |
| HSTS | 1 year + subdomains + preload in production |
| Proxy SSL header | `HTTP_X_FORWARDED_PROTO` (for Render) |

---

## 8. URL Structure

| Prefix | App | Key Endpoints |
|---|---|---|
| `/` | accounts | home, register, login, logout |
| `/accounts/` | accounts | same as above |
| `/donors/` | donors | edit-profile, donation-history |
| `/hospitals/` | hospitals | login, dashboard |
| `/blood-requests/` | blood_requests | CRUD + accept/decline/complete/confirm/cancel |
| `/notifications/` | notifications | list, detail, mark-read |
| `/dashboard/` | dashboard | donor dashboard, toggle-availability |
| `/bloodbank/` | bloodbank | stock list, add, request, fulfill, import |
| `/admin/` | Django admin | full admin panel |

---

## 9. Critical Issues / Notes

- `DEBUG=True` appears **twice** in `.env` — the second one overrides, but it's redundant and should be cleaned up
- `dashboard_url` in `email_utils.py` is hardcoded to `http://127.0.0.1:8000/dashboard/` — this will send wrong links in production on Render
- `LegacyBloodStock` maps to `old_blood_table` — this table name must match the actual legacy DB table exactly or queries will fail
- `bloodbank.BloodRequest` and `blood_requests.BloodRequest` are two separate models — this naming collision can cause confusion
- JWT (`simplejwt`) is installed but no JWT-protected endpoints are currently wired up in URLs