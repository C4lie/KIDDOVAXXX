# KiddoVax — Django Endpoint Analysis

> Generated: 2026-03-24  
> Architecture: Template-based Django views (no REST Framework / no JSON APIs)  
> All responses render HTML templates unless noted otherwise.

---

## Root URL Routing (`kiddovax/urls.py`)

| Prefix | Included App URLs |
|--------|-------------------|
| `/` | `patientapp.urls` |
| `/receptionist/` | `receptionistapp.urls` |
| `/hospital/` | `hospitalapp.urls` |
| `/admin/` | `adminapp.urls` |

---

## 🔵 App: `adminapp` — Prefix: `/admin/`

---

### Endpoint 1 — Admin Home

| Property | Detail |
|----------|--------|
| **URL** | `/admin/` |
| **Method** | GET |
| **View** | `Home` (function-based) |
| **Auth Required** | Yes — session key `CName` must exist |
| **Input** | None |
| **Output** | Renders `adminapp/home.html` |
| **Purpose** | Admin dashboard home page. Redirects to login if not authenticated. |

---

### Endpoint 2 — Admin Login

| Property | Detail |
|----------|--------|
| **URL** | `/admin/login/` |
| **Method** | GET, POST |
| **View** | `AdminLogin` (class-based) |
| **Auth Required** | No |
| **Input (POST)** | `username`, `password` |
| **Output** | GET: Renders `adminapp/login.html` · POST (success): Redirects to `/admin/` and sets session `CName` · POST (failure): Re-renders login with error message |
| **Purpose** | Authenticates admin using `Admintbl` (custom, not Django auth). Sets session on success. |

---

### Endpoint 3 — Admin Logout

| Property | Detail |
|----------|--------|
| **URL** | `/admin/logout/` |
| **Method** | GET |
| **View** | `Logout` (function-based) |
| **Auth Required** | No |
| **Input** | None |
| **Output** | Clears all sessions, renders `adminapp/login.html` |
| **Purpose** | Logs out admin and destroys all server-side sessions. |

---

### Endpoint 4 — Create Admin

| Property | Detail |
|----------|--------|
| **URL** | `/admin/newadmin/` |
| **Method** | GET, POST |
| **View** | `AdminCreation` (class-based) |
| **Auth Required** | Yes — session `CName` |
| **Input (POST)** | `username`, `password` (via `AdminForm`) |
| **Output** | Renders `adminapp/createadmin.html` with form and list of all admins |
| **Purpose** | Allows a logged-in admin to create new admin accounts in `Admintbl`. |

---

### Endpoint 5 — Manage Cities (List / Add / Edit / Delete)

| Property | Detail |
|----------|--------|
| **URL** | `/admin/city/` |
| **Method** | GET, POST |
| **View** | `ManageCity` (class-based) |
| **Auth Required** | Yes — session `CName` |
| **Input (POST)** | `cityName` |
| **Output** | GET: Renders `adminapp/city.html` with city list and form · POST: Saves city, redirects to `/admin/city/` |
| **Purpose** | Add or list cities. On POST, checks for duplicates before saving. |

| Property | Detail |
|----------|--------|
| **URL** | `/admin/editcity/<int:id>/` |
| **Method** | GET, POST |
| **View** | `ManageCity` (same class, `id` param) |
| **Input (GET)** | `id` (city PK in URL) |
| **Input (POST)** | `cityName` |
| **Output** | GET: Renders form pre-filled with city data · POST: Updates and redirects |
| **Purpose** | Edit an existing city record by PK. |

| Property | Detail |
|----------|--------|
| **URL** | `/admin/deletecity/<int:cityid>/` |
| **Method** | GET |
| **View** | `ManageCity` (same class, `cityid` param) |
| **Input** | `cityid` (in URL) |
| **Output** | Deletes city, redirects to `/admin/city/` |
| **Purpose** | Delete a city record by PK. |

---

### Endpoint 6 — Load Areas by City (AJAX helper)

| Property | Detail |
|----------|--------|
| **URL** | `/admin/bindareas/` |
| **Method** | GET |
| **View** | `load_areasbyCity` (function-based) |
| **Auth Required** | No |
| **Input (GET)** | `city_id` (query param) |
| **Output** | Renders `adminapp/citytoarea.html` with filtered area list |
| **Purpose** | AJAX/partial template endpoint — returns areas filtered by selected city for dependent dropdowns. |

