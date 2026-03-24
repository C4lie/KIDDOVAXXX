# KiddoVax — Project Documentation

> Generated: 2026-03-24  
> Django 3.1.1 · SQLite · No REST Framework · Template-based UI

---

## 1. System Overview

**KiddoVax** is a vaccine appointment management system designed to coordinate childhood vaccinations across multiple hospitals. The platform serves four distinct user roles — Admin, Hospital (Doctor), Receptionist, and Patient — each with their own dedicated portal.

| Property | Value |
|----------|-------|
| **Framework** | Django 3.1.1 |
| **Database** | SQLite (`db.sqlite3`) |
| **API Style** | None — all HTML template responses |
| **Auth Mechanism** | Custom session-based (plain-text passwords in DB) |
| **Deployment Mode** | Development (`DEBUG=True`) |
| **Language** | Python 3 |

### What the System Does

1. **Admin** sets up the platform by registering cities, areas, and hospitals.
2. **Hospitals** log in to register their receptionist staff and add their vaccine catalogue.
3. **Patients** self-register, browse vaccines, and book appointments for their children.
4. **Receptionists** manage the physical visit — checking patients in (RFID scan + arrival time) and checking them out (departure time).

---

## 2. Architecture

### Style
**Modular Monolith** — A single Django project split into four role-based apps. Apps share models via Python imports but each owns its own views, URLs, and templates.

### No REST Framework
Django REST Framework is **not installed**. There are no serializers, API ViewSets, or JSON endpoints. All 43 endpoints return rendered HTML templates.

### Dependency Graph

```
adminapp  (City, Area, Admintbl)
    └── hospitalapp  (Hospitaltbl, Vaccinetbl, Receptionisttbl)
            └── patientapp  (Patienttbl, Appointmenttbl)
                    └── receptionistapp  (no own models — views only)
```

### URL Routing

| URL Prefix | App |
|------------|-----|
| `/` | `patientapp` |
| `/admin/` | `adminapp` |
| `/hospital/` | `hospitalapp` |
| `/receptionist/` | `receptionistapp` |

### Settings Highlights

| Setting | Value |
|---------|-------|
| `DEBUG` | `True` |
| `DATABASES` | SQLite |
| `STATIC_URL` | `/static/` |
| `MEDIA_ROOT` | `static/` |
| `AUTH_PASSWORD_VALIDATORS` | Django defaults (not applied to custom auth) |
| `INSTALLED_APPS` | `adminapp`, `hospitalapp`, `patientapp`, `receptionistapp` |

---

## 3. Apps and Modules

### `adminapp`
**Purpose:** Platform configuration layer. Manages admin accounts and location master data (cities and areas) that all other apps reference.

| File | Present |
|------|---------|
| `models.py` | ✅ |
| `views.py` | ✅ |
| `urls.py` | ✅ |
| `forms.py` | ✅ |
| `admin.py` | ✅ |
| `templates/` | ✅ |
| `migrations/` | ✅ |

---

### `hospitalapp`
**Purpose:** Hospital registration, vaccine catalogue management, receptionist staff management, and appointment viewing.

| File | Present |
|------|---------|
| `models.py` | ✅ |
| `views.py` | ✅ |
| `urls.py` | ✅ |
| `forms.py` | ✅ |
| `admin.py` | ✅ |
| `templates/` | ✅ |
| `migrations/` | ✅ |

---

### `patientapp`
**Purpose:** Patient self-registration, login, vaccine appointment booking, appointment management, and password management.

| File | Present |
|------|---------|
| `models.py` | ✅ |
| `views.py` | ✅ |
| `urls.py` | ✅ |
| `forms.py` | ✅ |
| `admin.py` | ✅ |
| `templates/` | ✅ |
| `migrations/` | ✅ |

---

### `receptionistapp`
**Purpose:** Receptionist-facing dashboard for managing patient visit check-in and check-out. Has **no own models** — operates entirely on `hospitalapp` and `patientapp` models.

