# KiddoVax — Frontend Analysis

> Generated: 2026-03-24  
> Frontend type: Server-side rendered HTML via Django Template Engine  
> No SPA framework (no React, Vue, Angular). jQuery used for AJAX calls.

---

## Frontend Technology Stack

| Technology | Usage |
|-----------|-------|
| **Django Templates** | All pages — server-side rendered HTML |
| **Bootstrap 5** | Layout, forms, tables, badges, buttons (via CDN + local) |
| **jQuery** | AJAX calls for dependent dropdowns (city→area, hospital→vaccine) |
| **Font Awesome** | Icons throughout all panels |
| **Google Fonts** | `PT Sans` (admin), `Kumbh Sans` (patient), `Roboto` (login) |
| **Chart.js** | Bar/Line/Area/Pie/Scatter charts on admin dashboard base (static data) |
| **SimpleChart.js** | Weekly profit charts on admin base template |
| **Owl Carousel** | Image carousel (admin base) |
| **Light/Dark Mode Toggle** | Patient portal — `theme-change.js` |

---

## Static Asset Structure

| Folder | Used By |
|--------|---------|
| `static/admin/` | Admin panel (CSS, JS, fonts, images) |
| `static/clientlogin/` | Patient login & register pages |
| `static/patients/` | Patient portal pages |
| `static/hospital/` | Hospital panel |
| `static/receptionist/` | Receptionist panel |
| `static/profileimg/` | Hospital profile images (uploaded) |
| `static/staffimages/` | Receptionist staff images (uploaded) |

---

## Template Organization

Each app has its own `templates/<appname>/` directory. All admin/hospital/receptionist dashboards share a **base template** with a fixed sidebar and top header. Patient pages are standalone pages with a top navbar.

| App | Base Template | Approach |
|-----|--------------|----------|
| `adminapp` | `adminapp/base.html` | Sidebar + sticky header layout, `{% block contents %}` |
| `hospitalapp` | `hospitalapp/base.html` | Same sidebar pattern |
| `receptionistapp` | `receptionistapp/base.html` | Same sidebar pattern |
| `patientapp` | None (standalone pages) | Fixed top navbar + footer via `{% include %}` |

---

## 🔵 Admin Panel Pages

### Page 1 — Admin Login
**File:** `adminapp/templates/adminapp/login.html`  
**URL:** `/admin/login/`  
**Auth Required:** No

**Purpose:** Admin credential login screen.

**UI Components:**
- Avatar image (external CDN `pixabay.com`)
- Text input: `username`
- Password input: `password`
- Submit button: "Login"

**API Calls:** `POST /admin/login/`

---

### Page 2 — Admin Dashboard (Home)
**File:** `adminapp/templates/adminapp/home.html`  
**URL:** `/admin/`  
**Auth Required:** Yes (session `CName`)

**Purpose:** Admin landing page after login.

**UI Components:**
- Inherits `base.html` — full sidebar navigation, sticky top header, pie charts, bar charts, weekly sales line charts (all with static/random data — not connected to DB)
- Sidebar links: Dashboard, New Admin, City, Area, Hospitals
- Top header: Welcome message (`session.CName`), Logout dropdown

**API Calls:** None (charts use hardcoded static JS data)

---

### Page 3 — Manage City
**File:** `adminapp/templates/adminapp/city.html`  
**URL:** `/admin/city/`  
**Auth Required:** Yes

**Purpose:** Add, edit, and delete city records.

**UI Components:**
- Flash message alert (success/error)
- Form: `cityName` text input
- Submit button, Reset button
- Data table with columns: `#`, `City`, `Action` (Edit/Delete buttons)

**API Calls:** `POST /admin/city/`, `GET /admin/editcity/<id>/`, `GET /admin/deletecity/<cityid>/`

---

### Page 4 — Manage Area
**File:** `adminapp/templates/adminapp/area.html`  
**URL:** `/admin/addarea/`  
**Auth Required:** Yes

**Purpose:** Add, edit, and delete area records linked to a city.

**UI Components:**
- Flash message alert
- Form with: City dropdown (`cityId`), Area name input (`areaName`)
- Submit button, Reset button
- Data table with columns: `#`, `City`, `Area`, `Action` (Edit/Delete)

**API Calls:** `POST /admin/addarea/`, `GET /admin/editarea/<id>/`, `GET /admin/deletearea/<areaid>/`

---

### Page 5 — Manage Hospitals
**File:** `adminapp/templates/adminapp/hospitalreg.html`  
**URL:** `/admin/addhospitals/`  
**Auth Required:** Yes

**Purpose:** Register, edit, or delete hospitals on the platform.

