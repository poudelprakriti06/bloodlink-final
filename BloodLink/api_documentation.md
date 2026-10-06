# API Documentation

## BloodLink — REST API Reference

---

## Table of Contents

- [Overview](#overview)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Response Format](#response-format)
- [HTTP Status Codes](#http-status-codes)
- [Endpoints](#endpoints)
  - [Blood Requests](#blood-requests)
  - [Notifications](#notifications)
  - [Donor Actions](#donor-actions)
  - [Hospital Actions](#hospital-actions)
- [Web Interface Endpoints](#web-interface-endpoints)
- [Error Handling](#error-handling)

---

## Overview

BloodLink exposes a REST API built with Django REST Framework (DRF) for blood request management and notification handling. The API uses session-based authentication (Django sessions) for browser clients. JWT authentication is available via `djangorestframework_simplejwt` but is not currently wired to URL routes — it is available for future mobile client integration.

All API endpoints return JSON. Web interface endpoints (HTML views) use Django's template rendering and redirect responses.

---

## Base URL

| Environment | Base URL |
|---|---|
| Development | `http://127.0.0.1:8000` |
| Production | `https://bloodlink-final.onrender.com` |

---

## Authentication

### Session Authentication (Default)

All API endpoints require the user to be authenticated via Django session. Unauthenticated requests to protected endpoints return `HTTP 403 Forbidden`.

To authenticate, the user must first log in via the web interface:

```
POST /login/
```

The session cookie is then automatically included in subsequent requests.

### Permission Classes

| Endpoint Group | Permission |
|---|---|
| Blood Request List/Create | `IsAuthenticated` |
| Blood Request Detail | `IsAuthenticated` |
| Notification List/Detail | Authenticated (session) |
| Donor action endpoints | Authenticated (session) |
| Hospital action endpoints | Authenticated (session) |

---

## Response Format

### Success Response

```json
{
    "id": 1,
    "blood_group": "A+",
    "units_required": 2,
    "status": "Pending",
    ...
}
```

### Error Response

```json
{
    "message": "You have already responded to this request."
}
```

---

## HTTP Status Codes

| Code | Meaning |
|---|---|
| `200 OK` | Request succeeded |
| `201 Created` | Resource created successfully |
| `302 Found` | Redirect (used by action endpoints) |
| `400 Bad Request` | Invalid request data or business rule violation |
| `403 Forbidden` | Not authenticated or not authorized |
| `404 Not Found` | Resource does not exist |

---

## Endpoints

---

### Blood Requests

#### List All Blood Requests

```
GET /blood-requests/
```

Returns all blood requests ordered by creation date (newest first).

**Permission:** `IsAuthenticated`

**Response `200 OK`:**

```json
[
    {
        "id": 1,
        "hospital": 3,
        "blood_group": "A+",
        "units_required": 2,
        "units_fulfilled": 0,
        "district": "Kathmandu",
        "contact_person": "Dr. Sharma",
        "municipality": "Kathmandu Metropolitan City",
        "ward": 10,
        "area": "New Baneshwor",
        "latitude": 27.6939,
        "longitude": 85.3157,
        "contact_number": "+977-9800000000",
        "required_date": "2025-07-20",
        "urgency": "Urgent",
        "notes": "Required for surgery",
        "status": "Pending",
        "created_at": "2025-07-15T10:30:00Z"
    }
]
```

---

#### Create Blood Request

```
POST /blood-requests/
```

Creates a new blood request. On creation, the `post_save` signal automatically triggers donor matching and notification dispatch.

**Permission:** `IsAuthenticated`

**Request Body:**

```json
{
    "hospital": 3,
    "blood_group": "A+",
    "units_required": 2,
    "district": "Kathmandu",
    "contact_person": "Dr. Sharma",
    "municipality": "Kathmandu Metropolitan City",
    "ward": 10,
    "area": "New Baneshwor",
    "contact_number": "+977-9800000000",
    "required_date": "2025-07-20",
    "urgency": "Urgent",
    "notes": "Required for surgery"
}
```

**Field Validation:**

| Field | Required | Values |
|---|---|---|
| `hospital` | Yes | ID of an existing HospitalProfile |
| `blood_group` | Yes | `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-` |
| `units_required` | Yes | Positive integer |
| `district` | Yes | Any of 77 Nepal districts |
| `contact_person` | Yes | String, max 100 chars |
| `contact_number` | Yes | String, max 15 chars |
| `required_date` | Yes | Date (YYYY-MM-DD) |
| `urgency` | No | `Normal` (default), `Urgent`, `Critical` |
| `municipality` | No | String |
| `ward` | No | Positive integer |
| `area` | No | String |
| `notes` | No | Text |

**Response `201 Created`:** Full blood request object (same as GET response)

**Side Effects on Creation:**
1. Geocoding runs if `district`, `municipality`, `ward`, and `area` are all provided
2. `post_save` signal fires → donor matching → notifications created → emails sent

---

#### Retrieve Blood Request

```
GET /blood-requests/{id}/
```

Returns a single blood request by ID.

**Permission:** `IsAuthenticated`

**Response `200 OK`:** Full blood request object

---

#### Update Blood Request

```
PUT /blood-requests/{id}/
PATCH /blood-requests/{id}/
```

Updates a blood request. Partial updates supported via `PATCH`.

**Permission:** `IsAuthenticated`

**Response `200 OK`:** Updated blood request object

---

### Notifications

#### List Donor Notifications

```
GET /notifications/
```

Returns all notifications for the currently authenticated donor, ordered by `sent_at` descending.

**Permission:** Authenticated donor

**Response `200 OK`:**

```json
[
    {
        "id": 5,
        "donor": 2,
        "blood_request": 1,
        "message": "Emergency blood request for A+ blood at Bir Hospital in Kathmandu.",
        "is_read": false,
        "response": "Pending",
        "sent_at": "2025-07-15T10:30:05Z"
    }
]
```

---

#### Retrieve Notification Detail

```
GET /notifications/{id}/
```

Returns a single notification. Only accessible by the donor who owns it.

**Response `200 OK`:** Single notification object

---

#### Mark Notification as Read

```
PUT /notifications/{id}/read/
```

Marks a notification as read (`is_read = true`).

**Permission:** Authenticated donor (must own the notification)

**Response `200 OK`:** Updated notification object

```json
{
    "id": 5,
    "donor": 2,
    "blood_request": 1,
    "message": "Emergency blood request for A+ blood at Bir Hospital in Kathmandu.",
    "is_read": true,
    "response": "Pending",
    "sent_at": "2025-07-15T10:30:05Z"
}
```

---

### Donor Actions

These endpoints handle the donor's response to blood requests. They use `APIView` but redirect to the dashboard on success.

---

#### Accept Blood Request

```
POST /blood-requests/{id}/accept/
```

Donor accepts a blood request notification.

**Permission:** Authenticated donor

**Business Rules:**
- The donor must have a `Notification` record for this request with `response = "Pending"`
- The donor must be eligible (90-day cooldown must have passed)
- The number of already-accepted donors must be less than `units_required`

**On Success:**
- `notification.response` → `"Accepted"`
- `notification.is_read` → `True`
- `donor.is_available` → `False`
- Redirects to `/dashboard/`

**Error Responses:**

| Condition | Status | Message |
|---|---|---|
| All units already accepted | `400` | `"All required donor units have already been accepted."` |
| Donor already responded | `400` | `"You have already responded to this request."` |
| Donor not eligible (90-day rule) | Redirect | Error message on dashboard |

---

#### Decline Blood Request

```
POST /blood-requests/{id}/decline/
```

Donor declines a blood request notification.

**Permission:** Authenticated donor

**Business Rules:**
- The donor must have a `Notification` record for this request with `response = "Pending"`

**On Success:**
- `notification.response` → `"Declined"`
- `notification.is_read` → `True`
- Redirects to `/dashboard/`

**Error Response:**

| Condition | Status | Message |
|---|---|---|
| Donor already responded | `400` | `"You have already responded to this request."` |

---

#### Complete Donation

```
POST /blood-requests/{id}/complete-donation/
```

Donor marks their donation as physically completed (blood has been given).

**Permission:** Authenticated donor

**Business Rules:**
- The donor's notification `response` must be `"Accepted"`

**On Success:**
- `notification.response` → `"Completed"`
- `notification.is_read` → `True`
- Redirects to `/dashboard/`

**Error Response:**

| Condition | Status | Message |
|---|---|---|
| Donor has not accepted | `400` | `"You must accept the blood request before completing the donation."` |

---

### Hospital Actions

---

#### Confirm Blood Received

```
POST /blood-requests/{id}/confirm-received/
```

Hospital confirms that blood from a specific donor has been received.

**Permission:** Authenticated hospital user

**Request Body (form data):**

| Field | Type | Description |
|---|---|---|
| `notification_id` | Integer | ID of the donor's notification record |

**Business Rules:**
- The blood request must belong to the authenticated hospital
- The notification's `response` must be `"Completed"`
- No duplicate `Donation` record for the same donor + request
- `units_fulfilled` must be less than `units_required`

**On Success:**
1. `Donation` record created with:
   - `donor` = notification's donor
   - `blood_request` = the blood request
   - `hospital_name` = hospital name string
   - `donation_date` = today
   - `remarks` = `"Blood received and confirmed by hospital."`
2. `donor.last_donation_date` → today
3. `donor.is_available` → `False`
4. `notification.response` → `"Received"`
5. `blood_request.units_fulfilled` incremented by 1 (atomic)
6. If `units_fulfilled >= units_required` → `blood_request.status` → `"Fulfilled"`
7. Redirects to `/hospitals/dashboard/`

**Error Responses:**

| Condition | Status | Message |
|---|---|---|
| Not the hospital's request | `403` | `"You are not authorized to confirm this request."` |
| Donor not completed | `400` | `"The donor has not completed the donation yet."` |
| Duplicate donation | `400` | `"Blood from this donor has already been received."` |
| All units already received | `400` | `"All required blood units have already been received."` |

---

#### Cancel Blood Request

```
POST /blood-requests/{id}/cancel/
```

Hospital cancels an active blood request.

**Permission:** Authenticated hospital user (`@login_required`)

**Business Rules:**
- The blood request must belong to the authenticated hospital
- Request must not already be `Fulfilled` or `Cancelled`

**On Success:**
- All active notifications (`Pending`, `Accepted`, `Completed`) → `response = "Declined"`, `is_read = True`
- All affected donors → `is_available = True` (restored)
- `blood_request.status` → `"Cancelled"`
- Redirects to `/hospitals/dashboard/`

---

#### Delete Blood Request

```
POST /blood-requests/{id}/delete/
```

Permanently deletes a blood request.

**Permission:** Authenticated hospital user (`@login_required`)

**Business Rules:**
- The blood request must belong to the authenticated hospital

**On Success:**
- Blood request and all related notifications deleted (CASCADE)
- Redirects to `/hospitals/dashboard/`

---

#### Remove Accepted Donor

```
POST /blood-requests/remove-donor/{id}/
```

Hospital removes a specific accepted donor from a blood request.

**Permission:** Authenticated hospital user (`@login_required`)

**Path Parameter:** `id` = Notification ID (not blood request ID)

**Business Rules:**
- The notification must have `response = "Accepted"`
- The blood request must belong to the authenticated hospital

**On Success:**
- `notification.response` → `"Declined"`
- `notification.is_read` → `True`
- `donor.is_available` → `True` (restored)
- Redirects to `/hospitals/dashboard/`

---

## Web Interface Endpoints

These endpoints render HTML templates and are not part of the REST API.

| Method | URL | View | Description |
|---|---|---|---|
| GET | `/` | `home` | Landing page |
| GET/POST | `/register/` | `register_view` | Donor registration form |
| GET/POST | `/login/` | `login_view` | Donor login |
| POST | `/logout/` | `logout_view` | Logout |
| GET/POST | `/hospitals/login/` | `hospital_login_view` | Hospital login |
| GET | `/hospitals/dashboard/` | `hospital_dashboard_view` | Hospital dashboard |
| GET | `/dashboard/` | `dashboard` | Donor dashboard |
| POST | `/dashboard/toggle-availability/` | `toggle_availability` | Toggle donor availability |
| GET/POST | `/donors/edit-profile/` | `edit_profile` | Edit donor profile |
| GET | `/donors/donation-history/` | `donation_history` | Donor donation history |
| GET | `/bloodbank/` | `stock_list` | Combined blood stock view |
| GET/POST | `/bloodbank/add/` | `add_stock` | Add blood stock |
| GET/POST | `/bloodbank/request/` | `request_blood` | Request blood from stock |
| GET | `/bloodbank/requests/` | `request_list` | List bloodbank requests |
| POST | `/bloodbank/fulfill/{id}/` | `fulfill_pending_request` | Fulfill a pending request |
| GET/POST | `/bloodbank/import/` | `import_legacy_to_new` | Import legacy stock |
| GET/POST | `/admin/` | Django Admin | Admin panel |

---

## Error Handling

### Validation Errors (DRF)

When a serializer validation fails, DRF returns:

```json
{
    "field_name": ["This field is required."]
}
```

### Business Logic Errors

Business rule violations return a JSON message:

```json
{
    "message": "Descriptive error message here."
}
```

### Authentication Errors

Unauthenticated requests to `IsAuthenticated` endpoints return:

```json
{
    "detail": "Authentication credentials were not provided."
}
```

### Not Found

```json
{
    "detail": "Not found."
}
```

### Brute-Force Lockout

After 5 failed login attempts, django-axes locks the account for 1 hour. The login form displays an error message. The lockout resets automatically after the cooldown period or on a successful login.
