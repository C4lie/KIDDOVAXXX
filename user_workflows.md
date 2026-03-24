# KiddoVax — User Workflows (Code-Inferred)

> Generated: 2026-03-24  
> All workflows are strictly derived from `models.py`, `views.py`, and `urls.py` source code.

---

## Actors

| Actor | Auth Table | Session Keys Set |
|-------|-----------|------------------|
| **Admin** | `Admintbl` | `CName` (username) |
| **Hospital / Doctor** | `Hospitaltbl` | `CName` (dcrname), `Cid` (hospital id) |
| **Receptionist** | `Receptionisttbl` | `CName` (name), `Cid` (receptionist id) |
| **Patient** | `Patienttbl` | `CName` (name), `Cid` (patient id) |

---

## Workflow 1 — Patient Self-Registration

**Trigger:** A new patient visits the platform and clicks Register.

### Steps

| Step | Action | Endpoint | Model |
|------|--------|----------|-------|
| 1 | Patient opens the registration page | `GET /register/` | — |
| 2 | Page renders with city dropdown populated from DB | `GET /register/` | `City` |
| 3 | Patient selects a city; browser calls area loader | `GET /bindvaccines/` → actually `load_vaccinebyhospital` — _area binding is done via `/bindareas/`_ | `Area` |
| 4 | Patient fills: `name`, `address`, `cityId`, `areaId`, `contactNo`, `password` | — | — |
| 5 | Patient submits the form | `POST /register/` | `Patienttbl` |
| 6 | Backend checks if `contactNo` already exists in `Patienttbl` | — | `Patienttbl` |
| 7a | **If duplicate:** flash message "Contact Number is already taken", redirect to `/register/` | — | — |
| 7b | **If unique:** save new `Patienttbl` record, redirect to `/login/` | — | `Patienttbl` |

**Models Involved:** `City`, `Area`, `Patienttbl`  
**Endpoints Involved:** `GET /register/`, `POST /register/`  
**Outcome:** New patient account created; patient redirected to login.

---

## Workflow 2 — Patient Login

**Trigger:** Patient navigates to `/login/` and submits credentials.

### Steps

| Step | Action | Endpoint | Model |
|------|--------|----------|-------|
| 1 | Patient opens login page | `GET /login/` | — |
| 2 | Patient enters `contactno` and `password` | — | — |
| 3 | Backend fetches `Patienttbl` record by `contactNo` | `POST /login/` | `Patienttbl` |
| 4a | **If contactNo not found:** error "Invalid Contact Number" | — | — |
| 4b | **If contactNo found but password wrong:** error "Invalid Password" | — | — |
| 4c | **If both match:** set `session['CName'] = name`, `session['Cid'] = id`, redirect to `/` | — | `Patienttbl` |

**Models Involved:** `Patienttbl`  
**Endpoints Involved:** `GET /login/`, `POST /login/`  
**Outcome:** Patient session established; patient lands on the home page.

---

## Workflow 3 — Patient Books a Vaccine Appointment

**Trigger:** Logged-in patient navigates to `/booking/` to schedule a vaccination.

### Steps

| Step | Action | Endpoint | Model |
|------|--------|----------|-------|
| 1 | Patient opens booking page | `GET /booking/` | `Hospitaltbl`, `Appointmenttbl` |
| 2 | Page shows all hospitals and patient's existing appointments | — | `Hospitaltbl`, `Appointmenttbl` |
| 3 | Patient selects a hospital; browser fetches vaccines for that hospital | `GET /bindvaccines/?h_id=<id>` | `Vaccinetbl` |
| 4 | Patient fills: `childname`, `hospitalid`, `vaccineid`, `aptdate` | — | — |
| 5 | Patient submits the form | `POST /booking/` | `Appointmenttbl` |
| 6 | Backend saves `Appointmenttbl` with `active = 0` (pending), `patientid` from session | — | `Appointmenttbl` |
| 7 | Flash message "Your appointment is successfully booked!", redirect to `/booking/` | — | — |

**Models Involved:** `Hospitaltbl`, `Vaccinetbl`, `Patienttbl`, `Appointmenttbl`  
**Endpoints Involved:** `GET /booking/`, `GET /bindvaccines/`, `POST /booking/`  
**Outcome:** `Appointmenttbl` record created with `active=0`; patient sees it in their booking list.

---

## Workflow 4 — Patient Cancels an Appointment

**Trigger:** Patient clicks Delete on a pending appointment in their booking list.

### Steps

| Step | Action | Endpoint | Model |
|------|--------|----------|-------|
| 1 | Patient is on the booking page | `GET /booking/` | `Appointmenttbl` |
| 2 | Patient clicks Delete for an appointment | `GET /deletebooking/<aid>/` | `Appointmenttbl` |
| 3 | Backend fetches `Appointmenttbl` by PK and calls `.delete()` | — | `Appointmenttbl` |
| 4 | Flash message "Appointment Deleted Success!", redirect to `/booking/` | — | — |

**Models Involved:** `Appointmenttbl`  
**Endpoints Involved:** `GET /deletebooking/<aid>/`  
**Outcome:** Appointment record permanently removed from DB.

---

## Workflow 5 — Patient Changes Password

**Trigger:** Logged-in patient navigates to `/changepass/`.

### Steps

| Step | Action | Endpoint | Model |
|------|--------|----------|-------|
| 1 | Patient opens change password page | `GET /changepass/` | — |
| 2 | Patient submits `cpass` (current), `password` (new), `cfpass` (confirm new) | `POST /changepass/` | `Patienttbl` |
| 3a | **If current password doesn't match DB:** "Current Password is Not Valid!" | — | — |
| 3b | **If new and confirm don't match:** mismatch warning | — | — |
| 3c | **If all valid:** update `Patienttbl.password`, "Password changed successfully on next login!" | — | `Patienttbl` |