**UI Components:**
- Flash message alert
- Form (multipart): Title, Doctor Name, Address, City dropdown, Area dropdown (dynamically loaded), Contact No., Password, Image file upload, current image preview
- Submit button, Reset button
- Data table: `#`, Image (thumbnail), Title, DrName, City, Contact, Action (Edit/Delete)
- **AJAX:** On city change → `GET /admin/bindareas/?city_id=<id>` updates Area dropdown

**API Calls:** `POST /admin/addhospitals/`, AJAX `GET /admin/bindareas/`, `GET /admin/edithospital/<id>/`, `GET /admin/deletehospital/<pid>/`

---

### Page 6 — Create Admin
**File:** `adminapp/templates/adminapp/createadmin.html`  
**URL:** `/admin/newadmin/`  
**Auth Required:** Yes

**Purpose:** Create additional admin accounts.

**UI Components:**
- Form: `username`, `password` fields
- Submit button
- Table of all existing admin accounts

**API Calls:** `POST /admin/newadmin/`

---

## 🟢 Hospital Panel Pages

### Page 7 — Hospital Login
**File:** `hospitalapp/templates/hospitalapp/login.html`  
**URL:** `/hospital/login/`  
**Auth Required:** No

**Purpose:** Hospital (doctor) login using contact number and password.

**UI Components:**
- Contact number input (`contact`)
- Password input (`password`)
- Submit button
- Flash messages for errors

**API Calls:** `POST /hospital/login/`

---

### Page 8 — Hospital Dashboard (Home)
**File:** `hospitalapp/templates/hospitalapp/home.html`  
**URL:** `/hospital/`  
**Auth Required:** Yes

**Purpose:** Hospital landing page after login. Inherits the sidebar layout.

**UI Components:**
- Sidebar: Home, Receptionist, Vaccine, ShowBooking, PastBooking, Logout
- Top header: Welcome `session.CName`

**API Calls:** None

---

### Page 9 — Manage Receptionists
**File:** `hospitalapp/templates/hospitalapp/receptionist.html`  
**URL:** `/hospital/register/`  
**Auth Required:** Yes

**Purpose:** Register and manage receptionist staff for the hospital.

**UI Components:**
- Flash message alert
- Form (multipart): Name, Address, Gender (dropdown), City, Area (dynamic AJAX), Contact No., Password, Staff Image upload + preview, Date of Joining
- Submit button, Reset button
- Data table: Image, Name, Address, Gender, Contact, Action (Edit/Delete)
- **AJAX:** On city change → `GET /hospital/bindareas/?city_id=<id>`

**API Calls:** `POST /hospital/register/`, AJAX `GET /hospital/bindareas/`, edit/delete variants

---

### Page 10 — Manage Vaccines
**File:** `hospitalapp/templates/hospitalapp/managevaccine.html`  
**URL:** `/hospital/vaccine/`  
**Auth Required:** Yes

**Purpose:** Add and manage vaccines in the hospital's catalogue.

**UI Components:**
- Flash message alert
- Form: Vaccine Name, Description, Price
- Submit button, Reset button
- Data table: `#`, Vaccine Name, Description, Price, Action (Edit/Delete)

**API Calls:** `POST /hospital/vaccine/`, `GET /hospital/editvaccine/<id>/`, `GET /hospital/deletevaccine/<vid>/`

---

### Page 11 — Today's Appointments
**File:** `hospitalapp/templates/hospitalapp/showappointment.html`  
**URL:** `/hospital/showbooking/`  
**Auth Required:** Yes

**Purpose:** View all vaccine appointments booked for today.

**UI Components:**
- Data table showing appointments filtered by today's date
- Columns: Date, Child Name, Vaccine, TimeIn, TimeOut, Status badge (Pending/Waiting/Success)

**API Calls:** `GET /hospital/showbooking/`

---

### Page 12 — Past Appointments
**File:** `hospitalapp/templates/hospitalapp/pastappointment.html` / `showappointment.html`  
**URL:** `/hospital/showpastbooking/`  
**Auth Required:** Yes

**Purpose:** View historical appointments (all dates before today).

**UI Components:** Same table structure as Today's Appointments but filtered for past dates.

**API Calls:** `GET /hospital/showpastbooking/`

---

## 🟡 Patient Portal Pages

All patient pages share:
- **Fixed top navbar** (via `{% include 'patientapp/menu.html' %}`)
- **Footer** (via `{% include 'patientapp/footer.html' %}`)
- **Light/Dark mode toggle** (via `theme-change.js`)
- **Session-aware nav:** Shows Login (guest) or Appointment + ChangePassword + VaccineList + Logout (logged-in)

---

### Page 13 — Home Page
**File:** `patientapp/templates/patientapp/home.html`  
**URL:** `/`  
**Auth Required:** No

**Purpose:** Public landing page with vaccine awareness content.

