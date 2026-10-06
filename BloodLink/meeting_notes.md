# Meeting Notes

## BloodLink — Project Meeting Logs & Decision Records

---

## Table of Contents

- [Meeting Log Index](#meeting-log-index)
- [Meeting 01 — Project Kickoff](#meeting-01--project-kickoff)
- [Meeting 02 — Requirements Finalization](#meeting-02--requirements-finalization)
- [Meeting 03 — Database Design Review](#meeting-03--database-design-review)
- [Meeting 04 — Core Feature Development Review](#meeting-04--core-feature-development-review)
- [Meeting 05 — Donor Matching Algorithm Design](#meeting-05--donor-matching-algorithm-design)
- [Meeting 06 — Notification System & Email Integration](#meeting-06--notification-system--email-integration)
- [Meeting 07 — Legacy System Integration](#meeting-07--legacy-system-integration)
- [Meeting 08 — Security Review](#meeting-08--security-review)
- [Meeting 09 — Deployment Planning](#meeting-09--deployment-planning)
- [Meeting 10 — Final Review & Documentation](#meeting-10--final-review--documentation)
- [Open Action Items](#open-action-items)
- [Key Decisions Log](#key-decisions-log)

---

## Meeting Log Index

| # | Date | Topic | Status |
|---|---|---|---|
| 01 | Project Start | Project Kickoff | Completed |
| 02 | Week 2 | Requirements Finalization | Completed |
| 03 | Week 3 | Database Design Review | Completed |
| 04 | Week 5 | Core Feature Development Review | Completed |
| 05 | Week 6 | Donor Matching Algorithm Design | Completed |
| 06 | Week 7 | Notification System & Email Integration | Completed |
| 07 | Week 8 | Legacy System Integration | Completed |
| 08 | Week 9 | Security Review | Completed |
| 09 | Week 10 | Deployment Planning | Completed |
| 10 | Week 11 | Final Review & Documentation | Completed |

---

## Meeting 01 — Project Kickoff

**Topic:** Project Kickoff  
**Attendees:** Development Team  
**Status:** Completed

### Agenda

1. Define the problem statement
2. Agree on project scope
3. Select technology stack
4. Assign initial responsibilities

### Discussion

The team discussed the core problem: Nepal lacks a centralized, real-time platform connecting blood donors with hospitals. The existing process relies on phone calls and social media, which is too slow for emergencies.

The team agreed that the system must:
- Be web-based (accessible without a mobile app)
- Support both donors and hospitals as distinct user types
- Automate the donor-hospital matching process
- Be deployable on a free or low-cost cloud platform

### Decisions Made

| Decision | Rationale |
|---|---|
| Use Django as the backend framework | Team familiarity, built-in admin, ORM, auth system |
| Use MySQL as the database | Compatibility with existing legacy blood bank system |
| Target Nepal's 77 districts | Scope the geographic coverage to Nepal |
| Use Render for deployment | Free tier available, supports Python/Django, easy GitHub integration |
| Use Gmail SMTP for email | Free, no additional infrastructure required |

### Action Items

| Item | Owner | Due |
|---|---|---|
| Set up Django project structure | Dev Team | Week 2 |
| Create initial database schema draft | Dev Team | Week 2 |
| Research geocoding options for Nepal | Dev Team | Week 2 |

---

## Meeting 02 — Requirements Finalization

**Topic:** Requirements Finalization  
**Attendees:** Development Team  
**Status:** Completed

### Agenda

1. Finalize functional requirements
2. Define user roles and permissions
3. Agree on data models

### Discussion

The team reviewed the initial requirements and refined them based on research into Nepal's blood donation ecosystem. Key discussions:

**User Roles:**
- Two primary roles: `donor` and `hospital`
- Hospital accounts created by admin (not self-registration) to prevent fake hospital accounts
- Donors self-register through the public registration form

**Blood Request Workflow:**
- Hospitals post requests with blood group, units required, urgency, and location
- System automatically matches and notifies donors
- Donors accept or decline; hospitals confirm receipt

**Eligibility:**
- 90-day minimum interval between donations (aligned with Nepal's National Blood Transfusion Policy)
- System enforces this automatically — donors cannot accept requests if ineligible

### Decisions Made

| Decision | Rationale |
|---|---|
| Hospital accounts created via Django admin only | Prevents fake hospital registrations |
| 90-day donation cooldown | Aligned with national policy and WHO guidelines |
| Top 10 donors notified per request | Balance between coverage and notification spam |
| Urgency levels: Normal, Urgent, Critical | Allows hospitals to communicate priority |
| District + municipality + ward + area for location | Sufficient granularity for Nepal's administrative structure |

### Action Items

| Item | Owner | Due |
|---|---|---|
| Finalize `DonorProfile` model fields | Dev Team | Week 3 |
| Finalize `BloodRequest` model fields | Dev Team | Week 3 |
| Design `Notification` model | Dev Team | Week 3 |

---

## Meeting 03 — Database Design Review

**Topic:** Database Design Review  
**Attendees:** Development Team  
**Status:** Completed

### Agenda

1. Review proposed database schema
2. Discuss multi-database strategy for legacy integration
3. Finalize relationships

### Discussion

**Multi-Database Strategy:**
The team discussed how to integrate the existing legacy blood bank database without disrupting it. Two options were considered:

- **Option A:** Migrate all legacy data into the new database
- **Option B:** Connect to the legacy database in read-only mode

Option B was selected because it allows the legacy system to continue operating without any changes, and data can be imported incrementally using the import tool.

**Notification as Join Table:**
The team debated whether to use a direct many-to-many relationship between donors and blood requests, or a dedicated `Notification` model. The `Notification` model was chosen because it needs to store per-donor state (response, is_read, message, timestamp).

**Atomic Unit Fulfillment:**
The team identified a potential race condition in `units_fulfilled` updates. The solution — using Django's `F()` expression for atomic database-level increments — was agreed upon.

### Decisions Made

| Decision | Rationale |
|---|---|
| Two-database architecture (default + legacy) | Zero disruption to legacy system |
| `LegacyRouter` with `managed=False` | Prevents Django from modifying legacy tables |
| `Notification` as enriched join table | Supports per-donor state tracking |
| `F('units_fulfilled') + 1` for atomic updates | Prevents race conditions |
| `batch_code` with UUID-based generation | Unique, human-readable donation tracking |
| `unique_together` on `(donor, badge_key)` | Prevents duplicate badge awards |

### Action Items

| Item | Owner | Due |
|---|---|---|
| Implement `LegacyRouter` | Dev Team | Week 4 |
| Create all model migrations | Dev Team | Week 4 |
| Test multi-database routing | Dev Team | Week 4 |

---

## Meeting 04 — Core Feature Development Review

**Topic:** Core Feature Development Review  
**Attendees:** Development Team  
**Status:** Completed

### Agenda

1. Review completed models and migrations
2. Review registration and login flows
3. Review hospital dashboard

### Discussion

The core models (`DonorProfile`, `HospitalProfile`, `BloodRequest`, `Notification`, `Donation`) were reviewed and approved. The registration flow was tested — it correctly creates `User`, `UserProfile`, and `DonorProfile` in a single transaction.

**Issue Identified:** The hospital dashboard was initially showing all blood requests system-wide, not just the logged-in hospital's requests. This was fixed by filtering `BloodRequest.objects.filter(hospital=hospital)`.

**Issue Identified:** The donor dashboard was not syncing `last_donation_date` from actual `Donation` records. A sync step was added to the dashboard view.

### Decisions Made

| Decision | Rationale |
|---|---|
| Dashboard syncs `last_donation_date` from Donation records | Ensures eligibility check uses actual donation data |
| Hospital dashboard filters by `hospital=request.user.hospital_profile` | Security — hospitals only see their own requests |
| Role detection via `hasattr(user, 'donor_profile')` | Simpler than checking `UserProfile.role` field |

### Action Items

| Item | Owner | Due |
|---|---|---|
| Implement donor matching signal | Dev Team | Week 6 |
| Implement notification creation service | Dev Team | Week 6 |
| Implement email notification | Dev Team | Week 7 |

---

## Meeting 05 — Donor Matching Algorithm Design

**Topic:** Donor Matching Algorithm Design  
**Attendees:** Development Team  
**Status:** Completed

### Agenda

1. Design the donor matching algorithm
2. Select distance calculation method
3. Define fallback strategy for donors without GPS coordinates

### Discussion

**Distance Calculation:**
Three options were considered:
- **Euclidean distance:** Simple but inaccurate for geographic coordinates
- **Haversine formula:** Accounts for Earth's curvature, standard for GPS distances
- **Google Maps Distance Matrix API:** Most accurate but requires paid API key

The Haversine formula was selected as the best balance of accuracy and cost.

**Geocoding Strategy:**
The team discussed how to obtain GPS coordinates for donors and blood requests. Options:
- **Manual entry:** Donors enter coordinates manually — poor UX
- **Browser geolocation API:** Requires user permission, not persistent
- **Address-based geocoding:** Auto-geocode from district/municipality/ward/area

Address-based geocoding using Nominatim was selected. The multi-query fallback strategy (most specific → least specific) was designed to handle incomplete OpenStreetMap data.

**Fallback for Missing Coordinates:**
When a blood request or donor does not have GPS coordinates, the system falls back to district-based matching. This ensures the system works even in areas with poor OpenStreetMap coverage.

### Decisions Made

| Decision | Rationale |
|---|---|
| Haversine formula for distance | Accurate, free, no external API |
| Nominatim for geocoding | Free, open-source, reasonable Nepal coverage |
| Multi-query geocoding fallback | Handles incomplete addresses gracefully |
| District-based fallback when no GPS | Ensures matching works without coordinates |
| Top 10 donors by proximity | Limits notification volume while ensuring coverage |
| Geocode on save, cache in DB | Avoids repeated API calls |

### Action Items

| Item | Owner | Due |
|---|---|---|
| Implement `calculate_distance()` in `donors/utils.py` | Dev Team | Week 6 |
| Implement `get_coordinates()` in `donors/services.py` | Dev Team | Week 6 |
| Implement `post_save` signal in `blood_requests/signals.py` | Dev Team | Week 6 |
| Test matching with sample donor data | Dev Team | Week 6 |

---

## Meeting 06 — Notification System & Email Integration

**Topic:** Notification System & Email Integration  
**Attendees:** Development Team  
**Status:** Completed

### Agenda

1. Review notification model and service
2. Review email integration
3. Test end-to-end notification flow

### Discussion

The notification system was reviewed. The `create_notification()` service function was approved as a clean abstraction over direct model creation.

**Email Template:**
The team agreed to use a plain-text email template for maximum compatibility across email clients. The template is located at `notifications/templates/emails/blood_request_notification.txt`.

**Issue Identified:** The `dashboard_url` in `email_utils.py` is hardcoded to `http://127.0.0.1:8000/dashboard/`. This will send incorrect links in production. This was flagged as a known issue to be fixed before production deployment.

**Email Failure Handling:**
The team decided that email failures should be logged but not raise exceptions, to prevent a single email failure from blocking the entire notification batch. The `fail_silently=False` with a try/except block was implemented.

### Decisions Made

| Decision | Rationale |
|---|---|
| Plain-text email template | Maximum email client compatibility |
| Log email failures, don't raise | Prevents one failure from blocking all notifications |
| `EmailMultiAlternatives` for future HTML support | Allows adding HTML version later without refactoring |
| `dashboard_url` hardcoded — flagged as known issue | Needs to be made configurable via settings |

### Action Items

| Item | Owner | Due |
|---|---|---|
| Create email template | Dev Team | Week 7 |
| Test email delivery with Gmail SMTP | Dev Team | Week 7 |
| Fix `dashboard_url` hardcoding before production | Dev Team | Before deployment |

---

## Meeting 07 — Legacy System Integration

**Topic:** Legacy System Integration  
**Attendees:** Development Team  
**Status:** Completed

### Agenda

1. Review legacy database connection
2. Review `LegacyBloodStock` unmanaged model
3. Review combined stock view
4. Review import tool

### Discussion

The legacy database integration was reviewed. The `LegacyRouter` correctly routes reads to the `legacy` database and blocks writes.

**Issue Identified:** The `LegacyBloodStock` model maps to `old_blood_table`, but the actual legacy table name may differ. The team agreed to document this clearly and provide instructions for running `inspectdb` to verify the schema.

**Import Tool:**
The `import_legacy_to_new` view was reviewed. It uses `get_or_create` to avoid duplicates and updates quantities additively. The team agreed this is appropriate for a one-time or periodic import.

### Decisions Made

| Decision | Rationale |
|---|---|
| `managed = False` on `LegacyBloodStock` | Prevents Django from touching the legacy table |
| `db_table = 'old_blood_table'` — must be verified | Document as a configuration step |
| Additive import (not replace) | Preserves existing new-system stock |
| Combined view shows new + legacy + total | Gives operators full visibility |

### Action Items

| Item | Owner | Due |
|---|---|---|
| Document legacy table name configuration | Dev Team | Week 8 |
| Test import tool with sample legacy data | Dev Team | Week 8 |
| Add error handling for legacy DB connection failure | Dev Team | Future sprint |

---

## Meeting 08 — Security Review

**Topic:** Security Review  
**Attendees:** Development Team  
**Status:** Completed

### Agenda

1. Review authentication and authorization
2. Review brute-force protection
3. Review production security headers
4. Identify security gaps

### Discussion

The security configuration was reviewed against Django's security checklist and OWASP guidelines.

**django-axes Configuration:**
- 5 failure limit was agreed upon as a balance between security and usability
- 1-hour cooldown was selected
- `AXES_RESET_ON_SUCCESS = True` ensures legitimate users are not permanently locked out

**Production Security Headers:**
All production security headers (`SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`) are enabled automatically when `DEBUG=False`. This was verified.

**Authorization Gaps Identified:**
- `DeclineBloodRequestView` and `CompleteDonationView` do not have explicit `permission_classes` — they rely on session auth implicitly. This should be made explicit.
- `ConfirmBloodReceivedView` does not have `@login_required` — it relies on `get_object_or_404(HospitalProfile, user=request.user)` which will return 404 for unauthenticated users. This is functionally secure but should be made explicit.

### Decisions Made

| Decision | Rationale |
|---|---|
| 5 failed logins → 1-hour lockout | Balance between security and usability |
| All security headers via `DEBUG=False` | Single toggle for production security |
| `SECURE_PROXY_SSL_HEADER` for Render | Render terminates SSL at the proxy level |
| Document authorization gaps as known issues | Fix in next sprint |

### Action Items

| Item | Owner | Due |
|---|---|---|
| Add explicit `permission_classes` to all APIViews | Dev Team | Next sprint |
| Add `@login_required` to `ConfirmBloodReceivedView` | Dev Team | Next sprint |
| Run security headers check post-deployment | Dev Team | After deployment |

---

## Meeting 09 — Deployment Planning

**Topic:** Deployment Planning  
**Attendees:** Development Team  
**Status:** Completed

### Agenda

1. Finalize deployment platform selection
2. Configure Aiven MySQL
3. Plan deployment steps
4. Define rollback procedure

### Discussion

**Platform Selection:**
Render was confirmed as the deployment platform. Key reasons:
- Free tier supports Python/Django web services
- GitHub integration for automatic deployments
- Environment variable management via dashboard
- Shell access for running management commands

**Database:**
Aiven MySQL was selected for the cloud database. The `DATABASE_URL` environment variable approach (via `dj-database-url`) was confirmed as the correct configuration method.

**Static Files:**
WhiteNoise was confirmed as the static file solution. The build command `python manage.py collectstatic --noinput` was added.

**Issue Identified:** The `.env` file has `DEBUG=True` appearing twice. The second occurrence is redundant. This was flagged for cleanup.

### Decisions Made

| Decision | Rationale |
|---|---|
| Render for web hosting | Free tier, GitHub integration, Python support |
| Aiven MySQL for cloud DB | Managed, SSL-enabled, reliable |
| WhiteNoise for static files | No additional infrastructure needed |
| `DATABASE_URL` overrides individual DB vars | Standard cloud deployment pattern |
| Gunicorn as WSGI server | Production-grade, standard for Django on Render |

### Action Items

| Item | Owner | Due |
|---|---|---|
| Set up Aiven MySQL service | Dev Team | Week 10 |
| Configure Render web service | Dev Team | Week 10 |
| Set all environment variables on Render | Dev Team | Week 10 |
| Run `migrate` and `createsuperuser` post-deploy | Dev Team | Week 10 |
| Fix duplicate `DEBUG=True` in `.env` | Dev Team | Week 10 |

---

## Meeting 10 — Final Review & Documentation

**Topic:** Final Review & Documentation  
**Attendees:** Development Team  
**Status:** Completed

### Agenda

1. Review deployed application
2. Identify remaining issues
3. Plan documentation

### Discussion

The deployed application on Render was reviewed. All core features were verified as working:
- Donor registration and login
- Hospital login and dashboard
- Blood request creation and donor notification
- Accept/decline/complete/confirm flow
- Donation history and badge display
- Blood stock management

**Remaining Issues Identified:**
- `dashboard_url` in email still points to localhost
- Legacy DB not accessible from Render (expected — local only)
- `decade_donor` badge condition not implemented
- JWT endpoints not wired up

These were documented as known issues for future sprints.

### Decisions Made

| Decision | Rationale |
|---|---|
| Document all known issues in `testing.md` | Transparency for future developers |
| Write all documentation files | Professional project documentation |
| Keep JWT installed but not wired | Available for future mobile client |

### Action Items

| Item | Owner | Due |
|---|---|---|
| Write all documentation MD files | Dev Team | Final week |
| Fix `dashboard_url` in email | Dev Team | Next sprint |
| Implement `decade_donor` badge logic | Dev Team | Next sprint |
| Add explicit permission classes to all views | Dev Team | Next sprint |

---

## Open Action Items

| Item | Priority | Status |
|---|---|---|
| Fix `dashboard_url` hardcoding in `email_utils.py` | Medium | Open |
| Remove duplicate `DEBUG=True` from `.env` | Low | Open |
| Add error handling for legacy DB connection failure in `stock_list` | Medium | Open |
| Add explicit `permission_classes` to `DeclineBloodRequestView` and `CompleteDonationView` | Medium | Open |
| Implement `decade_donor` badge logic | Low | Open |
| Wire JWT endpoints for mobile client support | Low | Open |
| Add `@login_required` to `ConfirmBloodReceivedView` | Medium | Open |

---

## Key Decisions Log

A consolidated record of all major architectural and design decisions made during the project.

| # | Decision | Meeting | Rationale |
|---|---|---|---|
| 1 | Django as backend framework | 01 | Team familiarity, built-in features |
| 2 | MySQL as database | 01 | Legacy system compatibility |
| 3 | Render for deployment | 01 | Free tier, GitHub integration |
| 4 | Hospital accounts via admin only | 02 | Prevent fake hospital registrations |
| 5 | 90-day donation cooldown | 02 | National policy compliance |
| 6 | Top 10 donors notified per request | 02 | Balance coverage vs. spam |
| 7 | Two-database architecture | 03 | Zero disruption to legacy system |
| 8 | `Notification` as enriched join table | 03 | Per-donor state tracking |
| 9 | `F()` expression for atomic unit updates | 03 | Race condition prevention |
| 10 | Haversine formula for distance | 05 | Accurate, free, no API key |
| 11 | Nominatim for geocoding | 05 | Free, open-source |
| 12 | District fallback when no GPS | 05 | Works without coordinates |
| 13 | Plain-text email template | 06 | Maximum email client compatibility |
| 14 | Log email failures, don't raise | 06 | Prevents batch notification failure |
| 15 | `managed=False` on LegacyBloodStock | 07 | Protects legacy table |
| 16 | 5 failed logins → 1-hour lockout | 08 | Security vs. usability balance |
| 17 | WhiteNoise for static files | 09 | No additional infrastructure |
| 18 | `DATABASE_URL` overrides individual vars | 09 | Standard cloud deployment pattern |
