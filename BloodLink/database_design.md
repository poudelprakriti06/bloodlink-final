# Database Design

## BloodLink — Database Architecture & Schema Reference

---

## Table of Contents

- [Overview](#overview)
- [Database Configuration](#database-configuration)
- [Database Routing Strategy](#database-routing-strategy)
- [Entity Relationship Summary](#entity-relationship-summary)
- [Schema Reference](#schema-reference)
  - [accounts_userprofile](#accounts_userprofile)
  - [donors_donorprofile](#donors_donorprofile)
  - [donors_donation](#donors_donation)
  - [donors_donorbadge](#donors_donorbadge)
  - [hospitals_hospitalprofile](#hospitals_hospitalprofile)
  - [blood_requests_bloodrequest](#blood_requests_bloodrequest)
  - [notifications_notification](#notifications_notification)
  - [bloodbank_bloodstock](#bloodbank_bloodstock)
  - [bloodbank_bloodrequest](#bloodbank_bloodrequest)
  - [old_blood_table (Legacy)](#old_blood_table-legacy)
- [Enumerated Field Values](#enumerated-field-values)
- [Key Relationships Diagram](#key-relationships-diagram)
- [Indexing and Constraints](#indexing-and-constraints)
- [Design Decisions](#design-decisions)

---

## Overview

BloodLink uses two separate MySQL databases:

| Database Alias | Purpose | Location |
|---|---|---|
| `default` | All application data — donors, hospitals, requests, notifications, donations, blood stock | Aiven Cloud MySQL (production) / Local MySQL (development) |
| `legacy` | Read-only access to the existing legacy blood bank system | Local MySQL |

All Django-managed models write to and read from the `default` database. The `legacy` database is accessed in read-only mode through an unmanaged Django model (`LegacyBloodStock`) and a custom database router.

---

## Database Configuration

### Production (Render + Aiven)

When the `DATABASE_URL` environment variable is set, Django uses `dj-database-url` to parse it:

```python
DATABASES = {
    'default': dj_database_url.config(env='DATABASE_URL', conn_max_age=600)
}
```

### Development (Local MySQL)

When `DATABASE_URL` is not set, individual environment variables are used:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),        # bloodlink_db
        'USER': os.getenv('DB_USER'),        # root
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
    }
}
```

### Legacy Database (Always Local)

```python
DATABASES['legacy'] = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': os.getenv('LEGACY_DB_NAME'),    # old_blood_system_db
    'USER': os.getenv('LEGACY_DB_USER'),
    'PASSWORD': os.getenv('LEGACY_DB_PASSWORD'),
    'HOST': os.getenv('LEGACY_DB_HOST', '127.0.0.1'),
    'PORT': os.getenv('LEGACY_DB_PORT', '3306'),
}
```

---

## Database Routing Strategy

The `LegacyRouter` class in `miniProject/db_routers.py` controls which database each model uses.

### Routing Rules

| Condition | Read DB | Write DB | Migrate |
|---|---|---|---|
| Model has `managed = False` (unmanaged/legacy) | `legacy` | Blocked (`None`) | Never |
| App label is `bloodbank` or `myapp` | `default` | `default` | `default` only |
| All other managed models | `default` | `default` | `default` |

### Router Implementation

```python
class LegacyRouter:
    def db_for_read(self, model, **hints):
        if hasattr(model, '_meta') and not model._meta.managed:
            return 'legacy'
        return None

    def db_for_write(self, model, **hints):
        if hasattr(model, '_meta') and not model._meta.managed:
            return None          # Writes to legacy DB are blocked
        return 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in ['bloodbank', 'myapp']:
            return db == 'default'
        return None
```

This design ensures the legacy database is never accidentally modified by Django migrations or application writes.

---

## Entity Relationship Summary

```
auth_user (Django built-in)
    │
    ├──[1:1]── accounts_userprofile       (role: donor / hospital)
    ├──[1:1]── donors_donorprofile        (blood group, location, availability)
    │               │
    │               ├──[1:N]── donors_donation          (donation records)
    │               │               │
    │               │               └──[N:1]── blood_requests_bloodrequest
    │               │
    │               ├──[1:N]── donors_donorbadge        (earned badges)
    │               │
    │               └──[1:N]── notifications_notification
    │                               │
    │                               └──[N:1]── blood_requests_bloodrequest
    │
    └──[1:1]── hospitals_hospitalprofile
                    │
                    └──[1:N]── blood_requests_bloodrequest

bloodbank_bloodstock
    │
    └──[1:N]── bloodbank_bloodrequest (fulfilled_from FK)

old_blood_table (legacy, read-only)
    └── LegacyBloodStock (unmanaged Django model)
```

---

## Schema Reference

### accounts_userprofile

Extends Django's built-in `auth_user` with a role field.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | Primary key |
| `user_id` | BIGINT | FK → auth_user(id), UNIQUE, CASCADE | One-to-one link to Django user |
| `role` | VARCHAR(10) | NOT NULL, DEFAULT `'donor'` | User role (`donor` or `hospital`) |

---

### donors_donorprofile

Stores all donor-specific information including location and availability.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | Primary key |
| `user_id` | BIGINT | FK → auth_user(id), UNIQUE, CASCADE | One-to-one link to Django user |
| `phone` | VARCHAR(15) | NOT NULL | Contact phone number |
| `blood_group` | VARCHAR(5) | NOT NULL | Blood group (A+, A-, B+, B-, AB+, AB-, O+, O-) |
| `gender` | VARCHAR(10) | NOT NULL | Gender (Male, Female, Other) |
| `date_of_birth` | DATE | NOT NULL | Date of birth |
| `district` | VARCHAR(50) | NOT NULL | District (one of 77 Nepal districts) |
| `municipality` | VARCHAR(100) | NULL | Municipality name |
| `ward` | SMALLINT UNSIGNED | NULL | Ward number |
| `area` | VARCHAR(100) | NULL | Area/locality name |
| `last_donation_date` | DATE | NULL | Date of most recent donation |
| `is_available` | TINYINT(1) | NOT NULL, DEFAULT `1` | Whether donor is currently available |
| `profile_picture` | VARCHAR(100) | NULL | Path to uploaded profile image |
| `created_at` | DATETIME | NOT NULL, AUTO | Record creation timestamp |
| `latitude` | DOUBLE | NULL | GPS latitude (auto-geocoded) |
| `longitude` | DOUBLE | NULL | GPS longitude (auto-geocoded) |

**Business Logic:**
- `is_eligible()`: Returns `True` if `last_donation_date` is NULL or >= 90 days ago
- `days_until_eligible()`: Returns days remaining before next eligible donation
- `total_donations`: Property — count of related `Donation` records
- `award_badges()`: Called when a donation reaches `delivered` status
- `save()`: Auto-geocodes location using Nominatim when location fields change

---

### donors_donation

Records each confirmed blood donation event.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | Primary key |
| `donor_id` | BIGINT | FK → donors_donorprofile(id), CASCADE | Donating donor |
| `blood_request_id` | BIGINT | FK → blood_requests_bloodrequest(id), CASCADE, NULL | Linked blood request (if any) |
| `hospital_name` | VARCHAR(200) | NOT NULL | Name of the hospital where donation occurred |
| `destination_hospital` | VARCHAR(200) | NULL | Destination hospital (if different) |
| `donation_date` | DATE | NOT NULL | Date of donation |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT `'collected'` | Current stage in donation pipeline |
| `batch_code` | VARCHAR(80) | UNIQUE, NULL | Auto-generated unique code (`BL-XXXXXXXXXX`) |
| `remarks` | TEXT | NOT NULL (blank allowed) | Additional notes |
| `created_at` | DATETIME | NOT NULL, AUTO | Record creation timestamp |

**Status Pipeline:** `collected` → `processing` → `testing` → `shipped` → `delivered`

**Business Logic:**
- `batch_code`: Auto-generated as `BL-` + 10 uppercase hex characters (UUID-based) on first save
- `journey_steps`: Property returning list of pipeline steps with `done` flags
- `progress_percentage`: Property returning integer 0–100 based on current status
- `save()`: Calls `donor.award_badges()` when status reaches `delivered`

---

### donors_donorbadge

Stores gamification badges earned by donors.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | Primary key |
| `donor_id` | BIGINT | FK → donors_donorprofile(id), CASCADE | Badge owner |
| `badge_key` | VARCHAR(50) | NOT NULL | Unique badge identifier key |
| `badge_name` | VARCHAR(80) | NOT NULL | Display name of the badge |
| `description` | TEXT | NOT NULL (blank allowed) | Badge description |
| `claimed` | TINYINT(1) | NOT NULL, DEFAULT `1` | Whether badge has been claimed |
| `awarded_at` | DATETIME | NOT NULL, AUTO | Timestamp when badge was awarded |

**Unique Constraint:** `(donor_id, badge_key)` — a donor can only earn each badge once.

**Available Badges:**

| Badge Key | Badge Name | Unlock Condition |
|---|---|---|
| `first_timer` | First Timer | 1 or more completed donations |
| `gallon_grad` | Gallon Grad | 8 or more completed donations |
| `decade_donor` | Decade Donor | Placeholder (logic not yet implemented) |

---

### hospitals_hospitalprofile

Stores hospital account information.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | Primary key |
| `user_id` | BIGINT | FK → auth_user(id), UNIQUE, CASCADE | One-to-one link to Django user |
| `hospital_name` | VARCHAR(200) | NOT NULL | Official hospital name |
| `phone` | VARCHAR(15) | NOT NULL | Contact phone number |
| `district` | VARCHAR(50) | NOT NULL | District where hospital is located |
| `address` | TEXT | NOT NULL | Full address |
| `license_number` | VARCHAR(100) | NOT NULL (blank allowed) | Hospital license/registration number |
| `created_at` | DATETIME | NOT NULL, AUTO | Record creation timestamp |

---

### blood_requests_bloodrequest

Core table for hospital blood requests.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | Primary key |
| `hospital_id` | BIGINT | FK → hospitals_hospitalprofile(id), CASCADE | Requesting hospital |
| `blood_group` | VARCHAR(5) | NOT NULL | Required blood group |
| `units_required` | INT UNSIGNED | NOT NULL | Total units needed |
| `units_fulfilled` | INT UNSIGNED | NOT NULL, DEFAULT `0` | Units confirmed received so far |
| `district` | VARCHAR(50) | NOT NULL | District of the request |
| `contact_person` | VARCHAR(100) | NOT NULL | Name of contact person at hospital |
| `municipality` | VARCHAR(100) | NULL | Municipality |
| `ward` | SMALLINT UNSIGNED | NULL | Ward number |
| `area` | VARCHAR(100) | NULL | Area/locality |
| `latitude` | DOUBLE | NULL | GPS latitude (auto-geocoded) |
| `longitude` | DOUBLE | NULL | GPS longitude (auto-geocoded) |
| `contact_number` | VARCHAR(15) | NOT NULL | Contact phone number |
| `required_date` | DATE | NOT NULL | Date by which blood is needed |
| `urgency` | VARCHAR(10) | NOT NULL, DEFAULT `'Normal'` | Urgency level |
| `notes` | TEXT | NOT NULL (blank allowed) | Additional notes |
| `status` | VARCHAR(10) | NOT NULL, DEFAULT `'Pending'` | Request status |
| `created_at` | DATETIME | NOT NULL, AUTO | Record creation timestamp |

**Computed Property:** `units_remaining` = `units_required` - `units_fulfilled`

**Status Transitions:**
```
Pending → Accepted → Completed → Fulfilled
        ↘ Cancelled
```

---

### notifications_notification

Tracks each donor's response to a blood request.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | Primary key |
| `donor_id` | BIGINT | FK → donors_donorprofile(id), CASCADE | Notified donor |
| `blood_request_id` | BIGINT | FK → blood_requests_bloodrequest(id), CASCADE | Related blood request |
| `message` | TEXT | NOT NULL | Notification message text |
| `is_read` | TINYINT(1) | NOT NULL, DEFAULT `0` | Whether donor has read the notification |
| `response` | VARCHAR(10) | NOT NULL, DEFAULT `'Pending'` | Donor's response status |
| `sent_at` | DATETIME | NOT NULL, AUTO | Timestamp when notification was sent |

**Response State Machine:**
```
Pending → Accepted → Completed → Received
        ↘ Declined
```

---

### bloodbank_bloodstock

Manages current blood inventory in the new system.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | Primary key |
| `blood_group` | VARCHAR(3) | NOT NULL, UNIQUE | Blood group identifier |
| `quantity` | INT UNSIGNED | NOT NULL, DEFAULT `0` | Available units |
| `expiry_date` | DATE | NOT NULL | Expiry date of current stock |
| `last_updated` | DATETIME | NOT NULL, AUTO_UPDATE | Last modification timestamp |

**Ordering:** By `blood_group` alphabetically.

---

### bloodbank_bloodrequest

Manages blood requests within the blood bank module (separate from `blood_requests_bloodrequest`).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | Primary key |
| `requester_name` | VARCHAR(100) | NOT NULL | Name of the requester |
| `hospital_name` | VARCHAR(100) | NOT NULL | Hospital name |
| `blood_group` | VARCHAR(3) | NOT NULL | Required blood group |
| `quantity_needed` | INT UNSIGNED | NOT NULL | Units needed |
| `required_by_date` | DATE | NOT NULL | Required by date |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT `'pending'` | Request status (pending / fulfilled / cancelled) |
| `created_at` | DATETIME | NOT NULL, AUTO | Creation timestamp |
| `fulfilled_from_id` | BIGINT | FK → bloodbank_bloodstock(id), SET NULL, NULL | Stock record that fulfilled this request |

---

### old_blood_table (Legacy)

Read-only table in the `legacy` database. Mapped via the unmanaged `LegacyBloodStock` model.

| Django Field | DB Column | Type | Description |
|---|---|---|---|
| `blood_type` | `blood_group` | VARCHAR | Blood group |
| `total_units` | `quantity` | INT | Available units |
| `expiry` | `expiry_date` | DATE | Expiry date |

> **Important:** The actual table name in the legacy database must be `old_blood_table`. If the legacy table has a different name, update `db_table` in the `LegacyBloodStock.Meta` class. Run `python manage.py inspectdb --database=legacy` to inspect the actual legacy schema.

---

## Enumerated Field Values

### Blood Groups
`A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-`

### Donation Status
`collected`, `processing`, `testing`, `shipped`, `delivered`

### Blood Request Status (blood_requests app)
`Pending`, `Accepted`, `Completed`, `Cancelled`, `Fulfilled`

### Blood Request Urgency
`Normal`, `Urgent`, `Critical`

### Notification Response
`Pending`, `Accepted`, `Declined`, `Completed`, `Received`

### Bloodbank Request Status
`pending`, `fulfilled`, `cancelled`

### Donor Gender
`Male`, `Female`, `Other`

---

## Key Relationships Diagram

```
auth_user
  ├── 1:1 → UserProfile          (role)
  ├── 1:1 → DonorProfile         (blood group, location, availability)
  │           ├── 1:N → Donation          (FK: donor)
  │           │           └── N:1 → BloodRequest (blood_requests app)
  │           ├── 1:N → DonorBadge        (FK: donor)
  │           └── 1:N → Notification      (FK: donor)
  │                       └── N:1 → BloodRequest (blood_requests app)
  └── 1:1 → HospitalProfile      (hospital info)
              └── 1:N → BloodRequest      (FK: hospital)

BloodStock (bloodbank)
  └── 1:N → BloodRequest (bloodbank)   (FK: fulfilled_from)

LegacyBloodStock → legacy DB (read-only, unmanaged)
```

---

## Indexing and Constraints

| Table | Column(s) | Constraint Type |
|---|---|---|
| `accounts_userprofile` | `user_id` | UNIQUE |
| `donors_donorprofile` | `user_id` | UNIQUE |
| `donors_donorbadge` | `(donor_id, badge_key)` | UNIQUE TOGETHER |
| `donors_donation` | `batch_code` | UNIQUE |
| `hospitals_hospitalprofile` | `user_id` | UNIQUE |
| `bloodbank_bloodstock` | `blood_group` | UNIQUE |

---

## Design Decisions

### 1. Two-Database Architecture
The decision to maintain a separate `legacy` database rather than migrating all data into the new system was made to ensure zero disruption to existing blood bank operations. The `LegacyRouter` enforces read-only access, preventing any accidental writes.

### 2. Geocoding on Save
Both `DonorProfile` and `BloodRequest` auto-geocode their location fields on save using Nominatim. Coordinates are cached in the database to avoid repeated API calls. Geocoding only runs when location fields actually change.

### 3. Notification as the Donor-Request Bridge
Rather than a direct many-to-many relationship between donors and blood requests, the `Notification` model serves as the join table. This design allows tracking of per-donor response state, read status, and message content — all in one place.

### 4. Atomic Unit Fulfillment
When a hospital confirms blood received, `units_fulfilled` is incremented using `F('units_fulfilled') + 1` (a database-level atomic update) to prevent race conditions when multiple confirmations happen simultaneously.

### 5. Batch Code Generation
Batch codes are generated using Python's `uuid4` to produce a 10-character uppercase hex string prefixed with `BL-`. This provides sufficient uniqueness for tracking purposes while remaining human-readable.

### 6. Separate bloodbank.BloodRequest vs blood_requests.BloodRequest
These are two distinct models serving different purposes:
- `blood_requests.BloodRequest`: Hospital-to-donor matching workflow
- `bloodbank.BloodRequest`: Internal blood bank stock fulfillment workflow

This separation allows the blood bank module to operate independently of the donor-matching system.