---

### Endpoint 7 — Manage Areas (List / Add / Edit / Delete)

| Property | Detail |
|----------|--------|
| **URL** | `/admin/addarea/` |
| **Method** | GET, POST |
| **View** | `ManageArea` (class-based) |
| **Auth Required** | Yes — session `CName` |
| **Input (POST)** | `cityId`, `areaName` (via `AreaForm`) |
| **Output** | Renders `adminapp/area.html` with city dropdown and area list |
| **Purpose** | Add or list areas under a city. |

| Property | Detail |
|----------|--------|
| **URL** | `/admin/editarea/<int:id>/` |
| **Method** | GET, POST |
| **View** | `ManageArea` (same class, `id` param) |
| **Input** | `id` in URL; POST: `cityId`, `areaName` |
| **Output** | GET: Pre-filled form · POST: Updates record, redirects |
| **Purpose** | Edit an existing area. |

| Property | Detail |
|----------|--------|
| **URL** | `/admin/deletearea/<int:areaid>/` |
| **Method** | GET |
| **View** | `ManageArea` (same class, `areaid` param) |
| **Input** | `areaid` in URL |
| **Output** | Deletes area, redirects to `/admin/addarea/` |
| **Purpose** | Delete an area record by PK. |

---

### Endpoint 8 — Manage Hospitals (List / Add / Edit / Delete)

| Property | Detail |
|----------|--------|
| **URL** | `/admin/addhospitals/` |
| **Method** | GET, POST |
| **View** | `ManageHospitals` (class-based) |
| **Auth Required** | Yes — session `CName` |
| **Input (POST)** | `title`, `dcrname`, `address`, `cityId`, `areaId`, `contactNo`, `password`, `img` (file) — via `HospitalForm` |
| **Output** | GET: Renders `adminapp/hospitalreg.html` with hospital list · POST: Creates hospital, redirects |
| **Purpose** | Admin registers a new hospital on the platform. |

| Property | Detail |
|----------|--------|
| **URL** | `/admin/edithospital/<int:id>/` |
| **Method** | GET, POST |
| **View** | `ManageHospitals` (same class, `id` param) |
| **Input** | `id` in URL; POST: same hospital fields |
| **Output** | GET: Pre-filled form with existing hospital data · POST: Updates and redirects |
| **Purpose** | Edit an existing hospital record. |

| Property | Detail |
|----------|--------|
| **URL** | `/admin/deletehospital/<int:pid>/` |
| **Method** | GET |
| **View** | `ManageHospitals` (same class, `pid` param) |
| **Input** | `pid` in URL |
| **Output** | Deletes hospital, redirects to `/admin/addhospitals/` |
| **Purpose** | Delete a hospital record by PK. |

---

## 🟢 App: `hospitalapp` — Prefix: `/hospital/`

---

### Endpoint 9 — Hospital Home

| Property | Detail |
|----------|--------|
| **URL** | `/hospital/` |
| **Method** | GET |
| **View** | `Home` (function-based) |
| **Auth Required** | Yes — session `CName` |
| **Input** | None |
| **Output** | Renders `hospitalapp/home.html` |
| **Purpose** | Hospital dashboard home. Redirects to login if not authenticated. |

---

### Endpoint 10 — Hospital Login

| Property | Detail |
|----------|--------|
| **URL** | `/hospital/login/` |
| **Method** | GET, POST |
| **View** | `HospitalLogin` (class-based) |
| **Auth Required** | No |
| **Input (POST)** | `contact`, `password` |
| **Output** | GET: Renders `hospitalapp/login.html` · POST (success): Sets session `CName` (doctor name), `Cid` (hospital ID), redirects to `/hospital/` · POST (failure): Error message |
| **Purpose** | Authenticates hospital (doctor) using `Hospitaltbl.contactNo` and `password`. |

---

### Endpoint 11 — Hospital Logout

| Property | Detail |
|----------|--------|
| **URL** | `/hospital/logout/` |
| **Method** | GET |
| **View** | `Logout` (function-based) |
| **Auth Required** | No |
| **Input** | None |
| **Output** | Clears all sessions, renders `hospitalapp/login.html` |
| **Purpose** | Logs out hospital user and destroys all sessions. |

---

