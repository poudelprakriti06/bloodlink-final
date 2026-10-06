# Introduction

## BloodLink — Blood Donation Management System

---

## Table of Contents

- [Background](#background)
- [Problem Statement](#problem-statement)
- [Motivation](#motivation)
- [Project Objectives](#project-objectives)
- [Scope of the System](#scope-of-the-system)
- [Target Users](#target-users)
- [Expected Outcomes](#expected-outcomes)
- [Limitations](#limitations)

---

## Background

Blood donation is one of the most critical components of a functioning healthcare system. According to the World Health Organization (WHO), a country requires a minimum of 1% of its population to donate blood annually to meet basic medical needs. In Nepal, voluntary blood donation rates remain significantly below this threshold, and the existing infrastructure for connecting donors with hospitals is fragmented, manual, and inefficient.

Hospitals in Nepal — particularly in semi-urban and rural districts — frequently face acute blood shortages during emergencies. The process of finding a compatible donor typically involves phone calls, social media posts, and word-of-mouth, all of which are slow and unreliable in time-critical situations. There is no centralized digital platform that allows hospitals to broadcast blood requests and automatically reach verified, eligible donors in real time.

BloodLink was conceived and developed to address this gap. It is a web-based blood donation management system that digitizes and automates the entire process — from donor registration and hospital blood requests to donor matching, notification dispatch, donation tracking, and blood stock management.

---

## Problem Statement

The current blood donation ecosystem in Nepal suffers from the following critical deficiencies:

1. **No centralized donor registry:** Donor information is scattered across individual hospitals, blood banks, and informal networks. There is no unified database that hospitals can query in real time.

2. **Inefficient matching:** When a hospital needs blood, staff manually search for donors by blood group, often without knowledge of donor location, availability, or recent donation history. This wastes time in emergencies.

3. **No eligibility enforcement:** Donors can be contacted and asked to donate even if they donated recently (within 90 days), which poses health risks and leads to donor fatigue.

4. **Lack of donation transparency:** Donors have no visibility into what happens to their donated blood after collection. There is no tracking from collection through processing, testing, and delivery.

5. **Legacy system isolation:** Existing blood bank systems store historical stock data in isolated databases with no integration into modern request management workflows.

6. **No gamification or engagement:** There are no mechanisms to recognize and reward repeat donors, leading to low donor retention rates.

---

## Motivation

The development of BloodLink was motivated by:

- The urgent need for a digital solution to Nepal's blood shortage crisis
- The availability of modern web technologies (Django, REST APIs, geolocation services) that make such a system feasible to build and deploy at low cost
- The opportunity to integrate with existing legacy blood bank infrastructure rather than replacing it entirely
- The desire to create a system that is accessible, secure, and scalable across all 77 districts of Nepal

---

## Project Objectives

The primary objectives of BloodLink are:

### Core Objectives

1. **Centralize donor management:** Build a unified registry of blood donors across Nepal, capturing blood group, location, availability, and donation history.

2. **Automate donor-hospital matching:** Implement an intelligent matching algorithm that identifies the nearest eligible donors for a given blood request using GPS coordinates and the Haversine distance formula.

3. **Real-time notification system:** Automatically notify matched donors via in-app notifications and email when a blood request is created.

4. **Full donation lifecycle tracking:** Track each donation through five stages — Collected, Processing, Testing, Shipped, and Delivered — with a unique batch code for traceability.

5. **Hospital request management:** Provide hospitals with a dedicated interface to post blood requests, monitor donor responses, confirm blood receipt, and manage request status.

6. **Blood stock management:** Maintain a real-time inventory of blood stocks, integrated with the legacy blood bank database for a combined view.

7. **Legacy system integration:** Connect to the existing legacy blood bank database in read-only mode, enabling data continuity without disrupting the old system.

### Secondary Objectives

8. **Donor engagement through gamification:** Award badges to donors based on donation milestones to encourage repeat participation.

9. **Security and access control:** Implement brute-force login protection, role-based access (donor vs. hospital), and production-grade security headers.

10. **Scalable deployment:** Deploy the system on a cloud platform (Render) with a managed cloud database (Aiven MySQL) to ensure availability and scalability.

---

## Scope of the System

### In Scope

- Donor registration, profile management, and availability toggling
- Hospital registration and profile management (via Django admin)
- Blood request creation, management, and lifecycle (Pending → Accepted → Completed → Fulfilled / Cancelled)
- Automated donor matching using GPS proximity (Haversine) with district-based fallback
- In-app notification system with read/unread tracking
- Email notification dispatch via Gmail SMTP
- Donation record creation with batch code generation
- Donation status tracking (5-stage pipeline)
- Badge award system (First Timer, Gallon Grad, Decade Donor)
- Blood stock inventory management (new system)
- Legacy blood bank database integration (read-only)
- Legacy-to-new stock import tool
- Donor dashboard with statistics and donation history
- Hospital dashboard with request and donor response management
- REST API for blood requests and notifications
- Production deployment on Render with Aiven MySQL

### Out of Scope

- Mobile application (iOS / Android)
- Payment or incentive processing
- Real-time chat between donors and hospitals
- Integration with government health databases (e.g., NHRC Nepal)
- Automated blood type compatibility cross-matching (e.g., plasma, platelets)
- SMS notification system
- Multi-language support (Nepali language interface)

---

## Target Users

| User Type | Description |
|---|---|
| **Blood Donors** | Individuals registered on the platform who are willing to donate blood. They receive notifications, accept or decline requests, and track their donation history. |
| **Hospitals** | Healthcare institutions that post blood requests when they need blood for patients. They manage requests, confirm donor arrivals, and track fulfillment. |
| **System Administrators** | Technical staff who manage the platform via the Django admin panel, including creating hospital accounts, managing users, and monitoring system health. |

---

## Expected Outcomes

Upon successful deployment and adoption of BloodLink, the following outcomes are expected:

1. **Reduced response time** in blood procurement during emergencies, from hours to minutes
2. **Increased donor engagement** through transparent tracking and gamification
3. **Improved donor eligibility compliance** through automated 90-day cooldown enforcement
4. **Better blood stock visibility** through combined new + legacy inventory views
5. **Data continuity** from legacy systems without requiring a full migration
6. **Scalable infrastructure** capable of serving all 77 districts of Nepal

---

## Limitations

| Limitation | Description |
|---|---|
| Geocoding accuracy | The system relies on OpenStreetMap (Nominatim) for geocoding. Rural areas in Nepal may have incomplete or inaccurate map data, reducing GPS matching precision. |
| Email deliverability | Email notifications depend on Gmail SMTP. High-volume sending may trigger rate limits or spam filters. |
| Legacy DB dependency | The legacy database integration assumes a specific table structure (`old_blood_table`). Any schema changes in the legacy system require manual updates to the `LegacyBloodStock` model. |
| No real-time updates | The system does not use WebSockets or push notifications. Donors must refresh the dashboard to see new notifications. |
| Single blood bank scope | The current blood stock module manages a single blood bank's inventory. Multi-branch or multi-hospital stock management is not yet supported. |
| Manual hospital onboarding | Hospital accounts must be created by an administrator via the Django admin panel. Self-registration for hospitals is not available. |