| File | Present |
|------|---------|
| `models.py` | ✅ (empty) |
| `views.py` | ✅ |
| `urls.py` | ✅ |
| `admin.py` | ✅ |
| `templates/` | ✅ |
| `migrations/` | ✅ |

---

## 4. Data Models

### `Admintbl` — `adminapp`
Admin login credentials.

| Field | Type | Notes |
|-------|------|-------|
| `id` | AutoField PK | Auto |
| `username` | CharField(100) | |
| `password` | CharField(200) | Plain text |

---

### `City` — `adminapp`
City master data.

| Field | Type | Notes |
|-------|------|-------|
| `id` | AutoField PK | Auto |
| `cityName` | CharField(255) | |

---

### `Area` — `adminapp`
Area/locality master data.

| Field | Type | Notes |
|-------|------|-------|
| `id` | AutoField PK | Auto |
| `areaName` | CharField(255) | |
| `cityId` | FK → `City` | CASCADE |

---

### `Hospitaltbl` — `hospitalapp`
Hospital registration with doctor info.

| Field | Type | Notes |
|-------|------|-------|
| `id` | AutoField PK | Auto |
| `title` | CharField(500) | Hospital name |
| `dcrname` | CharField(255) | Doctor name (nullable) |
| `address` | CharField(500) | |
| `cityId` | FK → `City` | CASCADE |
| `areaId` | FK → `Area` | CASCADE |
| `contactNo` | IntegerField | Used as login username |
| `password` | CharField(255) | Plain text |
| `img` | ImageField | `upload_to='profileimg'` |

---

### `Vaccinetbl` — `hospitalapp`
Vaccine catalogue per hospital.

| Field | Type | Notes |
|-------|------|-------|
| `id` | AutoField PK | Auto |
| `vaccineName` | CharField(255) | |
| `vaccineDescr` | CharField(500) | |
| `price` | IntegerField | Nullable |
| `hospitalId` | FK → `Hospitaltbl` | CASCADE |

---

### `Receptionisttbl` — `hospitalapp`
Receptionist staff per hospital.

| Field | Type | Notes |
|-------|------|-------|
| `id` | AutoField PK | Auto |
| `name` | CharField(255) | |
| `address` | CharField(500) | |
| `gender` | CharField(10) | Default: `'Male'` |
| `contactNo` | IntegerField | Used as login username |
| `password` | CharField(255) | Plain text |
| `staffimg` | ImageField | `upload_to='staffimages'` |
| `doj` | DateField | Date of joining |
| `hospitalid` | FK → `Hospitaltbl` | CASCADE |
| `cityId` | FK → `City` | CASCADE |
| `areaId` | FK → `Area` | CASCADE |

---

### `Patienttbl` — `patientapp`
Patient account information.

| Field | Type | Notes |
|-------|------|-------|
| `id` | AutoField PK | Auto |
| `name` | CharField(255) | |
| `address` | CharField(500) | |
| `contactNo` | IntegerField | Used as login username; must be unique |
| `password` | CharField(255) | Plain text |
| `cityId` | FK → `City` | CASCADE |
| `areaId` | FK → `Area` | CASCADE |

---

### `Appointmenttbl` — `patientapp`
Vaccine appointment record with check-in/out tracking.

| Field | Type | Notes |
|-------|------|-------|
| `id` | AutoField PK | Auto |
| `childname` | CharField(255) | Name of child being vaccinated |
| `aptdate` | DateField | Appointment date |
| `active` | IntegerField | Status: `0`=Pending, `1`=Checked-In, `2`=Checked-Out |
| `rfidno` | IntegerField | RFID assigned at check-in |
| `indt` | DateTimeField | Auto set at check-in |
| `outdt` | DateTimeField | Auto set at check-out |
| `hospitalid` | FK → `Hospitaltbl` | CASCADE |
| `vaccineid` | FK → `Vaccinetbl` | CASCADE |
| `patientid` | FK → `Patienttbl` | CASCADE |