**UI Components:**
- Fixed navbar with brand "KiddoVax"
- Hero banner slider with health awareness message
- Features section: 4 prevention tip cards with icons (Wash hands, Social distancing, Avoid face touching, Respiratory hygiene)
- Services section: 3 image cards (Face Mask, Wash Hands, Avoid Contact)
- Footer

**API Calls:** None

---

### Page 14 — About Page
**File:** `patientapp/templates/patientapp/about.html`  
**URL:** `/about/`  
**Auth Required:** No

**Purpose:** Static informational page about the vaccine platform.

**UI Components:** Navbar, static content, footer

**API Calls:** None

---

### Page 15 — Contact Page
**File:** `patientapp/templates/patientapp/contact.html`  
**URL:** `/contact/`  
**Auth Required:** No

**Purpose:** Static contact page.

**UI Components:** Navbar, static content, footer

**API Calls:** None

---

### Page 16 — Patient Login
**File:** `patientapp/templates/patientapp/login.html`  
**URL:** `/login/`  
**Auth Required:** No

**Purpose:** Patient login with contact number and password. Background image is `clientlogin/images/home1.jpg`.

**UI Components:**
- Contact number input (`contactno`) — restricted to digits only (JS validation), max 10 chars, must be exactly 10 digits to enable submit
- Password input (`password`)
- Submit button (`Log In`) — **disabled until 10-digit contact is entered**
- Link: "New Register" → `/register/`
- Flash messages for errors

**API Calls:** `POST /login/`

---

### Page 17 — Patient Registration
**File:** `patientapp/templates/patientapp/register.html`  
**URL:** `/register/`  
**Auth Required:** No

**Purpose:** New patient self-registration form.

**UI Components:**
- Form: Name, Address, City dropdown (dynamic AJAX), Area dropdown, Contact No. (10-digit JS validation), Password, RFID No.
- Submit button — disabled until valid 10-digit contact
- Link: "Already registered? Login"
- **AJAX:** On city change → `GET /admin/bindareas/?city_id=<id>` populates Area dropdown

**API Calls:** `POST /register/`, AJAX `GET /admin/bindareas/`

---

### Page 18 — Vaccine Booking
**File:** `patientapp/templates/patientapp/bookvaccine.html`  
**URL:** `/booking/`  
**Auth Required:** Yes

**Purpose:** Patient books a vaccine appointment and views their existing bookings.

**UI Components:**
- Breadcrumb: Home → Vaccine Booking
- Booking form: Child Name (text), Hospital (dropdown), Vaccine (dropdown — AJAX loaded), Appointment Date (date picker), Submit button
- **AJAX:** On hospital change → `GET /bindvaccines/?h_id=<id>` populates Vaccine dropdown
- Appointments table with columns: `#`, Date, Child Name, Hospital, Vaccine, Status badge, Action
  - Status badges: `Pending` (yellow, `active=0`), `Waiting` (grey, `active=1`), `Success` (green, `active=2`)
  - Cancel button shown only when `active=0`; otherwise shows "No Action" badge

**API Calls:** `POST /booking/`, AJAX `GET /bindvaccines/`, `GET /deletebooking/<aid>/`

---

### Page 19 — View Vaccine List
**File:** `patientapp/templates/patientapp/showvaccines.html`  
**URL:** `/viewvaccines/`  
**Auth Required:** Yes

**Purpose:** Patient browses all available vaccines across all hospitals; can filter by hospital.

**UI Components:**
- Hospital filter dropdown (includes "All" option)
- **AJAX:** On hospital change → `GET /loadvaccinedata/?h_id=<id>` loads and replaces table body
- Vaccine data table: `#`, Hospital Name, Vaccine Name, Description, Price

**API Calls:** `GET /viewvaccines/`, AJAX `GET /loadvaccinedata/`

---

### Page 20 — Change Password
**File:** `patientapp/templates/patientapp/changepassword.html`  
**URL:** `/changepass/`  
**Auth Required:** Yes

**Purpose:** Logged-in patient changes their account password.

**UI Components:**
- Breadcrumb: Home → Vaccine Booking (reused breadcrumb label — not changed in template)
- Form: Current Password, New Password, Confirm Password (all type="password")
- Submit button
- Flash messages for validation errors and success

**API Calls:** `POST /changepass/`

---

## 🔴 Receptionist Panel Pages

### Page 21 — Receptionist Login
**File:** `receptionistapp/templates/receptionistapp/login.html`  
**URL:** `/receptionist/login/`  
**Auth Required:** No

**Purpose:** Receptionist login using contact number and password.

**UI Components:**
- Contact number input (`contact`)
- Password input (`password`)
- Submit button
- Flash messages

**API Calls:** `POST /receptionist/login/`

---

