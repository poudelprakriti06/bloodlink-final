# Testing Documentation

## BloodLink — Test Strategy, Test Cases & Results

---

## Table of Contents

- [Testing Strategy](#testing-strategy)
- [Test Environment](#test-environment)
- [Unit Tests](#unit-tests)
- [Integration Tests](#integration-tests)
- [API Tests](#api-tests)
- [Security Tests](#security-tests)
- [Manual Test Cases](#manual-test-cases)
- [Edge Cases and Boundary Conditions](#edge-cases-and-boundary-conditions)
- [Known Issues](#known-issues)
- [Test Coverage Summary](#test-coverage-summary)

---

## Testing Strategy

BloodLink's testing approach covers four levels:

| Level | Scope | Tools |
|---|---|---|
| Unit Testing | Individual model methods, utility functions | Django TestCase, Python unittest |
| Integration Testing | Signal-driven workflows, multi-model interactions | Django TestCase with test DB |
| API Testing | REST endpoint request/response validation | DRF APIClient, Django TestCase |
| Manual Testing | End-to-end user flows, UI verification | Browser, Postman |

All automated tests use Django's built-in test runner, which creates a temporary test database, runs all tests in isolation, and tears down the database after completion.

---

## Test Environment

| Component | Value |
|---|---|
| Django Version | 6.0.7 |
| Test Database | SQLite (in-memory, used by Django test runner) |
| Test Runner | `python manage.py test` |
| Test Discovery | All `tests.py` files in each app |

### Running Tests

```bash
# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test donors
python manage.py test blood_requests
python manage.py test notifications

# Run a specific test class
python manage.py test donors.tests.DonorProfileModelTest

# Run with verbosity
python manage.py test --verbosity=2
```

---

## Unit Tests

### Donor Eligibility Logic

**Test Class:** `DonorEligibilityTest`

| Test Case | Input | Expected Output |
|---|---|---|
| Donor with no donation history | `last_donation_date = None` | `is_eligible() = True` |
| Donor donated exactly 90 days ago | `last_donation_date = today - 90 days` | `is_eligible() = True` |
| Donor donated 89 days ago | `last_donation_date = today - 89 days` | `is_eligible() = False` |
| Donor donated today | `last_donation_date = today` | `is_eligible() = False` |
| Days until eligible — 89 days ago | `last_donation_date = today - 89 days` | `days_until_eligible() = 1` |
| Days until eligible — 80 days ago | `last_donation_date = today - 80 days` | `days_until_eligible() = 10` |
| Days until eligible — eligible donor | `last_donation_date = None` | `days_until_eligible() = 0` |

```python
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from donors.models import DonorProfile
import datetime

class DonorEligibilityTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testdonor', password='pass')
        self.donor = DonorProfile.objects.create(
            user=self.user,
            phone='9800000000',
            blood_group='A+',
            gender='Male',
            date_of_birth='1995-01-01',
            district='Kathmandu'
        )

    def test_eligible_no_donation_history(self):
        self.assertTrue(self.donor.is_eligible())

    def test_eligible_90_days_ago(self):
        self.donor.last_donation_date = timezone.now().date() - datetime.timedelta(days=90)
        self.assertTrue(self.donor.is_eligible())

    def test_not_eligible_89_days_ago(self):
        self.donor.last_donation_date = timezone.now().date() - datetime.timedelta(days=89)
        self.assertFalse(self.donor.is_eligible())

    def test_days_until_eligible(self):
        self.donor.last_donation_date = timezone.now().date() - datetime.timedelta(days=80)
        self.assertEqual(self.donor.days_until_eligible(), 10)
```

---

### Haversine Distance Calculation

**Test Class:** `HaversineDistanceTest`

| Test Case | Input | Expected Output | Tolerance |
|---|---|---|---|
| Same point | lat1=lat2, lon1=lon2 | 0.0 km | ±0.001 km |
| Kathmandu to Pokhara | (27.7172, 85.3240) → (28.2096, 83.9856) | ~200 km | ±5 km |
| Kathmandu to Biratnagar | (27.7172, 85.3240) → (26.4525, 87.2718) | ~270 km | ±5 km |
| Short distance (same district) | Two points ~5 km apart | ~5 km | ±1 km |

```python
from django.test import TestCase
from donors.utils import calculate_distance

class HaversineDistanceTest(TestCase):

    def test_same_point_returns_zero(self):
        distance = calculate_distance(27.7172, 85.3240, 27.7172, 85.3240)
        self.assertAlmostEqual(distance, 0.0, places=2)

    def test_kathmandu_to_pokhara(self):
        distance = calculate_distance(27.7172, 85.3240, 28.2096, 83.9856)
        self.assertGreater(distance, 190)
        self.assertLess(distance, 210)

    def test_returns_float(self):
        result = calculate_distance(27.0, 85.0, 28.0, 86.0)
        self.assertIsInstance(result, float)
```

---

### Donation Batch Code Generation

**Test Class:** `DonationBatchCodeTest`

| Test Case | Expected Behavior |
|---|---|
| New donation without batch code | Batch code auto-generated on save |
| Batch code format | Starts with `BL-`, followed by 10 uppercase hex characters |
| Existing batch code | Not overwritten on subsequent saves |
| Uniqueness | Two donations have different batch codes |

```python
from django.test import TestCase
from django.contrib.auth.models import User
from donors.models import DonorProfile, Donation
import re

class DonationBatchCodeTest(TestCase):

    def setUp(self):
        user = User.objects.create_user(username='donor1', password='pass')
        self.donor = DonorProfile.objects.create(
            user=user, phone='9800000001', blood_group='B+',
            gender='Female', date_of_birth='1998-05-10', district='Lalitpur'
        )

    def test_batch_code_auto_generated(self):
        donation = Donation.objects.create(
            donor=self.donor,
            hospital_name='Test Hospital',
            donation_date='2025-07-15',
            status='collected'
        )
        self.assertIsNotNone(donation.batch_code)

    def test_batch_code_format(self):
        donation = Donation.objects.create(
            donor=self.donor,
            hospital_name='Test Hospital',
            donation_date='2025-07-15',
            status='collected'
        )
        self.assertRegex(donation.batch_code, r'^BL-[A-F0-9]{10}$')

    def test_batch_codes_are_unique(self):
        d1 = Donation.objects.create(
            donor=self.donor, hospital_name='H1',
            donation_date='2025-07-15', status='collected'
        )
        user2 = User.objects.create_user(username='donor2', password='pass')
        donor2 = DonorProfile.objects.create(
            user=user2, phone='9800000002', blood_group='B+',
            gender='Male', date_of_birth='1997-03-20', district='Lalitpur'
        )
        d2 = Donation.objects.create(
            donor=donor2, hospital_name='H2',
            donation_date='2025-07-15', status='collected'
        )
        self.assertNotEqual(d1.batch_code, d2.batch_code)
```

---

### Donation Journey Steps

**Test Class:** `DonationJourneyTest`

| Test Case | Status Input | Expected `done` Steps |
|---|---|---|
| Status = `collected` | `collected` | `[collected=True, processing=False, ...]` |
| Status = `testing` | `testing` | `[collected=True, processing=True, testing=True, shipped=False, delivered=False]` |
| Status = `delivered` | `delivered` | All 5 steps `done=True` |
| Progress percentage at `collected` | `collected` | `20%` |
| Progress percentage at `delivered` | `delivered` | `100%` |

---

### Badge Award Logic

**Test Class:** `BadgeAwardTest`

| Test Case | Donations | Expected Badges |
|---|---|---|
| 0 donations | 0 | No badges |
| 1 donation delivered | 1 | `first_timer` |
| 8 donations delivered | 8 | `first_timer`, `gallon_grad` |
| Badge not duplicated | Award twice | Still only 1 badge record |

---

## Integration Tests

### Blood Request Creation Triggers Notifications

**Test Class:** `BloodRequestSignalTest`

| Test Case | Setup | Expected Outcome |
|---|---|---|
| Request created with matching donors | 3 eligible donors with matching blood group in same district | 3 notifications created |
| Request created with no matching donors | No donors with matching blood group | 0 notifications created |
| Request created — ineligible donors excluded | Donors donated 50 days ago | 0 notifications (all ineligible) |
| Request created — unavailable donors excluded | Donors with `is_available=False` | 0 notifications |
| Top 10 limit enforced | 15 eligible matching donors | Exactly 10 notifications created |

```python
from django.test import TestCase
from django.contrib.auth.models import User
from donors.models import DonorProfile
from hospitals.models import HospitalProfile
from blood_requests.models import BloodRequest
from notifications.models import Notification

class BloodRequestSignalTest(TestCase):

    def setUp(self):
        # Create hospital
        hosp_user = User.objects.create_user(username='hospital1', password='pass')
        self.hospital = HospitalProfile.objects.create(
            user=hosp_user, hospital_name='Test Hospital',
            phone='01-000000', district='Kathmandu', address='Test Address'
        )
        # Create matching donors
        for i in range(3):
            u = User.objects.create_user(username=f'donor{i}', password='pass')
            DonorProfile.objects.create(
                user=u, phone=f'980000000{i}', blood_group='O+',
                gender='Male', date_of_birth='1995-01-01',
                district='Kathmandu', is_available=True
            )

    def test_notifications_created_on_blood_request(self):
        BloodRequest.objects.create(
            hospital=self.hospital, blood_group='O+',
            units_required=2, district='Kathmandu',
            contact_person='Dr. Test', contact_number='9800000000',
            required_date='2025-07-20', urgency='Urgent'
        )
        self.assertEqual(Notification.objects.count(), 3)

    def test_no_notifications_for_wrong_blood_group(self):
        BloodRequest.objects.create(
            hospital=self.hospital, blood_group='AB-',
            units_required=1, district='Kathmandu',
            contact_person='Dr. Test', contact_number='9800000000',
            required_date='2025-07-20'
        )
        self.assertEqual(Notification.objects.count(), 0)
```

---

### Donation Confirmation Updates Units Fulfilled

**Test Class:** `ConfirmBloodReceivedTest`

| Test Case | Expected Outcome |
|---|---|
| First confirmation on 2-unit request | `units_fulfilled = 1`, status = `Pending` |
| Second confirmation on 2-unit request | `units_fulfilled = 2`, status = `Fulfilled` |
| Duplicate confirmation blocked | `400` error, no duplicate `Donation` record |
| Confirmation after fulfilled | `400` error |

---

## API Tests

### Blood Request List API

```
GET /blood-requests/
```

| Test Case | Auth | Expected Status |
|---|---|---|
| Authenticated user | Session auth | `200 OK` |
| Unauthenticated user | No auth | `403 Forbidden` |
| Response is a list | Authenticated | Response body is JSON array |

### Accept Blood Request API

```
POST /blood-requests/{id}/accept/
```

| Test Case | Setup | Expected Outcome |
|---|---|---|
| Valid accept | Donor has pending notification, is eligible | Redirect to dashboard, `response = "Accepted"` |
| Already accepted | `response = "Accepted"` | `400` — already responded |
| All units taken | `occupied_count >= units_required` | `400` — all units accepted |
| Ineligible donor | Donated 50 days ago | Redirect to dashboard with error message |

### Notification Mark Read API

```
PUT /notifications/{id}/read/
```

| Test Case | Expected Outcome |
|---|---|
| Valid mark read | `is_read = True`, `200 OK` |
| Wrong donor's notification | `404 Not Found` |

---

## Security Tests

### Brute-Force Protection (django-axes)

| Test Case | Steps | Expected Outcome |
|---|---|---|
| 4 failed logins | 4 × wrong password | Login form shown, no lockout |
| 5th failed login | 5th × wrong password | Account locked, error message shown |
| Lockout duration | Wait < 1 hour | Login still blocked |
| Reset on success | Correct login after < 5 failures | Failure count reset |

### CSRF Protection

| Test Case | Expected Outcome |
|---|---|
| POST without CSRF token | `403 Forbidden` |
| POST with valid CSRF token | Request processed normally |

### Authorization Checks

| Test Case | Expected Outcome |
|---|---|
| Hospital A tries to cancel Hospital B's request | `403 Forbidden` |
| Hospital A tries to confirm Hospital B's notification | `403 Forbidden` |
| Donor tries to access hospital dashboard | Redirect to donor dashboard |
| Hospital tries to access donor dashboard | Redirect to hospital dashboard |

### Session Security

| Test Case | Expected Outcome |
|---|---|
| Access protected view without login | Redirect to login page |
| Access after logout | Session invalidated, redirect to login |

---

## Manual Test Cases

### End-to-End: Donor Registration and Blood Request Flow

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to `/register/` | Registration form displayed |
| 2 | Fill form with valid data | Account created, redirected to dashboard |
| 3 | Hospital creates blood request via admin | Blood request saved |
| 4 | Check donor dashboard | Notification visible with `Pending` status |
| 5 | Click Accept | Notification status → `Accepted`, donor unavailable |
| 6 | Click Complete Donation | Notification status → `Completed` |
| 7 | Hospital confirms received | Donation record created, `units_fulfilled` incremented |
| 8 | Check donation history | Donation visible with batch code |

### End-to-End: Blood Stock Management

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to `/bloodbank/` | Combined stock view (new + legacy) |
| 2 | Add 10 units of A+ | Stock updated to 10 units |
| 3 | Request 5 units of A+ | Request fulfilled, stock reduced to 5 units |
| 4 | Request 10 units of A+ | Insufficient stock, request marked pending |
| 5 | Navigate to import page | Legacy stock preview shown |
| 6 | Confirm import | Legacy units added to new system stock |

### End-to-End: Hospital Request Cancellation

| Step | Action | Expected Result |
|---|---|---|
| 1 | Hospital creates blood request | Donors notified |
| 2 | Donor accepts | `response = "Accepted"`, donor unavailable |
| 3 | Hospital cancels request | All active notifications → `Declined`, donors restored to available |
| 4 | Check donor dashboard | Notification shows `Declined` |

---

## Edge Cases and Boundary Conditions

| Scenario | Handling |
|---|---|
| Donor donates exactly on day 90 | `is_eligible()` returns `True` (>= 90 days) |
| Blood request with 0 matching donors | No notifications created, no error |
| Geocoding API timeout | `GeocoderTimedOut` caught, returns `None`, coordinates left null |
| Duplicate batch code (UUID collision) | `unique=True` constraint raises `IntegrityError` — practically impossible |
| Hospital confirms same donor twice | `Donation.objects.filter(...).exists()` check returns `400` |
| `units_fulfilled` race condition | `F('units_fulfilled') + 1` atomic update prevents double-counting |
| Donor with no profile accesses dashboard | `AttributeError` on `request.user.donor_profile` — should be handled with `hasattr` check |
| Legacy DB unreachable | `OperationalError` raised on `LegacyBloodStock.objects.all()` — not currently caught |

---

## Known Issues

| Issue | Severity | Status |
|---|---|---|
| `dashboard_url` in email hardcoded to localhost | Medium | Open — needs to be updated to production URL |
| `DEBUG=True` appears twice in `.env` | Low | Open — second occurrence is redundant |
| Legacy DB connection failure not handled gracefully in `stock_list` view | Medium | Open — should wrap in try/except |
| `bloodbank.BloodRequest` and `blood_requests.BloodRequest` naming collision | Low | Open — causes confusion but no functional bug |
| JWT endpoints not wired to URLs despite `simplejwt` being installed | Low | Open — available for future mobile client |
| `decade_donor` badge condition hardcoded to `False` | Low | Open — logic not yet implemented |

---

## Test Coverage Summary

| App | Models Tested | Views Tested | Signals Tested | Coverage |
|---|---|---|---|---|
| `accounts` | UserProfile | register, login, logout | — | Partial |
| `donors` | DonorProfile, Donation, DonorBadge | edit_profile, donation_history | generate_donor_coordinates | Partial |
| `hospitals` | HospitalProfile | hospital_login, hospital_dashboard | — | Partial |
| `blood_requests` | BloodRequest | All action views | notify_donors_on_blood_request | Partial |
| `notifications` | Notification | list, detail, mark-read | — | Partial |
| `dashboard` | — | dashboard, toggle_availability | — | Partial |
| `bloodbank` | BloodStock, BloodRequest, LegacyBloodStock | stock_list, add_stock, request_blood | — | Partial |

> **Note:** The test files (`tests.py`) in each app are currently scaffolded. The test cases documented above represent the intended test suite. Full automated test implementation is a recommended next step for the project.