**Appointment Status State Machine:**
```
active = 0  →  Booked / Pending
active = 1  →  Checked In  (rfidno + indt recorded)
active = 2  →  Checked Out (outdt recorded)
```

---

### Model Summary

| Model | App | FKs To |
|-------|-----|--------|
| `Admintbl` | adminapp | — |
| `City` | adminapp | — |
| `Area` | adminapp | City |
| `Hospitaltbl` | hospitalapp | City, Area |
| `Vaccinetbl` | hospitalapp | Hospitaltbl |
| `Receptionisttbl` | hospitalapp | Hospitaltbl, City, Area |
| `Patienttbl` | patientapp | City, Area |
| `Appointmenttbl` | patientapp | Hospitaltbl, Vaccinetbl, Patienttbl |

---

## 5. API Endpoints

> All endpoints return **rendered HTML**. No JSON/REST responses.  
> Auth = session key `CName` must exist (set at login).

### `adminapp` — Prefix `/admin/`

| URL | Methods | View | Auth | Purpose |
|-----|---------|------|------|---------|
| `/admin/` | GET | `Home` | ✅ | Admin dashboard |
| `/admin/login/` | GET, POST | `AdminLogin` | ❌ | Admin login |
| `/admin/logout/` | GET | `Logout` | ❌ | Admin logout |
| `/admin/newadmin/` | GET, POST | `AdminCreation` | ✅ | Create admin account |
| `/admin/city/` | GET, POST | `ManageCity` | ✅ | List / add city |
| `/admin/editcity/<id>/` | GET, POST | `ManageCity` | ✅ | Edit city |
| `/admin/deletecity/<cityid>/` | GET | `ManageCity` | ✅ | Delete city |
| `/admin/addarea/` | GET, POST | `ManageArea` | ✅ | List / add area |
| `/admin/editarea/<id>/` | GET, POST | `ManageArea` | ✅ | Edit area |
| `/admin/deletearea/<areaid>/` | GET | `ManageArea` | ✅ | Delete area |
| `/admin/bindareas/` | GET | `load_areasbyCity` | ❌ | AJAX: areas by city |
| `/admin/addhospitals/` | GET, POST | `ManageHospitals` | ✅ | List / add hospital |
| `/admin/edithospital/<id>/` | GET, POST | `ManageHospitals` | ✅ | Edit hospital |
| `/admin/deletehospital/<pid>/` | GET | `ManageHospitals` | ✅ | Delete hospital |

### `hospitalapp` — Prefix `/hospital/`

| URL | Methods | View | Auth | Purpose |
|-----|---------|------|------|---------|
| `/hospital/` | GET | `Home` | ✅ | Hospital dashboard |
| `/hospital/login/` | GET, POST | `HospitalLogin` | ❌ | Hospital login |
| `/hospital/logout/` | GET | `Logout` | ❌ | Hospital logout |
| `/hospital/bindareas/` | GET | `load_areasbyCity` | ❌ | AJAX: areas by city |
| `/hospital/register/` | GET, POST | `ReceptionistRegister` | ✅ | List / add receptionist |
| `/hospital/editreceptionist/<id>/` | GET, POST | `ReceptionistRegister` | ✅ | Edit receptionist |
| `/hospital/deletereceptionist/<pid>/` | GET | `ReceptionistRegister` | ✅ | Delete receptionist |
| `/hospital/vaccine/` | GET, POST | `ManageVaccine` | ✅ | List / add vaccine |
| `/hospital/editvaccine/<id>/` | GET, POST | `ManageVaccine` | ✅ | Edit vaccine |
| `/hospital/deletevaccine/<vid>/` | GET | `ManageVaccine` | ✅ | Delete vaccine |
| `/hospital/showbooking/` | GET | `ShowAppointments` | ✅ | Today's appointments |
| `/hospital/showpastbooking/` | GET | `ShowPastAppointments` | ✅ | Past appointments |

### `patientapp` — Prefix `/` (root)