### Page 22 — Receptionist Dashboard (Home)
**File:** `receptionistapp/templates/receptionistapp/home.html`  
**URL:** `/receptionist/`  
**Auth Required:** Yes

**Purpose:** Receptionist landing page. Inherits base sidebar.

**UI Components:**
- Sidebar: Home, Booking, Logout
- Top header: Welcome `session.CName`

**API Calls:** None

---

### Page 23 — All Appointments (Booking List)
**File:** `receptionistapp/templates/receptionistapp/booking.html`  
**URL:** `/receptionist/booking/`  
**Auth Required:** Yes

**Purpose:** Receptionist views all appointments for their hospital.

**UI Components:**
- Appointments table: Date, Child Name, Vaccine, TimeIn, TimeOut, Status badge (Pending/Waiting/Success), View button
- TimeIn/TimeOut shows "Pending" if not yet recorded
- "View" button → navigates to appointment detail page

**API Calls:** `GET /receptionist/booking/`

---

### Page 24 — Appointment Detail / Check-In-Out
**File:** `receptionistapp/templates/receptionistapp/showdata.html`  
**URL:** `/receptionist/showbooking/<id>/`  
**Auth Required:** Yes

**Purpose:** Receptionist views a single appointment's details and performs check-in or check-out action.

**UI Components:**
- Form showing: RFID No. input (`rfidno`), Appointment Date (read-only display), Child Name (display), Vaccine Name (display)
- Submit button — performs check-in (active 0→1) or check-out (active 1→2) based on current status

**API Calls:** `GET /receptionist/showbooking/<id>/`, `POST /receptionist/showbooking/<id>/`

---

## Navigation Flow

### Patient Portal Navigation

```
[Public]
  /  (Home)
    ├── /about/
    ├── /contact/
    └── /login/
          ├── [Login success] → / (Home, now session active)
          └── "New Register" → /register/ → /login/

[Logged-in Patient — Navbar]
  Appointment   → /booking/
                    └── Delete appointment → /deletebooking/<aid>/
  ChangePassword → /changepass/
  VaccineList    → /viewvaccines/
  Logout         → /logout/ → / (Home, guest)
```

### Admin Panel Navigation (Sidebar)

```
/admin/login/  →  /admin/ (Dashboard)
  Sidebar:
    Dashboard     → /admin/
    New Admin     → /admin/newadmin/
    City          → /admin/city/
                      ├── Edit → /admin/editcity/<id>/
                      └── Delete → /admin/deletecity/<cityid>/
    Area          → /admin/addarea/
                      ├── Edit → /admin/editarea/<id>/
                      └── Delete → /admin/deletearea/<areaid>/
    Hospitals     → /admin/addhospitals/
                      ├── Edit → /admin/edithospital/<id>/
                      └── Delete → /admin/deletehospital/<pid>/
  Logout (header dropdown)
```

### Hospital Panel Navigation (Sidebar)

```
/hospital/login/  →  /hospital/ (Dashboard)
  Sidebar:
    Home          → /hospital/
    Receptionist  → /hospital/register/
                      ├── Edit → /hospital/editreceptionist/<id>/
                      └── Delete → /hospital/deletereceptionist/<pid>/
    Vaccine       → /hospital/vaccine/
                      ├── Edit → /hospital/editvaccine/<id>/
                      └── Delete → /hospital/deletevaccine/<vid>/
    ShowBooking   → /hospital/showbooking/
    PastBooking   → /hospital/showpastbooking/
  Logout
```

### Receptionist Panel Navigation (Sidebar)

```
/receptionist/login/  →  /receptionist/ (Dashboard)
  Sidebar:
    Home     → /receptionist/
    Booking  → /receptionist/booking/
                  └── View → /receptionist/showbooking/<id>/
                               └── Submit → Check-In or Check-Out → /receptionist/booking/
  Logout
```

---

## Partial / Reusable Templates

| Template | Included By | Purpose |
|----------|------------|---------|
| `patientapp/menu.html` | All patient pages | Top navbar with session-aware links |
| `patientapp/footer.html` | All patient pages | Site footer |
| `adminapp/citytoarea.html` | AJAX response | Renders `<option>` tags for area dropdown |
| `patientapp/hospitaltovaccine.html` | AJAX response | Renders `<option>` tags for vaccine dropdown |
| `patientapp/loadvaccinerecord.html` | AJAX response | Renders vaccine table rows for filter |

---

## Summary: Pages Count

| Portal | Pages | Template Files |
|--------|-------|---------------|
| Admin | 6 | 7 (+ base + citytoarea) |
| Hospital | 6 | 7 (+ base + pastappointment) |
| Patient | 9 | 8 (+ menu + footer + 3 AJAX partials) |
| Receptionist | 4 | 4 (+ base) |
| **Total** | **25 pages** | **33 templates** |

---

*End of frontend analysis.*
