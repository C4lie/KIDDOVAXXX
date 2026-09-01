# KiddoVax – Complete Setup & Installation Guide

Welcome to **KiddoVax**, an enterprise-grade Child Immunization Management and Pediatric Tracking System built with **Django 5.2.12** and **SQLite**. This platform coordinates pediatric vaccinations, smart RFID check-ins, automated SMS notifications, vaccine inventory forecasting, and digital certificate generation across 4 dedicated user portals.

---

## 📑 Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
   - [Clone Repository](#clone-repository)
   - [Create & Activate Virtual Environment](#create--activate-virtual-environment)
   - [Install Dependencies](#install-dependencies)
3. [Environment Configuration (.env)](#3-environment-configuration-env)
4. [Database Setup & Data Seeding](#4-database-setup--data-seeding)
   - [Run Migrations](#run-database-migrations)
   - [Seed Default Users](#seed-default-users-and-master-data)
5. [Running the Development Server](#5-running-the-development-server)
6. [Accessing the Application](#6-accessing-the-application)
   - [Portal URLs & Default Credentials](#portal-urls--default-credentials)
   - [Portal Overview](#portal-overview)
7. [Running Tests](#7-running-tests)
8. [Project Structure](#8-project-structure)
9. [Troubleshooting & FAQs](#9-troubleshooting--faqs)

---

## 1. Prerequisites

Before installing KiddoVax, ensure your system satisfies the following system requirements:

- **Python**: Version `3.10`, `3.11`, or `3.12` ([Download Python](https://www.python.org/downloads/))
- **Git**: Version Control System ([Download Git](https://git-scm.com/))
- **pip**: Latest Python package manager (bundled with Python)
- **SQLite3**: Lightweight relational database (bundled with Python standard library)
- **Operating System**: Windows 10/11, macOS 11+, or Linux (Ubuntu 20.04+, Debian, Fedora, etc.)
- *(Optional)* **Twilio Account**: For live SMS appointment reminder notifications.

Verify your installed versions by running:

```bash
# Verify Python version
python --version   # Windows
python3 --version  # macOS / Linux

# Verify Git version
git --version

# Verify pip version
pip --version      # Windows
pip3 --version     # macOS / Linux
```

---

## 2. Installation

### Clone Repository

Clone the project repository from GitHub and navigate into the project directory:

```bash
git clone https://github.com/C4lie/KIDDOVAXXX.git
cd KIDDOVAXXX
```

> **Note**: If you already have the repository locally, ensure you are on the latest branch:
> ```bash
> git pull origin main
> ```

---

### Create & Activate Virtual Environment

It is strongly recommended to use an isolated Python virtual environment (`venv`) to prevent dependency conflicts.

#### **On Windows (PowerShell / Command Prompt)**

```powershell
# Create virtual environment named 'venv'
python -m venv venv

# Activate in PowerShell
.\venv\Scripts\Activate.ps1

# OR Activate in Command Prompt (cmd.exe)
venv\Scripts\activate.bat
```

> **PowerShell Execution Policy Note**: If you encounter an execution policy error on Windows PowerShell, run:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\venv\Scripts\Activate.ps1
> ```

#### **On macOS / Linux (bash / zsh)**

```bash
# Create virtual environment named 'venv'
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

*(Once activated, your terminal prompt will show `(venv)` at the beginning.)*

---

### Install Dependencies

Upgrade `pip` and install all required Python packages from `requirements.txt`:

#### **On Windows**
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### **On macOS / Linux**
```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

### Core Package List

The KiddoVax platform relies on the following core dependencies:

| Package | Version | Description |
|---|---|---|
| `Django` | `5.2.12` | High-level Python Web framework |
| `asgiref` | `3.11.1` | ASGI specifications and helper utilities |
| `sqlparse` | `0.5.5` | Non-validating SQL parser |
| `tzdata` | `2025.3` | IANA Timezone database for Python |
| `openpyxl` | `3.1.5` | Excel (.xlsx) file generation and data export |
| `pillow` | `12.1.1` | Python Imaging Library for QR codes & profile images |
| `reportlab` | `5.0.0` | PDF generation engine for digital vaccine cards |
| `beautifulsoup4` | `4.15.0` | HTML/XML parsing library |
| `requests` | `2.32.5` | HTTP library for external REST API communications |
| `twilio` | `9.10.4` | Twilio API library for SMS notification dispatch |
| `PyJWT` | `2.12.1` | JSON Web Token implementation for secure tokens |
| `qrcode` | `8.2` | QR Code generator for child vaccine digital passes |

---

## 3. Environment Configuration (.env)

The application automatically loads configuration variables from a `.env` file located in the root project directory (`KIDDOVAXXX/.env`).

Create or edit the `.env` file in the root directory:

```env
# Django Core Settings
DJANGO_SETTINGS_MODULE=kiddovax.settings
SECRET_KEY=your_secret_key_here
DEBUG=True

# Twilio SMS Service Settings (Optional / Sandbox)
TWILIO_ACCOUNT_SID=your_twilio_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE=your_twilio_phone_here
```

### Explanation of Environment Variables

- `DJANGO_SETTINGS_MODULE`: Points Django to the project's settings module (`kiddovax.settings`).
- `SECRET_KEY`: A unique, secret cryptographic key for Django session signing and security.
- `DEBUG`: Set to `True` for local development. Set to `False` in production environments.
- `TWILIO_ACCOUNT_SID`: Account SID from Twilio Console for SMS alerts.
- `TWILIO_AUTH_TOKEN`: Auth Token corresponding to your Twilio account.
- `TWILIO_PHONE`: Twilio virtual phone number formatted with international code (e.g., `+13186603520`).

> 💡 **No third-party dotenv dependency needed**: KiddoVax's `kiddovax/settings.py` includes a lightweight, built-in `.env` reader that parses `.env` keys into `os.environ` on boot.

---

## 4. Database Setup & Data Seeding

KiddoVax utilizes an embedded **SQLite3** database (`db.sqlite3`).

### Run Database Migrations

Apply existing schema migrations across all installed applications (`adminapp`, `hospitalapp`, `patientapp`, `receptionistapp`):

#### **On Windows**
```powershell
python manage.py makemigrations
python manage.py migrate
```

#### **On macOS / Linux**
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

---

### Seed Default Users and Master Data

The repository includes a `create_users.py` script that seeds initial master data (City, Area) and test user accounts for the Admin, Hospital, and Receptionist portals.

#### **Run Seeding Script:**

#### **On Windows**
```powershell
python manage.py shell -c "exec(open('create_users.py').read())"
```

#### **On macOS / Linux**
```bash
python3 manage.py shell -c "exec(open('create_users.py').read())"
```

#### *(Optional) Create Django Superuser:*
To access the standard Django backend admin interface:

```bash
python manage.py createsuperuser
```

---

## 5. Running the Development Server

Start the Django local development web server:

#### **On Windows**
```powershell
python manage.py runserver
```

#### **On macOS / Linux**
```bash
python3 manage.py runserver
```

### Custom Port or Host Binding
If port `8000` is already in use, or if you want to expose the server to your local network:

```bash
# Run on port 8080
python manage.py runserver 8080

# Run on all network interfaces
python manage.py runserver 0.0.0.0:8000
```

The console will display:
```text
System check identified no issues (0 silenced).
September 01, 2026 - 16:35:00
Django version 5.2.12, using settings 'kiddovax.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK (or CTRL-C).
```

---

## 6. Accessing the Application

Open your browser and navigate to any of the portal entry points:

### Portal URLs & Default Credentials

| Portal Name | Access URL | Default Username / Contact | Default Password |
|---|---|---|---|
| **Patient Portal (Home)** | `http://127.0.0.1:8000/` | *Public Access* | *N/A* |
| **Patient Login** | `http://127.0.0.1:8000/login/` | Registered Parent Contact | Parent Password |
| **Admin Portal** | `http://127.0.0.1:8000/admin/login/` | `admin` | `admin` |
| **Hospital Portal** | `http://127.0.0.1:8000/hospital/login/` | `1234567890` (or `1`) | `hospital123` (or `hospital`) |
| **Receptionist Portal** | `http://127.0.0.1:8000/receptionist/login/` | `0987654321` (or `2`) | `receptionist123` (or `receptionist`) |

---

### Portal Overview

```
                      ┌────────────────────────────────────────┐
                      │          KiddoVax Platform             │
                      └──────────────────┬─────────────────────┘
                                         │
     ┌──────────────────┬────────────────┼─────────────────┬──────────────────┐
     ▼                  ▼                ▼                 ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐
│ Patient      │ │ Admin        │ │ Hospital     │ │ Receptionist │ │ Smart RFID &    │
│ Portal       │ │ Portal       │ │ Portal       │ │ Portal       │ │ AI Services     │
├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤ ├─────────────────┤
│ • Child Mgmt │ │ • Cities     │ │ • Vaccines   │ │ • Check-in   │ │ • Queue AI      │
│ • Bookings   │ │ • Areas      │ │ • Inventory  │ │ • Check-out  │ │ • Stock Forecast│
│ • QR Passes  │ │ • Hospitals  │ │ • Staff/UIN  │ │ • Card Link  │ │ • OCR Scanner   │
│ • PDF Cards  │ │ • System Log │ │ • AI Queue   │ │ • Daily Log  │ │ • SMS Engine    │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └─────────────────┘
```

1. **Patient / Parent Portal (`/`)**:
   - Register children with blood groups and DOB.
   - Schedule vaccination slots based on hospital proximity and live inventory.
   - Download PDF vaccination certificates and view secure dynamic QR codes.
   - Interactive vaccination journey timeline and AI education assistant.
   - Real-time multi-language support (English / Hindi).

2. **Hospital Portal (`/hospital/`)**:
   - Manage hospital profile, location, and operating hours.
   - Manage vaccine catalog, pricing, dose intervals, and stock thresholds.
   - AI-driven dynamic Queue Prioritization and 14-day Inventory Forecasting.
   - Register receptionists and issue 5-digit staff Unique Identification Numbers (UIN).
   - In-hospital patient onboarding & RFID card generation.

3. **Receptionist Portal (`/receptionist/`)**:
   - Daily appointment lookup and arrival tracking.
   - Smart RFID scanning for touchless child check-in and checkout.
   - Automatic dose completion logging and inventory decrement.
   - RFID card linking for newly registered walk-in parents.

4. **Admin Portal (`/admin/`)**:
   - Manage master geographical directory (Cities and Areas).
   - Authorize and manage network hospital branches.
   - System administration, analytics, and hospital credential tracking.

---

## 7. Running Tests

KiddoVax includes a comprehensive automated test suite covering models, views, API endpoints, RFID check-in services, inventory forecasting, queue prioritization, translation middleware, and PDF generation.

### Run All Unit & Integration Tests

#### **On Windows**
```powershell
python manage.py test
```

#### **On macOS / Linux**
```bash
python3 manage.py test
```

### Run Tests for Specific Applications

```bash
# Run tests for Patient Portal & AI Services
python manage.py test patientapp

# Run tests for Hospital Portal & Staff Services
python manage.py test hospitalapp

# Run tests for Receptionist Portal & RFID Infrastructure
python manage.py test receptionistapp

# Run tests for Admin Portal
python manage.py test adminapp
```

### Verbose Test Output
To inspect individual test cases and execution time:

```bash
python manage.py test -v 2
```

---

## 8. Project Structure

```text
KIDDOVAXXX/
├── adminapp/                       # Master Data & Administration App
│   ├── migrations/                 # Database migrations for admin app
│   ├── templates/                  # Admin portal HTML templates
│   ├── models.py                   # City, Area, Admintbl models
│   ├── views.py                    # Admin CRUD & auth views
│   ├── urls.py                     # /admin/ route mappings
│   └── tests.py                    # Admin unit tests
│
├── hospitalapp/                    # Hospital & Inventory Management App
│   ├── migrations/                 # Database migrations for hospital app
│   ├── services/                   # Inventory forecast & alert services
│   ├── templates/                  # Hospital portal HTML templates
│   ├── models.py                   # Hospitaltbl, Vaccinetbl, Receptionisttbl
│   ├── views.py                    # Vaccine inventory, staff mgmt, AI queue
│   ├── urls.py                     # /hospital/ route mappings
│   └── tests.py                    # Staff UI & hospital tests
│
├── patientapp/                     # Patient & Child Immunization App
│   ├── middleware.py               # Auto-translation & AccountStatus middlewares
│   ├── services/                   # Queue priority, PDF, OCR, Geocoding services
│   ├── templates/                  # Patient portal HTML templates
│   ├── models.py                   # Patienttbl, Childtbl, Appointmenttbl, RFIDCard
│   ├── views.py                    # Bookings, journey, QR card, auth
│   ├── urls.py                     # / (root) & patient route mappings
│   └── tests.py                    # 14+ automated integration test cases
│
├── receptionistapp/                # Reception Desk & Check-in App
│   ├── services/                   # RFID lookup, card linking & check-in
│   ├── templates/                  # Receptionist portal HTML templates
│   ├── views.py                    # Appointment check-in/check-out, RFID scan
│   ├── urls.py                     # /receptionist/ route mappings
│   └── tests.py                    # RFID API & hardware simulation tests
│
├── kiddovax/                       # Project Configuration Root
│   ├── __init__.py
│   ├── asgi.py                     # ASGI entry point for async deployment
│   ├── settings.py                 # Core Django configuration & .env loader
│   ├── urls.py                     # Master URL routing table
│   └── wsgi.py                     # WSGI entry point for web servers
│
├── static/                         # Static Web Assets
│   ├── css/                        # Custom CSS stylesheets
│   ├── js/                         # JavaScript, RFID scanner logic, jQuery
│   ├── images/                     # Hospital branding, vaccine icons, logos
│   └── media/                      # Uploaded cards, PDFs, child QR passes
│
├── create_users.py                 # Default database seeder script
├── requirements.txt                # Python package dependency manifest
├── manage.py                       # Django CLI management executable
├── .env                            # Environment variables file
├── .gitignore                      # Git ignore rule definitions
├── PROJECT_DOCUMENTATION.md        # Detailed technical feature documentation
├── README.md                       # High-level project summary
└── SETUP.md                        # Setup and installation guide (this file)
```

---

## 9. Troubleshooting & FAQs

### Q1: `ImportError: No module named 'django'` or dependencies missing
**Cause**: The virtual environment is not activated or packages were installed in global Python.  
**Solution**:
1. Check that `(venv)` appears in your terminal prompt.
2. If not, activate it (`.\venv\Scripts\Activate.ps1` on Windows or `source venv/bin/activate` on macOS/Linux).
3. Re-run `pip install -r requirements.txt`.

---

### Q2: PowerShell says `Execution of scripts is disabled on this system`
**Cause**: Windows restricts running unsigned PowerShell scripts by default.  
**Solution**: Run the following command in PowerShell before activating:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

---

### Q3: `Port 8000 is already in use` (`OSError: [WinError 10048]` / `Address already in use`)
**Cause**: Another process or background server is bound to port `8000`.  
**Solution**:
1. Specify an alternative port:
   ```bash
   python manage.py runserver 8080
   ```
2. Or terminate the process occupying port 8000:
   - **Windows**: `netstat -ano | findstr :8000` followed by `taskkill /PID <PID> /F`
   - **macOS/Linux**: `lsof -i :8000` followed by `kill -9 <PID>`

---

### Q4: Database migration errors or `no such table`
**Cause**: Database schema is out of sync with model definitions.  
**Solution**:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py shell -c "exec(open('create_users.py').read())"
```

---

### Q5: Static files (CSS, Images) not displaying properly
**Solution**: Run collectstatic if running with `DEBUG=False` or verify `STATICFILES_DIRS` in `kiddovax/settings.py`:
```bash
python manage.py collectstatic --noinput
```

---

### Q6: Twilio SMS alerts failing or throwing authentication errors
**Cause**: Invalid Twilio SID or token in `.env`.  
**Solution**: KiddoVax is designed to fail gracefully when Twilio credentials are in test mode or unavailable. To test SMS locally:
1. Ensure your `.env` contains valid `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_PHONE`.
2. For local testing without active Twilio credits, the system logs notifications in the internal notification center (`/notifications/`).

---

### 💬 Need More Help?
- Refer to [PROJECT_DOCUMENTATION.md](file:///d:/TeamKiddoVax/KIDDOVAXXX/PROJECT_DOCUMENTATION.md) for full architectural workflows, ER diagrams, and endpoint specifications.
- Submit issues or pull requests at [GitHub Repository](https://github.com/C4lie/KIDDOVAXXX).
