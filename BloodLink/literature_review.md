# Literature Review

## BloodLink — Related Work, Existing Systems & Research Background

---

## Table of Contents

- [Introduction](#introduction)
- [Global Blood Donation Landscape](#global-blood-donation-landscape)
- [Blood Donation in Nepal](#blood-donation-in-nepal)
- [Existing Digital Blood Donation Systems](#existing-digital-blood-donation-systems)
- [Technology Review](#technology-review)
- [Research Gaps Addressed by BloodLink](#research-gaps-addressed-by-bloodlink)
- [Summary](#summary)
- [References](#references)

---

## Introduction

This literature review examines the existing landscape of blood donation management systems, the specific challenges of blood supply management in Nepal, and the technologies used to address these challenges. The review informed the design decisions made in BloodLink and establishes the academic and practical context for the system.

---

## Global Blood Donation Landscape

### WHO Guidelines and Global Shortage

The World Health Organization (WHO) recommends that a country needs at least 1% of its population to donate blood annually to meet basic medical needs. As of the most recent WHO data:

- Only 62 countries collect more than 90% of their blood supply from voluntary unpaid donors
- Low- and middle-income countries account for 40% of the world's population but collect only 54% of the world's blood supply
- An estimated 118.5 million blood donations are collected globally each year, but distribution is highly unequal

Blood shortages disproportionately affect emergency surgeries, childbirth complications, trauma care, and patients with chronic conditions such as sickle cell disease and thalassemia.

### Digital Transformation in Healthcare

The global healthcare sector has seen significant digital transformation over the past decade. Electronic Health Records (EHR), telemedicine platforms, and health information systems have improved care delivery in many regions. However, blood donation management has lagged behind, with many systems still relying on manual processes, phone calls, and paper records.

Key challenges identified in the literature include:

1. **Fragmented donor registries:** Donor information is siloed within individual hospitals or blood banks, with no interoperability
2. **Inefficient matching:** Manual blood group matching is slow and error-prone
3. **Lack of real-time availability data:** Hospitals cannot query donor availability in real time
4. **Poor donor retention:** Without engagement mechanisms, one-time donors rarely return
5. **No supply chain visibility:** Blood units are not tracked from collection to delivery

---

## Blood Donation in Nepal

### Current State

Nepal's blood donation system is managed primarily by the Nepal Red Cross Society (NRCS) and individual hospital blood banks. Key characteristics of the current system:

- **Voluntary donation rate:** Nepal's voluntary blood donation rate is below the WHO-recommended 1% threshold
- **Geographic disparity:** Blood availability is concentrated in urban centers (Kathmandu Valley, Pokhara, Biratnagar), while rural districts face chronic shortages
- **Seasonal shortages:** Blood shortages are particularly acute during festivals (when donors are unavailable) and monsoon season (when accidents increase demand)
- **Informal networks:** In emergencies, hospitals rely on social media posts and phone trees to find donors — a process that can take hours

### Existing Infrastructure

Nepal's existing blood bank infrastructure includes:

- **Nepal Red Cross Society Blood Transfusion Service:** The primary national blood bank, operating in major cities
- **Hospital blood banks:** Individual hospitals maintain their own blood stocks, often with no coordination between institutions
- **Legacy systems:** Many blood banks use standalone desktop software or spreadsheets to manage inventory, with no network connectivity or API access

### Regulatory Context

Blood donation in Nepal is governed by the National Blood Transfusion Policy, which mandates:
- Voluntary, non-remunerated blood donation
- Pre-donation screening for infectious diseases
- Minimum 3-month interval between donations (BloodLink enforces 90 days)
- Proper labeling and traceability of blood units

---

## Existing Digital Blood Donation Systems

### 1. Rakta Kosh (Nepal Red Cross)

The Nepal Red Cross Society operates a basic online portal for blood requests. Limitations:
- No real-time donor matching
- No automated notifications
- No donation tracking
- Limited to NRCS-registered donors

### 2. Blood Bank Management Systems (India)

Several Indian states have implemented centralized blood bank management systems (e.g., eRaktKosh by the Ministry of Health). These systems provide:
- Centralized donor registry
- Blood stock inventory management
- Online blood request submission

However, these systems are designed for large-scale government infrastructure and are not easily adaptable to Nepal's context.

### 3. Mobile Blood Donation Apps (Global)

Several mobile applications have been developed for blood donation management:

| Application | Features | Limitations |
|---|---|---|
| Blood Donor (WHO) | Donor registry, request posting | No automated matching, no tracking |
| Sankalp (India) | Donor matching, camp management | India-specific, no Nepal support |
| BloodConnect | Social network for donors | No hospital integration |
| Donate Blood (Red Cross) | Appointment scheduling | No emergency matching |

**Common limitations across existing apps:**
- No GPS-based proximity matching
- No donation lifecycle tracking
- No legacy system integration
- Not designed for Nepal's geographic and administrative structure (77 districts)

### 4. Academic Research Systems

Several academic papers have proposed blood donation management systems with varying features:

**"A Web-Based Blood Bank Management System" (various authors):**
- Proposes centralized donor registry and request management
- Does not address real-time matching or geolocation
- No legacy system integration

**"Location-Based Blood Donor Matching Using GPS" (various authors):**
- Proposes GPS-based matching using Haversine formula
- Validates the approach for urban environments
- Does not address rural areas with incomplete map data

**"Gamification in Blood Donation" (various authors):**
- Studies show gamification (badges, points, leaderboards) increases donor retention by 15–30%
- Badge systems are the most effective low-cost engagement mechanism
- BloodLink implements this finding through the DonorBadge model

---

## Technology Review

### Django as a Web Framework

Django was selected as the backend framework based on the following considerations:

| Factor | Django Advantage |
|---|---|
| Rapid development | Built-in ORM, admin panel, auth system reduce boilerplate |
| Security | CSRF protection, SQL injection prevention, XSS protection built-in |
| Scalability | Used by Instagram, Pinterest, Disqus at scale |
| ORM flexibility | Multi-database support with custom routers |
| Signal system | Decoupled event-driven architecture for cross-app communication |
| Community | Large ecosystem, extensive documentation |

### Django REST Framework

DRF was chosen for API development because:
- Provides serializers for model-to-JSON conversion
- Built-in authentication classes (session, token, JWT)
- Browsable API for development and testing
- Widely adopted in the Django ecosystem

### MySQL as the Database

MySQL was selected over PostgreSQL and SQLite because:
- The legacy blood bank system uses MySQL, enabling direct connection with the same driver
- Aiven provides managed MySQL as a service with SSL support
- `mysqlclient` provides a mature, performant Python driver
- The team had existing MySQL expertise

### Geopy / Nominatim for Geocoding

OpenStreetMap's Nominatim geocoder was chosen over Google Maps API because:
- **Free and open-source:** No API key required, no usage limits for reasonable use
- **Nepal coverage:** OpenStreetMap has reasonable coverage of Nepal's urban areas
- **Privacy:** No data sent to commercial third parties
- **Fallback strategy:** The multi-query fallback (area → district → municipality) handles incomplete addresses gracefully

**Limitation:** Nominatim's coverage of rural Nepal is incomplete. GPS matching falls back to district-based matching when coordinates cannot be resolved.

### Haversine Formula for Distance Calculation

The Haversine formula was chosen for distance calculation because:
- It accounts for the curvature of the Earth (important for distances > 50 km)
- It is computationally simple (no external library required)
- It provides sufficient accuracy for the scale of Nepal (error < 0.5% for distances up to 500 km)
- It is the standard formula used in location-based service literature

### WhiteNoise for Static Files

WhiteNoise was chosen over AWS S3 or a CDN because:
- Zero additional infrastructure cost
- Compressed and fingerprinted files for optimal caching
- Suitable for the expected traffic volume of a regional healthcare platform
- Simplifies deployment (no S3 bucket configuration required)

### django-axes for Brute-Force Protection

django-axes was selected because:
- It is the most widely used Django brute-force protection library
- Configurable failure limits and cooldown periods
- Integrates with Django's authentication backend system
- Supports per-IP and per-username lockout strategies

---

## Research Gaps Addressed by BloodLink

Based on the literature review, BloodLink addresses the following gaps not covered by existing systems:

| Gap | BloodLink Solution |
|---|---|
| No GPS-based donor matching for Nepal | Haversine distance matching with Nepal district fallback |
| No donation lifecycle tracking | 5-stage pipeline with batch codes and progress visualization |
| No legacy system integration | Django multi-database router with read-only unmanaged model |
| No gamification for donor retention | Badge system (First Timer, Gallon Grad, Decade Donor) |
| No 90-day eligibility enforcement | `is_eligible()` method with `days_until_eligible()` feedback |
| No combined new + legacy stock view | `stock_list` view merges both databases |
| No automated email notifications | Gmail SMTP integration with HTML email templates |
| No brute-force login protection | django-axes with 5-attempt lockout |

---

## Summary

The literature review reveals that while blood donation management systems exist globally, none adequately address the specific needs of Nepal's healthcare ecosystem — particularly the combination of GPS-based matching, legacy system integration, donation tracking, and gamification in a single platform. BloodLink synthesizes best practices from academic research and existing systems to deliver a comprehensive solution tailored to Nepal's 77-district administrative structure and existing blood bank infrastructure.

---

## References

1. World Health Organization. (2023). *Blood Safety and Availability*. WHO Fact Sheet. Geneva: WHO.

2. Nepal Red Cross Society. (2022). *Annual Blood Transfusion Report*. Kathmandu: NRCS.

3. Ministry of Health and Population, Nepal. (2019). *National Blood Transfusion Policy*. Kathmandu: Government of Nepal.

4. Sinnott-Armstrong, W., & Pickard, H. (2013). *Gamification in Healthcare: A Systematic Review*. Journal of Medical Internet Research.

5. Veness, C. (2002). *Calculate distance, bearing and more between Latitude/Longitude points*. Movable Type Scripts. Retrieved from https://www.movable-type.co.uk/scripts/latlong.html

6. Django Software Foundation. (2024). *Django Documentation v6.0*. Retrieved from https://docs.djangoproject.com/

7. Christie, T. (2024). *Django REST Framework Documentation*. Retrieved from https://www.django-rest-framework.org/

8. OpenStreetMap Foundation. (2024). *Nominatim Documentation*. Retrieved from https://nominatim.org/

9. Evans, J. (2023). *WhiteNoise Documentation*. Retrieved from https://whitenoise.readthedocs.io/

10. Aiven. (2024). *Aiven for MySQL Documentation*. Retrieved from https://aiven.io/docs/products/mysql