| URL | Methods | View | Auth | Purpose |
|-----|---------|------|------|---------|
| `/` | GET | `Home` | ❌ | Public home page |
| `/about/` | GET | `About` | ❌ | About page |
| `/contact/` | GET | `Contact` | ❌ | Contact page |
| `/login/` | GET, POST | `PatientLogin` | ❌ | Patient login |
| `/register/` | GET, POST | `PatientRegistration` | ❌ | Patient registration |
| `/logout/` | GET | `PatientLogout` | ❌ | Patient logout |
| `/booking/` | GET, POST | `BookedAppointment` | ✅ | View/book appointments |
| `/deletebooking/<aid>/` | GET | `BookedAppointment` | ✅ | Cancel appointment |
| `/bindvaccines/` | GET | `load_vaccinebyhospital` | ❌ | AJAX: vaccines by hospital |
| `/changepass/` | GET, POST | `ChangeAuthentication` | ✅ | Change password |
| `/viewvaccines/` | GET | `ViewVaccineList` | ✅ | Browse all vaccines |
| `/loadvaccinedata/` | GET | `loadVaccines` | ❌ | AJAX: vaccine table filter |

### `receptionistapp` — Prefix `/receptionist/`

| URL | Methods | View | Auth | Purpose |
|-----|---------|------|------|---------|
| `/receptionist/` | GET | `Home` | ✅ | Receptionist dashboard |
| `/receptionist/login/` | GET, POST | `ReceptionistLogin` | ❌ | Receptionist login |
| `/receptionist/logout/` | GET | `Logout` | ❌ | Receptionist logout |
| `/receptionist/booking/` | GET | `ManagePatient` | ✅ | All appointments list |
| `/receptionist/showbooking/<id>/` | GET, POST | `ManagePatient` | ✅ | Appointment detail + check-in/out |

**Total: 43 endpoints**

---

## 6. Core Workflows

### Workflow 1 — Patient Registration

| Step | Action | Endpoint |
|------|--------|----------|
| 1 | Patient opens register page | `GET /register/` |
| 2 | Fills: name, address, city, area, contactNo, password | — |
| 3 | Submits form | `POST /register/` |
| 4a | Duplicate contactNo → error, redirect | — |
| 4b | Unique → save `Patienttbl`, redirect to login | — |

---

### Workflow 2 — Patient Login

| Step | Action | Endpoint |
|------|--------|----------|
| 1 | Patient submits `contactno` + `password` | `POST /login/` |
| 2 | Backend checks `Patienttbl` by `contactNo` | — |
| 3 | Sets `session['CName']` and `session['Cid']`, redirects to `/` | — |

---

### Workflow 3 — Book Vaccine Appointment

| Step | Action | Endpoint |
|------|--------|----------|
| 1 | Patient opens booking page | `GET /booking/` |
| 2 | Selects hospital → vaccines load via AJAX | `GET /bindvaccines/?h_id=<id>` |
| 3 | Fills: child name, hospital, vaccine, date | — |
| 4 | Submits → creates `Appointmenttbl` with `active=0` | `POST /booking/` |

---

### Workflow 4 — Admin Platform Setup

| Step | Action | Endpoint |
|------|--------|----------|
| 1 | Admin logs in | `POST /admin/login/` |
| 2 | Creates cities | `POST /admin/city/` |
| 3 | Creates areas under cities | `POST /admin/addarea/` |
| 4 | Registers hospitals (with image) | `POST /admin/addhospitals/` |

---

### Workflow 5 — Hospital Catalogue Setup

| Step | Action | Endpoint |
|------|--------|----------|
| 1 | Hospital logs in with `contactNo` + `password` | `POST /hospital/login/` |
| 2 | Adds vaccines to catalogue | `POST /hospital/vaccine/` |
| 3 | Registers receptionist staff | `POST /hospital/register/` |
| 4 | Views today's or past appointments | `GET /hospital/showbooking/` |

---

### Workflow 6 — Receptionist Check-In / Check-Out

