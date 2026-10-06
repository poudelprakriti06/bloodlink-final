# Methodology

## BloodLink — System Design, Architecture & Development Methodology

---

## Table of Contents

- [Development Methodology](#development-methodology)
- [System Architecture](#system-architecture)
- [Application Module Design](#application-module-design)
- [Data Flow Design](#data-flow-design)
- [Donor Matching Algorithm](#donor-matching-algorithm)
- [Geolocation Strategy](#geolocation-strategy)
- [Notification System Design](#notification-system-design)
- [Donation Lifecycle Design](#donation-lifecycle-design)
- [Badge and Gamification System](#badge-and-gamification-system)
- [Legacy System Integration Strategy](#legacy-system-integration-strategy)
- [Security Design](#security-design)
- [API Design Principles](#api-design-principles)
- [Technology Selection Rationale](#technology-selection-rationale)

---

## Development Methodology

BloodLink was developed using an **iterative, feature-driven development** approach. The system was built in incremental phases, with each phase delivering a working, testable feature set before moving to the next.

### Development Phases

| Phase | Focus | Key Deliverables |
|---|---|---|
| Phase 1 | Foundation | Django project setup, database configuration, user authentication |
| Phase 2 | Core Entities | Donor profiles, hospital profiles, registration forms |
| Phase 3 | Blood Request Workflow | Blood request model, hospital dashboard, request management |
| Phase 4 | Matching & Notifications | Donor matching algorithm, signal-based notifications, email dispatch |
| Phase 5 | Donation Tracking | Donation lifecycle, batch codes, status pipeline |
| Phase 6 | Gamification | Badge system, donor dashboard statistics |
| Phase 7 | Blood Bank Module | Stock management, legacy DB integration, import tool |
| Phase 8 | Security & Deployment | django-axes, production security headers, Render deployment |

### Key Principles

- **Separation of concerns:** Each Django app handles a single domain (donors, hospitals, notifications, etc.)
- **Signal-driven side effects:** Cross-app actions (e.g., creating notifications when a blood request is saved) are handled via Django signals rather than direct coupling
- **Database-level atomicity:** Critical operations (unit fulfillment counting) use database-level atomic updates (`F()` expressions) to prevent race conditions
- **Fail-safe defaults:** Security settings default to the most restrictive values; `DEBUG=False` enables all production security headers automatically

---

## System Architecture

BloodLink follows a **monolithic Django architecture** with clear internal module boundaries. This was chosen over a microservices approach due to the project's scale and the need for rapid development.

```
┌─────────────────────────────────────────────────────────┐
│                    Client (Browser)                      │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP/HTTPS
┌──────────────────────────▼──────────────────────────────┐
│                  Render Web Service                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Gunicorn (WSGI Server)              │    │
│  │  ┌───────────────────────────────────────────┐  │    │
│  │  │           Django Application              │  │    │
│  │  │                                           │  │    │
│  │  │  Middleware Stack:                        │  │    │
│  │  │  ├── SecurityMiddleware                   │  │    │
│  │  │  ├── WhiteNoiseMiddleware (static files)  │  │    │
│  │  │  ├── SessionMiddleware                    │  │    │
│  │  │  ├── AxesMiddleware (brute-force)         │  │    │
│  │  │  ├── CsrfViewMiddleware                   │  │    │
│  │  │  └── AuthenticationMiddleware             │  │    │
│  │  │                                           │  │    │
│  │  │  URL Router → App Views                   │  │    │
│  │  │  ├── accounts (auth)                      │  │    │
│  │  │  ├── donors (profiles, donations)         │  │    │
│  │  │  ├── hospitals (profiles, dashboard)      │  │    │
│  │  │  ├── blood_requests (REST API + actions)  │  │    │
│  │  │  ├── notifications (REST API)             │  │    │
│  │  │  ├── dashboard (donor UI)                 │  │    │
│  │  │  └── bloodbank (stock management)         │  │    │
│  │  │                                           │  │    │
│  │  │  Django ORM                               │  │    │
│  │  │  ├── default → Aiven MySQL (cloud)        │  │    │
│  │  │  └── legacy  → Local MySQL (read-only)    │  │    │
│  │  └───────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
┌─────────────▼──────────┐  ┌──────────▼──────────┐
│   Aiven MySQL (cloud)   │  │  Gmail SMTP Server   │
│   (default database)    │  │  (email dispatch)    │
└─────────────────────────┘  └─────────────────────┘
```

---

## Application Module Design

Each Django app is designed around a single domain responsibility:

### `accounts`
Handles user identity and authentication. On registration, it creates both a `UserProfile` (role) and a `DonorProfile` (medical/location data) atomically. Role detection (`donor` vs `hospital`) is done by checking for the presence of `donor_profile` or `hospital_profile` reverse relations on the user object.

### `donors`
Owns all donor-specific data. The `DonorProfile` model is the central entity for the donor workflow. The `Donation` model records confirmed donation events and drives the badge system. The `services.py` module encapsulates the geocoding logic, keeping it reusable across apps.

### `hospitals`
Owns hospital account data. Hospital accounts are created by administrators via the Django admin panel. The hospital dashboard aggregates blood requests and donor responses.

### `blood_requests`
The most complex app. It owns the `BloodRequest` model and all state transitions. The `signals.py` module fires on `BloodRequest` creation to trigger the matching and notification pipeline. All donor-hospital interaction endpoints (accept, decline, complete, confirm, cancel) live here.

### `notifications`
Acts as the bridge between donors and blood requests. Each `Notification` record represents one donor's awareness of and response to one blood request. The `services.py` module provides a clean `create_notification()` function used by the signal. The `email_utils.py` module handles email dispatch.

### `dashboard`
A thin view layer with no models. It aggregates data from `donors`, `notifications`, and `blood_requests` to render the donor dashboard. The `toggle_availability` view provides a simple POST endpoint for donors to change their availability status.

### `bloodbank`
A self-contained blood stock management module. It has its own `BloodRequest` model (separate from `blood_requests.BloodRequest`) for internal stock fulfillment tracking. It integrates with the legacy database via the `LegacyBloodStock` unmanaged model.

---

## Data Flow Design

### Blood Request Creation → Donor Notification

```
1. Hospital submits blood request form / API call
        ↓
2. BloodRequest.save() called
   - Location fields changed? → get_coordinates() → store lat/lon
        ↓
3. Django post_save signal fires (blood_requests/signals.py)
        ↓
4. Matching strategy selected:
   - If request has lat/lon → GPS proximity matching
   - Else → district-based fallback
        ↓
5. Donor filter applied:
   - blood_group = request.blood_group
   - is_available = True
   - is_eligible() = True (90-day check)
        ↓
6. For GPS matching:
   - calculate_distance(Haversine) for each candidate donor
   - Sort by distance ascending
   - Take top 10
        ↓
7. For each matched donor:
   - create_notification(donor, blood_request, message)
   - send_blood_request_email(donor, blood_request)
```

### Donation Confirmation Flow

```
1. Donor accepts notification
   - notification.response = "Accepted"
   - donor.is_available = False
        ↓
2. Donor physically donates blood and marks complete
   - notification.response = "Completed"
        ↓
3. Hospital confirms blood received
   - Donation record created (batch_code auto-generated)
   - donor.last_donation_date = today
   - blood_request.units_fulfilled += 1 (atomic F() update)
   - notification.response = "Received"
        ↓
4. If units_fulfilled >= units_required:
   - blood_request.status = "Fulfilled"
        ↓
5. When Donation.status reaches "delivered":
   - donor.award_badges() called
   - Eligible badges created in donors_donorbadge
```

---

## Donor Matching Algorithm

The matching algorithm is implemented in `blood_requests/signals.py` and uses `donors/utils.py` for distance calculation.

### Primary Strategy: GPS Proximity Matching

Used when the blood request has valid `latitude` and `longitude` values.

**Step 1 — Candidate Selection:**
```python
matching_donors = DonorProfile.objects.filter(
    blood_group=instance.blood_group,
    is_available=True,
    latitude__isnull=False,
    longitude__isnull=False
)
```

**Step 2 — Eligibility Filter:**
```python
for donor in matching_donors:
    if donor.is_eligible():  # 90-day cooldown check
        distance = calculate_distance(...)
        nearby_donors.append((distance, donor))
```

**Step 3 — Sort and Select:**
```python
nearby_donors.sort(key=lambda x: x[0])  # Sort by distance
top_donors = [donor for _, donor in nearby_donors[:10]]  # Top 10
```

### Fallback Strategy: District-Based Matching

Used when the blood request does not have GPS coordinates.

```python
top_donors = DonorProfile.objects.filter(
    blood_group=instance.blood_group,
    is_available=True,
    district=instance.district
)
top_donors = [d for d in top_donors if d.is_eligible()][:10]
```

### Haversine Distance Formula

Implemented in `donors/utils.py`. Calculates the great-circle distance between two GPS coordinates.

```
a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
c = 2 × atan2(√a, √(1−a))
distance = R × c    (R = 6371 km)
```

This formula accounts for the curvature of the Earth and provides accurate distances for the scale of Nepal (approximately 800 km × 200 km).

---

## Geolocation Strategy

### Geocoding on Save

Both `DonorProfile` and `BloodRequest` auto-geocode their location on save. The logic is:

1. Check if any location field (`district`, `municipality`, `ward`, `area`) has changed
2. If changed and all four fields are present, call `get_coordinates()`
3. Store the returned `latitude` and `longitude` on the model

### Geocoding Implementation

`donors/services.py` uses **geopy** with the **Nominatim** geocoder (OpenStreetMap):

```python
queries = [
    f"{area}, {municipality}, {district}, Nepal",   # Most specific
    f"{area}, {district}, Nepal",                    # Without municipality
    f"{municipality}, {district}, Nepal",            # Without area
]
```

The function tries each query in order and returns the first successful result. This graceful degradation handles cases where the most specific address is not in the OpenStreetMap database.

### Coordinate Caching

Coordinates are stored in the database after the first successful geocoding. Subsequent saves only re-geocode if location fields actually change, preventing unnecessary API calls to Nominatim.

### Signal-Based Geocoding for New Donors

The `donors/signals.py` `post_save` signal provides a second geocoding attempt for newly created `DonorProfile` records that don't yet have coordinates (e.g., if the `save()` geocoding failed due to a timeout).

---

## Notification System Design

### Design Choice: Notification as Join Table

Rather than a direct many-to-many relationship between `DonorProfile` and `BloodRequest`, the `Notification` model serves as an enriched join table. This design was chosen because:

1. Each donor-request pair needs its own state (`response`, `is_read`)
2. Each notification needs its own message text
3. The notification timestamp (`sent_at`) is needed for ordering
4. The response state machine (Pending → Accepted → Completed → Received / Declined) requires per-record tracking

### Email Notification

Email is sent via `notifications/email_utils.py` using Django's `EmailMultiAlternatives`. The email:
- Uses a text template (`emails/blood_request_notification.txt`)
- Is sent to the donor's registered email address
- Includes the blood request details and a link to the dashboard
- Fails silently (logs error) to prevent a single email failure from blocking the entire notification batch

---

## Donation Lifecycle Design

### Five-Stage Pipeline

The `Donation.status` field tracks blood through five stages:

| Stage | Key | Meaning |
|---|---|---|
| 1 | `collected` | Blood has been collected from the donor |
| 2 | `processing` | Blood is being processed (separation, etc.) |
| 3 | `testing` | Blood is being tested for compatibility and safety |
| 4 | `shipped` | Blood is in transit to the destination |
| 5 | `delivered` | Blood has been delivered to the recipient |

### Progress Tracking

The `journey_steps` property returns a list of step objects with `done` flags, enabling a visual progress bar in the UI. The `progress_percentage` property returns an integer 0–100.

### Batch Code Generation

Each donation receives a unique batch code on first save:

```python
self.batch_code = f"BL-{uuid.uuid4().hex[:10].upper()}"
# Example: BL-A3F7C2E891
```

The `BL-` prefix identifies the code as a BloodLink batch. The 10-character hex suffix provides 16^10 ≈ 1 trillion unique values, making collisions practically impossible.

---

## Badge and Gamification System

### Design Philosophy

Badges are awarded automatically based on donation milestones. The system is designed to be extensible — new badges can be added by appending to the `badge_definitions` list in `DonorProfile.award_badges()`.

### Award Trigger

`award_badges()` is called from `Donation.save()` when `status == 'delivered'`. This ensures badges are only awarded for fully completed donations.

### Idempotency

The `unique_together = ('donor', 'badge_key')` constraint on `DonorBadge` ensures a donor can never receive the same badge twice, even if `award_badges()` is called multiple times.

### Current Badge Definitions

| Badge Key | Condition | Description |
|---|---|---|
| `first_timer` | `total_donations >= 1` | First completed donation |
| `gallon_grad` | `total_donations >= 8` | 8 donations = 1 gallon of blood |
| `decade_donor` | Placeholder (`False`) | Long-term donor recognition |

---

## Legacy System Integration Strategy

### Read-Only Access via Unmanaged Model

The legacy blood bank database is accessed through Django's **unmanaged model** feature:

```python
class LegacyBloodStock(models.Model):
    blood_type = models.CharField(max_length=3, db_column='blood_group')
    total_units = models.IntegerField(db_column='quantity')
    expiry = models.DateField(db_column='expiry_date')

    class Meta:
        managed = False          # Django will not create/modify this table
        db_table = 'old_blood_table'
```

The `managed = False` flag tells Django:
- Do not create this table in migrations
- Do not modify or drop this table
- Do not include it in `migrate` operations

### Database Router Enforcement

The `LegacyRouter` enforces read-only access at the ORM level:
- Reads from `LegacyBloodStock` are routed to the `legacy` database
- Write attempts are blocked by returning `None` from `db_for_write()`

### Combined Stock View

The `bloodbank/views.py` `stock_list` view combines new and legacy stock:

```python
new_dict = {s.blood_group: s.quantity for s in BloodStock.objects.all()}
legacy_dict = {l.blood_type: l.total_units for l in LegacyBloodStock.objects.all()}
# Merge by blood group key
```

### Import Tool

The `import_legacy_to_new` view provides a one-time (or periodic) import of legacy stock into the new system. It uses `get_or_create` to avoid duplicates and updates quantities additively.

---

## Security Design

### Authentication and Authorization

- **Role detection:** Based on the presence of `donor_profile` or `hospital_profile` reverse relations — no separate role field is checked at the view level
- **Login protection:** django-axes tracks failed login attempts per IP/username and locks accounts after 5 failures
- **`@login_required`:** Applied to all views that require authentication
- **Hospital-specific views:** Check `hasattr(request.user, 'hospital_profile')` before rendering hospital content

### CSRF Protection

All state-changing web views use Django's built-in CSRF middleware. API endpoints that use `APIView` rely on DRF's session authentication, which includes CSRF validation for browser clients.

### Password Security

Django's built-in password validators enforce:
- Minimum length
- Not similar to username/email
- Not a common password
- Not entirely numeric

### Production Security Headers

All production security headers are enabled automatically when `DEBUG=False`. See the [Deployment Guide](deployment.md) for the full security checklist.

---

## API Design Principles

### REST Conventions

- `GET` for read operations
- `POST` for create and action operations
- `PUT`/`PATCH` for updates
- Resource URLs use plural nouns (`/blood-requests/`, `/notifications/`)

### Hybrid Response Strategy

The API uses a hybrid approach:
- **JSON responses** for list/detail/create/update operations (DRF serializers)
- **Redirect responses** for action endpoints (accept, decline, complete, confirm, cancel)

This hybrid approach was chosen because the action endpoints are primarily used by browser form submissions, where a redirect to the dashboard is the expected behavior. The JSON error responses allow programmatic clients to detect failures.

### Serializers

`BloodRequestSerializer` and `NotificationSerializer` use `fields = "__all__"` for simplicity. In a future version, these should be restricted to expose only the fields needed by each client type.
