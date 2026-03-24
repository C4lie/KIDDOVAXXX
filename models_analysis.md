# KiddoVax — Django Models Analysis

> Generated: 2026-03-24  
> Source apps: `adminapp`, `hospitalapp`, `patientapp`, `receptionistapp`

---

## Model: Admintbl
**App:** `adminapp`  
**Purpose:** Stores admin login credentials for system-level access.

**Fields:**
| Field | Type |
|-------|------|
| `id` | AutoField (PK, auto) |
| `username` | CharField (max_length=100) |
| `password` | CharField (max_length=200) |

**Relationships:** None

---

## Model: City
**App:** `adminapp`  
**Purpose:** Master table for city names used across the platform for address selection.

**Fields:**
| Field | Type |
|-------|------|
| `id` | AutoField (PK, auto) |
| `cityName` | CharField (max_length=255) |

**Relationships:** None

---

## Model: Area
**App:** `adminapp`  
**Purpose:** Master table for area/locality names, linked to a City.

**Fields:**
| Field | Type |
|-------|------|
| `id` | AutoField (PK, auto) |
| `areaName` | CharField (max_length=255) |
| `cityId` | ForeignKey → `City` |

**Relationships:**
- `cityId` → **ForeignKey** to `City` (`on_delete=CASCADE`)

---

## Model: Hospitaltbl
**App:** `hospitalapp`  
**Purpose:** Stores hospital registration details including doctor info, location, contact, login password, and profile image.

**Fields:**
| Field | Type |
|-------|------|
| `id` | AutoField (PK, auto) |
| `title` | CharField (max_length=500) |
| `dcrname` | CharField (max_length=255, blank/null allowed) |
| `address` | CharField (max_length=500) |
| `cityId` | ForeignKey → `City` |
| `areaId` | ForeignKey → `Area` |
| `contactNo` | IntegerField (blank/null allowed) |
| `password` | CharField (max_length=255) |
| `img` | ImageField (upload_to='profileimg', blank/null allowed) |

**Relationships:**
- `cityId` → **ForeignKey** to `adminapp.City` (`on_delete=CASCADE`)
- `areaId` → **ForeignKey** to `adminapp.Area` (`on_delete=CASCADE`)

---

## Model: Vaccinetbl
**App:** `hospitalapp`  
**Purpose:** Catalogue of vaccines offered by a hospital, including name, description, and price.

**Fields:**
| Field | Type |
|-------|------|
| `id` | AutoField (PK, auto) |
| `vaccineName` | CharField (max_length=255) |
| `vaccineDescr` | CharField (max_length=500) |
| `price` | IntegerField (blank/null allowed) |
| `hospitalId` | ForeignKey → `Hospitaltbl` |

**Relationships:**
- `hospitalId` → **ForeignKey** to `Hospitaltbl` (`on_delete=CASCADE`, null/blank allowed)

---

## Model: Receptionisttbl
**App:** `hospitalapp`  
**Purpose:** Stores receptionist (staff) details for a hospital, including personal info, login credentials, and joining date.

**Fields:**
| Field | Type |
|-------|------|
| `id` | AutoField (PK, auto) |
| `name` | CharField (max_length=255) |
| `address` | CharField (max_length=500) |
| `gender` | CharField (max_length=10, default='Male') |
| `contactNo` | IntegerField (blank/null allowed) |
| `password` | CharField (max_length=255) |
| `staffimg` | ImageField (upload_to='staffimages') |
| `doj` | DateField (null allowed) |
| `hospitalid` | ForeignKey → `Hospitaltbl` |
| `cityId` | ForeignKey → `City` |
| `areaId` | ForeignKey → `Area` |

**Relationships:**
- `hospitalid` → **ForeignKey** to `Hospitaltbl` (`on_delete=CASCADE`, blank/null allowed)
- `cityId` → **ForeignKey** to `adminapp.City` (`on_delete=CASCADE`)
- `areaId` → **ForeignKey** to `adminapp.Area` (`on_delete=CASCADE`)

---

## Model: Patienttbl
**App:** `patientapp`  
**Purpose:** Stores patient registration details including name, address, contact, and login credentials.

**Fields:**
| Field | Type |
|-------|------|
| `id` | AutoField (PK, auto) |
| `name` | CharField (max_length=255) |
| `address` | CharField (max_length=500) |
| `contactNo` | IntegerField (blank/null allowed) |
| `password` | CharField (max_length=255) |
| `cityId` | ForeignKey → `City` |
| `areaId` | ForeignKey → `Area` |

**Relationships:**
- `cityId` → **ForeignKey** to `adminapp.City` (`on_delete=CASCADE`)
- `areaId` → **ForeignKey** to `adminapp.Area` (`on_delete=CASCADE`)

---

## Model: Appointmenttbl
**App:** `patientapp`  
**Purpose:** Records a vaccine appointment made by a patient at a specific hospital. Tracks the child being vaccinated, appointment date, timestamps, RFID number, and appointment status.

**Fields:**
| Field | Type |
|-------|------|
| `id` | AutoField (PK, auto) |
| `childname` | CharField (max_length=255, blank/null allowed) |
| `aptdate` | DateField (null allowed) |
| `indt` | DateTimeField (auto_now_add=True, blank/null allowed) |
| `outdt` | DateTimeField (auto_now_add=True, blank/null allowed) |
| `active` | IntegerField (blank/null allowed) |
| `rfidno` | IntegerField (blank/null allowed) |
| `hospitalid` | ForeignKey → `Hospitaltbl` |
| `vaccineid` | ForeignKey → `Vaccinetbl` |
| `patientid` | ForeignKey → `Patienttbl` |

**Relationships:**
- `hospitalid` → **ForeignKey** to `hospitalapp.Hospitaltbl` (`on_delete=CASCADE`)
- `vaccineid` → **ForeignKey** to `hospitalapp.Vaccinetbl` (`on_delete=CASCADE`)
- `patientid` → **ForeignKey** to `Patienttbl` (`on_delete=CASCADE`, blank/null allowed)

---

## Model Summary Table

| Model | App | Fields | ForeignKeys |
|-------|-----|--------|-------------|
| `Admintbl` | adminapp | 2 | 0 |
| `City` | adminapp | 1 | 0 |
| `Area` | adminapp | 2 | 1 → City |
| `Hospitaltbl` | hospitalapp | 7 | 2 → City, Area |
| `Vaccinetbl` | hospitalapp | 4 | 1 → Hospitaltbl |
| `Receptionisttbl` | hospitalapp | 9 | 3 → Hospitaltbl, City, Area |
| `Patienttbl` | patientapp | 5 | 2 → City, Area |
| `Appointmenttbl` | patientapp | 7 | 3 → Hospitaltbl, Vaccinetbl, Patienttbl |

> `receptionistapp` — No models defined. Uses models from `hospitalapp` and `patientapp` directly in views.

---

*End of model analysis.*