| Step | Action | Endpoint |
|------|--------|----------|
| 1 | Receptionist logs in | `POST /receptionist/login/` |
| 2 | Views hospital's appointment list | `GET /receptionist/booking/` |
| 3 | Opens an appointment | `GET /receptionist/showbooking/<id>/` |
| 4 | **Check-In:** Submits `rfidno` → `active 0→1`, `indt = now()` | `POST /receptionist/showbooking/<id>/` |
| 5 | **Check-Out:** Submits again → `active 1→2`, `outdt = now()` | `POST /receptionist/showbooking/<id>/` |

---

### Workflow 7 — Cancel Appointment (Patient)

| Step | Action | Endpoint |
|------|--------|----------|
| 1 | Patient views booking list | `GET /booking/` |
| 2 | Clicks Cancel (only visible when `active=0`) | `GET /deletebooking/<aid>/` |
| 3 | Record deleted from `Appointmenttbl` | — |

---

## 7. Frontend Structure

### Technology

| Technology | Role |
|-----------|------|
| Django Templates | All pages — server-side rendered |
| Bootstrap 5 | Layout, forms, tables, badges, buttons |
| jQuery | AJAX for dependent dropdowns |
| Font Awesome | Icons |
| Chart.js + SimpleChart.js | Admin dashboard charts (static data) |
| Google Fonts | `PT Sans` (admin), `Kumbh Sans` (patient) |
| Light/Dark Mode Toggle | Patient portal only (`theme-change.js`) |

### Template Architecture

**Admin / Hospital / Receptionist portals** — each uses a `base.html` with:
- Fixed left sidebar navigation
- Sticky top header (shows `session.CName`, Logout)
- `{% block contents %}` for page-specific content

**Patient portal** — standalone pages with:
- Fixed top navbar (via `{% include 'patientapp/menu.html' %}`)
- Footer (via `{% include 'patientapp/footer.html' %}`)
- Session-aware nav links

### AJAX Interactions

| Trigger | Endpoint Called | Effect |
|---------|----------------|--------|
| City dropdown change (hospital reg, area, register) | `GET /admin/bindareas/?city_id=X` | Area dropdown populated |
| Hospital dropdown change (booking form) | `GET /bindvaccines/?h_id=X` | Vaccine dropdown populated |
| Hospital dropdown change (vaccine list) | `GET /loadvaccinedata/?h_id=X` | Vaccine table rows reloaded |

### Pages Summary

| Portal | Pages | URL Prefix |
|--------|-------|------------|
| Admin | 6 | `/admin/` |
| Hospital | 6 | `/hospital/` |
| Patient | 9 | `/` |
| Receptionist | 4 | `/receptionist/` |
| **Total** | **25** | — |

### Navigation Map

```
Patient
  /  → /about/ · /contact/ · /login/ → /register/
  [Logged in] → /booking/ · /viewvaccines/ · /changepass/ · /logout/

Admin
  /admin/login/ → /admin/ → City · Area · Hospitals · New Admin · Logout

Hospital
  /hospital/login/ → /hospital/ → Receptionist · Vaccine · ShowBooking · PastBooking · Logout

Receptionist
  /receptionist/login/ → /receptionist/ → /receptionist/booking/ → /receptionist/showbooking/<id>/
```

---

## Appendix — File Index

| File | Description |
|------|-------------|
| `kiddovax/settings.py` | Project settings |
| `kiddovax/urls.py` | Root URL routing |
| `adminapp/models.py` | `Admintbl`, `City`, `Area` |
| `adminapp/views.py` | Admin CRUD views |
| `hospitalapp/models.py` | `Hospitaltbl`, `Vaccinetbl`, `Receptionisttbl` |
| `hospitalapp/views.py` | Hospital CRUD, appointment views |
| `patientapp/models.py` | `Patienttbl`, `Appointmenttbl` |
| `patientapp/views.py` | Patient login, booking, password change |
| `receptionistapp/views.py` | Check-in / check-out logic |
| `db.sqlite3` | SQLite database |
| `static/` | All CSS, JS, images, uploaded files |

---

*End of documentation.*
