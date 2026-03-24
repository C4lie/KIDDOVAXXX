# KiddoVax — Django Backend Breakdown

> Generated: 2026-03-24

---

## 1. Django Apps in the Project

| # | App Name | Registered in INSTALLED_APPS |
|---|----------|------------------------------|
| 1 | `adminapp` | ✅ Yes |
| 2 | `hospitalapp` | ✅ Yes |
| 3 | `patientapp` | ✅ Yes |
| 4 | `receptionistapp` | ✅ Yes |

---

## 2. App Breakdown

---

### 🔵 `adminapp`

**Purpose:**  
Manages system-level admin authentication and location master data (Cities and Areas). Acts as the foundational configuration app for the platform.

**Files Present:**

| File | Present |
|------|---------|
| `__init__.py` | ✅ |
| `admin.py` | ✅ |
| `apps.py` | ✅ |
| `forms.py` | ✅ |
| `models.py` | ✅ |
| `urls.py` | ✅ |
| `views.py` | ✅ |
| `tests.py` | ✅ |
| `migrations/` | ✅ |
| `templates/` | ✅ |

**Models Defined:**
- `Admintbl` — Admin credentials (username, password)
- `City` — City master data
- `Area` — Area master data (linked to City via FK)

---

### 🟢 `hospitalapp`

**Purpose:**  
Manages hospital registrations, vaccine catalogue, and hospital-level receptionist staff. Imports location data from `adminapp`.

**Files Present:**

| File | Present |
|------|---------|
| `__init__.py` | ✅ |
| `admin.py` | ✅ |
| `apps.py` | ✅ |
| `forms.py` | ✅ |
| `models.py` | ✅ |
| `urls.py` | ✅ |
| `views.py` | ✅ |
| `tests.py` | ✅ |
| `migrations/` | ✅ |
| `templates/` | ✅ |

**Models Defined:**
- `Hospitaltbl` — Hospital profile (title, doctor name, address, city, area, contact, password, profile image)
- `Vaccinetbl` — Vaccine catalogue (name, description, price, linked to hospital)
- `Receptionisttbl` — Receptionist staff (name, address, gender, contact, password, image, date of joining, linked to hospital)

---

### 🟡 `patientapp`

**Purpose:**  
Manages patient registration and vaccine appointment booking. Imports hospital and location data from `hospitalapp` and `adminapp`.

**Files Present:**

| File | Present |
|------|---------|
| `__init__.py` | ✅ |
| `admin.py` | ✅ |
| `apps.py` | ✅ |
| `forms.py` | ✅ |
| `models.py` | ✅ |
| `urls.py` | ✅ |
| `views.py` | ✅ |
| `tests.py` | ✅ |
| `migrations/` | ✅ |
| `templates/` | ✅ |

**Models Defined:**
- `Patienttbl` — Patient profile (name, address, city, area, contact, password)
- `Appointmenttbl` — Vaccine appointments (linked to hospital, vaccine, and patient; stores child name, appointment date, in/out timestamps, RFID no, status)

---

### 🔴 `receptionistapp`

**Purpose:**  
Provides the receptionist-facing dashboard and workflow views. Has no independently defined models — relies entirely on models from `hospitalapp` and `patientapp`.

**Files Present:**

| File | Present |
|------|---------|
| `__init__.py` | ✅ |
| `admin.py` | ✅ |
| `apps.py` | ✅ |
| `models.py` | ✅ (empty — no models defined) |
| `urls.py` | ✅ |
| `views.py` | ✅ |
| `tests.py` | ✅ |
| `migrations/` | ✅ |
| `templates/` | ✅ |

> ⚠️ `models.py` exists but contains no model definitions. The app imports and uses models from `hospitalapp` and `patientapp`.

---

## 3. Overall Architecture

| Attribute | Value |
|-----------|-------|
| **Architecture Style** | **Modular Monolith** — Single Django project split into role-based apps sharing models via imports |
| **Django REST Framework (DRF)** | **No** — Not installed in `INSTALLED_APPS`. No serializers or API views present anywhere in the codebase. |
| **Template Engine** | Django's built-in template engine (each app has its own `templates/` directory) |
| **Database** | SQLite (`db.sqlite3`) |
| **Static Files** | Centralized `/static/` directory; media also served from `static/` |
| **Auth** | Custom credential-based auth (username/password stored in `Admintbl`, `Hospitaltbl`, etc.) — NOT using Django's built-in `auth.User` |

---

## Dependency Graph

```
adminapp
    └── City, Area
            └── hospitalapp (Hospitaltbl, Vaccinetbl, Receptionisttbl)
                    └── patientapp (Patienttbl, Appointmenttbl)
                            └── receptionistapp (views only, no own models)
```

---

*End of backend breakdown.*