### Endpoint 12 — Load Areas by City (AJAX helper)

| Property | Detail |
|----------|--------|
| **URL** | `/hospital/bindareas/` |
| **Method** | GET |
| **View** | `load_areasbyCity` (function-based) |
| **Auth Required** | No |
| **Input (GET)** | `city_id` (query param) |
| **Output** | Renders `adminapp/citytoarea.html` with filtered area list |
| **Purpose** | AJAX/partial template — fetches areas for selected city in receptionist registration form. |

---

### Endpoint 13 — Manage Receptionists (List / Add / Edit / Delete)

| Property | Detail |
|----------|--------|
| **URL** | `/hospital/register/` |
| **Method** | GET, POST |
| **View** | `ReceptionistRegister` (class-based) |
| **Auth Required** | Yes — session `CName`, `Cid` |
| **Input (POST)** | `name`, `address`, `gender`, `contactNo`, `password`, `staffimg` (file), `doj`, `areaId`, `cityId` |
| **Output** | GET: Renders `hospitalapp/receptionist.html` · POST: Creates receptionist linked to logged-in hospital, redirects |
| **Purpose** | Hospital registers new receptionist staff. Hospital ID taken from session. |

| Property | Detail |
|----------|--------|
| **URL** | `/hospital/editreceptionist/<int:id>/` |
| **Method** | GET, POST |
| **View** | `ReceptionistRegister` (same class, `id` param) |
| **Input** | `id` in URL; POST: same receptionist fields |
| **Output** | GET: Pre-filled form · POST: Updates and redirects |
| **Purpose** | Edit an existing receptionist record. |

| Property | Detail |
|----------|--------|
| **URL** | `/hospital/deletereceptionist/<int:pid>/` |
| **Method** | GET |
| **View** | `ReceptionistRegister` (same class, `pid` param) |
| **Input** | `pid` in URL |
| **Output** | Deletes receptionist, redirects to `/hospital/register/` |
| **Purpose** | Delete a receptionist record by PK. |

---

### Endpoint 14 — Manage Vaccines (List / Add / Edit / Delete)

| Property | Detail |
|----------|--------|
| **URL** | `/hospital/vaccine/` |
| **Method** | GET, POST |
| **View** | `ManageVaccine` (class-based) |
| **Auth Required** | Yes — session `CName`, `Cid` |
| **Input (POST)** | `vaccineName`, `vaccineDescr`, `price` |
| **Output** | GET: Renders `hospitalapp/managevaccine.html` with vaccines for this hospital · POST: Creates vaccine, redirects |
| **Purpose** | Hospital adds vaccines to its catalogue. Checks for duplicate vaccine names before saving. |

| Property | Detail |
|----------|--------|
| **URL** | `/hospital/editvaccine/<int:id>/` |
| **Method** | GET, POST |
| **View** | `ManageVaccine` (same class, `id` param) |
| **Input** | `id` in URL; POST: `vaccineName`, `vaccineDescr`, `price` |
| **Output** | GET: Pre-filled form · POST: Updates and redirects |
| **Purpose** | Edit an existing vaccine record. |

| Property | Detail |
|----------|--------|
| **URL** | `/hospital/deletevaccine/<int:vid>/` |
| **Method** | GET |
| **View** | `ManageVaccine` (same class, `vid` param) |
| **Input** | `vid` in URL |
| **Output** | Deletes vaccine, redirects to `/hospital/vaccine/` |
| **Purpose** | Delete a vaccine record by PK. |

---

### Endpoint 15 — Show Today's Appointments