**Models Involved:** `Patienttbl`  
**Endpoints Involved:** `GET /changepass/`, `POST /changepass/`  
**Outcome:** Patient's plain-text password updated directly in `Patienttbl`.

---

## Workflow 6 — Admin Logs In and Sets Up the Platform

**Trigger:** Admin visits `/admin/login/` to configure the platform (cities, areas, hospitals).

### Steps

| Step | Action | Endpoint | Model |
|------|--------|----------|-------|
| 1 | Admin logs in with `username` + `password` | `POST /admin/login/` | `Admintbl` |
| 2 | Session `CName` set; redirected to `/admin/` | — | — |
| 3 | Admin adds a City | `POST /admin/city/` | `City` |
| 4 | Admin adds an Area under that City | `POST /admin/addarea/` | `Area` |
| 5 | Admin registers a Hospital (with city, area, doctor info, image) | `POST /admin/addhospitals/` | `Hospitaltbl` |
| 6 | Admin can edit or delete any city, area, or hospital at any time | `GET /admin/editcity/<id>/`, `GET /admin/deletehospital/<pid>/`, etc. | `City`, `Area`, `Hospitaltbl` |

**Models Involved:** `Admintbl`, `City`, `Area`, `Hospitaltbl`  
**Endpoints Involved:** `/admin/login/`, `/admin/city/`, `/admin/addarea/`, `/admin/addhospitals/` + their edit/delete variants  
**Outcome:** Platform is populated with location master data and registered hospitals; hospitals can now log in.

---

## Workflow 7 — Hospital Logs In and Manages Its Catalogue

**Trigger:** Hospital (doctor) logs in at `/hospital/login/` using `contactNo` and `password`.

### Steps

| Step | Action | Endpoint | Model |
|------|--------|----------|-------|
| 1 | Hospital logs in | `POST /hospital/login/` | `Hospitaltbl` |
| 2 | Session `CName` (dcrname) and `Cid` (hospital id) set; redirected to `/hospital/` | — | — |
| 3 | Hospital adds vaccines to its catalogue | `POST /hospital/vaccine/` | `Vaccinetbl` |
| 4 | Hospital registers receptionist staff (with image, city, area) | `POST /hospital/register/` | `Receptionisttbl` |
| 5 | Hospital can edit / delete vaccines and receptionists | `/hospital/editvaccine/<id>/`, `/hospital/deletevaccine/<vid>/`, etc. | `Vaccinetbl`, `Receptionisttbl` |
| 6 | Hospital views today's appointments | `GET /hospital/showbooking/` | `Appointmenttbl` |
| 7 | Hospital views past appointments | `GET /hospital/showpastbooking/` | `Appointmenttbl` |

**Models Involved:** `Hospitaltbl`, `Vaccinetbl`, `Receptionisttbl`, `Appointmenttbl`  
**Endpoints Involved:** `/hospital/login/`, `/hospital/vaccine/`, `/hospital/register/`, `/hospital/showbooking/`, `/hospital/showpastbooking/`  
**Outcome:** Hospital's vaccine catalogue and receptionist staff are set up; appointments are visible to the hospital.

---

## Workflow 8 — Receptionist Manages Appointment Check-In / Check-Out

**Trigger:** Receptionist logs in at `/receptionist/login/` and a patient arrives for their appointment.

### Steps

| Step | Action | Endpoint | Model |
|------|--------|----------|-------|
| 1 | Receptionist logs in with `contactNo` + `password` | `POST /receptionist/login/` | `Receptionisttbl` |
| 2 | Session `CName` (name) and `Cid` (receptionist id) set; redirected to `/receptionist/` | — | — |
| 3 | Receptionist views all appointments for their hospital | `GET /receptionist/booking/` | `Receptionisttbl`, `Appointmenttbl` |
| 4 | Receptionist selects an appointment to manage | `GET /receptionist/showbooking/<id>/` | `Appointmenttbl` |
| 5 | **Check-In (active = 0 → 1):** Receptionist submits `rfidno`; backend records `rfidno`, sets `indt = now()`, `active = 1` | `POST /receptionist/showbooking/<id>/` | `Appointmenttbl` |
| 6 | **Check-Out (active = 1 → 2):** Receptionist submits again; backend sets `outdt = now()`, `active = 2` | `POST /receptionist/showbooking/<id>/` | `Appointmenttbl` |
| 7 | Redirect back to `/receptionist/booking/` after each action | — | — |

**Appointment Status State Machine:**

```
active = 0  →  Booked (pending)
active = 1  →  Checked In  (indt recorded, rfidno assigned)
active = 2  →  Checked Out (outdt recorded)
```

**Models Involved:** `Receptionisttbl`, `Appointmenttbl`  
**Endpoints Involved:** `/receptionist/login/`, `/receptionist/booking/`, `GET /receptionist/showbooking/<id>/`, `POST /receptionist/showbooking/<id>/`  
**Outcome:** Patient's vaccine visit is fully tracked — from booking through arrival (RFID scan) to departure.

---

## End-to-End Platform Flow

```
Admin
  └─ Creates City / Area / Hospital
          │
Hospital
  └─ Logs In → Adds Vaccines → Registers Receptionists
          │
Patient
  └─ Registers → Logs In → Books Appointment (active=0)
          │
Receptionist
  └─ Logs In → Views Appointments
       ├─ Check-In Patient  → active=0 ➜ 1  (RFID + indt)
       └─ Check-Out Patient → active=1 ➜ 2  (outdt)
```

---

*End of workflow analysis.*