| Property | Detail |
|----------|--------|
| **URL** | `/hospital/showbooking/` |
| **Method** | GET |
| **View** | `ShowAppointments` (class-based) |
| **Auth Required** | Yes — session `CName`, `Cid` |
| **Input** | None (filters by session hospital ID and today's date) |
| **Output** | Renders `hospitalapp/showappointment.html` with today's appointments |
| **Purpose** | Hospital views all vaccine appointments scheduled for today. |

---

### Endpoint 16 — Show Past Appointments

| Property | Detail |
|----------|--------|
| **URL** | `/hospital/showpastbooking/` |
| **Method** | GET |
| **View** | `ShowPastAppointments` (class-based) |
| **Auth Required** | Yes — session `CName`, `Cid` |
| **Input** | None (filters by session hospital ID and date before today) |
| **Output** | Renders `hospitalapp/showappointment.html` with past appointments |
| **Purpose** | Hospital views historical vaccine appointments (all dates before today). |

---

## 🟡 App: `patientapp` — Prefix: `/` (root)

---

### Endpoint 17 — Home Page

| Property | Detail |
|----------|--------|
| **URL** | `/` |
| **Method** | GET |
| **View** | `Home` (function-based) |
| **Auth Required** | No |
| **Input** | None |
| **Output** | Renders `patientapp/home.html` |
| **Purpose** | Public landing / home page for the platform. |

---

### Endpoint 18 — About Page

| Property | Detail |
|----------|--------|
| **URL** | `/about/` |
| **Method** | GET |
| **View** | `About` (function-based) |
| **Auth Required** | No |
| **Input** | None |
| **Output** | Renders `patientapp/about.html` |
| **Purpose** | Static informational about page. |

---

### Endpoint 19 — Contact Page

| Property | Detail |
|----------|--------|
| **URL** | `/contact/` |
| **Method** | GET |
| **View** | `Contact` (function-based) |
| **Auth Required** | No |
| **Input** | None |
| **Output** | Renders `patientapp/contact.html` |
| **Purpose** | Static contact page. |

---

### Endpoint 20 — Patient Login

| Property | Detail |
|----------|--------|
| **URL** | `/login/` |
| **Method** | GET, POST |
| **View** | `PatientLogin` (class-based) |
| **Auth Required** | No |
| **Input (POST)** | `contactno`, `password` |
| **Output** | GET: `patientapp/login.html` · POST (success): Sets session `CName` (name), `Cid` (patient ID), redirects to `/` · POST (failure): Error message |
| **Purpose** | Authenticates patient using `Patienttbl.contactNo` and `password`. |

---

### Endpoint 21 — Patient Registration

| Property | Detail |
|----------|--------|
| **URL** | `/register/` |
| **Method** | GET, POST |
| **View** | `PatientRegistration` (class-based) |
| **Auth Required** | No |
| **Input (POST)** | `name`, `address`, `cityId`, `areaId`, `contactNo`, `password` (via `PatientForm`) |
| **Output** | GET: Renders `patientapp/register.html` with city dropdown · POST (success): Saves and redirects to `/login/` · POST (duplicate contact): Error message |
| **Purpose** | New patient self-registration. Checks for duplicate contact number before saving. |

---

### Endpoint 22 — Patient Logout

| Property | Detail |
|----------|--------|
| **URL** | `/logout/` |
| **Method** | GET |
| **View** | `PatientLogout` (class-based) |
| **Auth Required** | No |
| **Input** | None |
| **Output** | Clears all sessions, renders `patientapp/home.html` |
| **Purpose** | Logs out current patient and destroys all sessions. |

---

### Endpoint 23 — Book / View / Delete Appointment

| Property | Detail |
|----------|--------|
| **URL** | `/booking/` |
| **Method** | GET, POST |
| **View** | `BookedAppointment` (class-based) |
| **Auth Required** | Yes — session `CName`, `Cid` |
| **Input (POST)** | `childname`, `hospitalid`, `vaccineid`, `aptdate` |
| **Output** | GET: Renders `patientapp/bookvaccine.html` with hospital list and patient's appointments · POST (success): Books appointment (sets `active=0`), redirects |
| **Purpose** | Patient books a vaccine appointment for their child by selecting hospital, vaccine, and date. |

| Property | Detail |
|----------|--------|
| **URL** | `/deletebooking/<int:aid>/` |
| **Method** | GET |
| **View** | `BookedAppointment` (same class, `aid` param) |
| **Input** | `aid` (appointment PK in URL) |
| **Output** | Deletes appointment, redirects to `/booking/` |
| **Purpose** | Patient cancels/deletes a previously booked appointment. |

---

### Endpoint 24 — Load Vaccines by Hospital (AJAX helper)

| Property | Detail |
|----------|--------|
| **URL** | `/bindvaccines/` |
| **Method** | GET |
| **View** | `load_vaccinebyhospital` (function-based) |
| **Auth Required** | No |
| **Input (GET)** | `h_id` (query param — hospital ID) |
| **Output** | Renders `patientapp/hospitaltovaccine.html` with vaccines for selected hospital |
| **Purpose** | AJAX/partial template — populates vaccine dropdown when a hospital is selected during booking. |

---

### Endpoint 25 — Change Password

| Property | Detail |
|----------|--------|
| **URL** | `/changepass/` |
| **Method** | GET, POST |
| **View** | `ChangeAuthentication` (class-based) |
| **Auth Required** | Yes — session `CName`, `Cid` |
| **Input (POST)** | `cpass` (current password), `password` (new password), `cfpass` (confirm new password) |
| **Output** | GET: Renders `patientapp/changepassword.html` · POST (success): Updates password in DB, shows confirmation · POST (failure): Error messages for wrong current pass or mismatch |
| **Purpose** | Allows logged-in patient to change their account password. |

---

### Endpoint 26 — View All Vaccines (browseable list)

| Property | Detail |
|----------|--------|
| **URL** | `/viewvaccines/` |
| **Method** | GET |
| **View** | `ViewVaccineList` (class-based) |
| **Auth Required** | Yes — session `CName` |
| **Input** | None |
| **Output** | Renders `patientapp/showvaccines.html` with all vaccines and hospitals |
| **Purpose** | Patient browses all available vaccines across all hospitals. |

---

### Endpoint 27 — Load Vaccine Records (AJAX filter)

| Property | Detail |
|----------|--------|
| **URL** | `/loadvaccinedata/` |
| **Method** | GET |
| **View** | `loadVaccines` (function-based) |
| **Auth Required** | No |
| **Input (GET)** | `h_id` (query param — hospital ID; `0` or negative returns all vaccines) |
| **Output** | Renders `patientapp/loadvaccinerecord.html` with filtered or all vaccine records |
| **Purpose** | AJAX/partial template — filters vaccine list by hospital on the View Vaccines page. |

---

## 🔴 App: `receptionistapp` — Prefix: `/receptionist/`

---

### Endpoint 28 — Receptionist Home

| Property | Detail |
|----------|--------|
| **URL** | `/receptionist/` |
| **Method** | GET |
| **View** | `Home` (function-based) |
| **Auth Required** | Yes — session `CName` |
| **Input** | None |
| **Output** | Renders `receptionistapp/home.html` |
| **Purpose** | Receptionist dashboard home. Redirects to login if not authenticated. |

---

### Endpoint 29 — Receptionist Login

| Property | Detail |
|----------|--------|
| **URL** | `/receptionist/login/` |
| **Method** | GET, POST |
| **View** | `ReceptionistLogin` (class-based) |
| **Auth Required** | No |
| **Input (POST)** | `contact`, `password` |
| **Output** | GET: `receptionistapp/login.html` · POST (success): Sets session `CName` (name), `Cid` (receptionist ID), redirects to `/receptionist/` · POST (failure): Error message |
| **Purpose** | Authenticates receptionist using `Receptionisttbl.contactNo` and `password`. |

---

### Endpoint 30 — Receptionist Logout

| Property | Detail |
|----------|--------|
| **URL** | `/receptionist/logout/` |
| **Method** | GET |
| **View** | `Logout` (function-based) |
| **Auth Required** | No |
| **Input** | None |
| **Output** | Clears all sessions, renders `receptionistapp/login.html` |
| **Purpose** | Logs out receptionist and destroys all sessions. |

---

### Endpoint 31 — Manage Patient Appointments (View / Update Status)

| Property | Detail |
|----------|--------|
| **URL** | `/receptionist/booking/` |
| **Method** | GET |
| **View** | `ManagePatient` (class-based) |
| **Auth Required** | Yes — session `CName`, `Cid` |
| **Input** | None (filters by hospital linked to logged-in receptionist) |
| **Output** | Renders `receptionistapp/booking.html` with all appointments for the receptionist's hospital |
| **Purpose** | Receptionist views all appointments for their hospital. |

| Property | Detail |
|----------|--------|
| **URL** | `/receptionist/showbooking/<int:id>/` |
| **Method** | GET, POST |
| **View** | `ManagePatient` (same class, `id` param) |
| **Auth Required** | Yes — session |
| **Input (GET)** | `id` (appointment PK in URL) |
| **Input (POST)** | `rfidno` (RFID number for check-in) |
| **Output** | GET: Renders `receptionistapp/showdata.html` with single appointment detail · POST: Updates appointment status (`active` field: 0→1 = check-in with RFID + `indt`, 1→2 = check-out with `outdt`), redirects to booking list |
| **Purpose** | Receptionist manages vaccine appointment status — checks patient in (records RFID + arrival time) and checks out (records departure time). |

---

## Summary Table

| # | URL | Method(s) | App | Auth |
|---|-----|-----------|-----|------|
| 1 | `/admin/` | GET | adminapp | ✅ Session |
| 2 | `/admin/login/` | GET, POST | adminapp | ❌ Public |
| 3 | `/admin/logout/` | GET | adminapp | ❌ Public |
| 4 | `/admin/newadmin/` | GET, POST | adminapp | ✅ Session |
| 5 | `/admin/city/` | GET, POST | adminapp | ✅ Session |
| 6 | `/admin/editcity/<id>/` | GET, POST | adminapp | ✅ Session |
| 7 | `/admin/deletecity/<cityid>/` | GET | adminapp | ✅ Session |
| 8 | `/admin/bindareas/` | GET | adminapp | ❌ Public |
| 9 | `/admin/addarea/` | GET, POST | adminapp | ✅ Session |
| 10 | `/admin/editarea/<id>/` | GET, POST | adminapp | ✅ Session |
| 11 | `/admin/deletearea/<areaid>/` | GET | adminapp | ✅ Session |
| 12 | `/admin/addhospitals/` | GET, POST | adminapp | ✅ Session |
| 13 | `/admin/edithospital/<id>/` | GET, POST | adminapp | ✅ Session |
| 14 | `/admin/deletehospital/<pid>/` | GET | adminapp | ✅ Session |
| 15 | `/hospital/` | GET | hospitalapp | ✅ Session |
| 16 | `/hospital/login/` | GET, POST | hospitalapp | ❌ Public |
| 17 | `/hospital/logout/` | GET | hospitalapp | ❌ Public |
| 18 | `/hospital/bindareas/` | GET | hospitalapp | ❌ Public |
| 19 | `/hospital/register/` | GET, POST | hospitalapp | ✅ Session |
| 20 | `/hospital/editreceptionist/<id>/` | GET, POST | hospitalapp | ✅ Session |
| 21 | `/hospital/deletereceptionist/<pid>/` | GET | hospitalapp | ✅ Session |
| 22 | `/hospital/vaccine/` | GET, POST | hospitalapp | ✅ Session |
| 23 | `/hospital/editvaccine/<id>/` | GET, POST | hospitalapp | ✅ Session |
| 24 | `/hospital/deletevaccine/<vid>/` | GET | hospitalapp | ✅ Session |
| 25 | `/hospital/showbooking/` | GET | hospitalapp | ✅ Session |
| 26 | `/hospital/showpastbooking/` | GET | hospitalapp | ✅ Session |
| 27 | `/` | GET | patientapp | ❌ Public |
| 28 | `/about/` | GET | patientapp | ❌ Public |
| 29 | `/contact/` | GET | patientapp | ❌ Public |
| 30 | `/login/` | GET, POST | patientapp | ❌ Public |
| 31 | `/register/` | GET, POST | patientapp | ❌ Public |
| 32 | `/logout/` | GET | patientapp | ❌ Public |
| 33 | `/booking/` | GET, POST | patientapp | ✅ Session |
| 34 | `/deletebooking/<aid>/` | GET | patientapp | ✅ Session |
| 35 | `/bindvaccines/` | GET | patientapp | ❌ Public |
| 36 | `/changepass/` | GET, POST | patientapp | ✅ Session |
| 37 | `/viewvaccines/` | GET | patientapp | ✅ Session |
| 38 | `/loadvaccinedata/` | GET | patientapp | ❌ Public |
| 39 | `/receptionist/` | GET | receptionistapp | ✅ Session |
| 40 | `/receptionist/login/` | GET, POST | receptionistapp | ❌ Public |
| 41 | `/receptionist/logout/` | GET | receptionistapp | ❌ Public |
| 42 | `/receptionist/booking/` | GET | receptionistapp | ✅ Session |
| 43 | `/receptionist/showbooking/<id>/` | GET, POST | receptionistapp | ✅ Session |

> **Total: 43 endpoints** across 4 apps. No REST API / JSON responses — all endpoints render HTML templates.

---

*End of endpoint analysis.*
