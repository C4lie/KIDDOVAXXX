# KiddoVax – Child Immunization Management System

## Overview
KiddoVax is a child immunization management system designed to coordinate pediatric vaccinations across multiple partner hospitals and clinics. The system features dedicated portals for Admins, Hospitals, Receptionists, and Patients to manage hospital setups, vaccine catalogs, slot bookings, dynamic schedules, notifications, and digital vaccine records.

## Features

### Patient Portal
- **Child Profile Management**: Register children under the guardian's account, select blood groups, and track date of birth details.
- **Vaccine Booking**: Book immunization appointments at available hospital centers based on vaccine details and date slots.
- **Appointment Tracking**: View scheduled dates, pending checklists, and vaccination history logs.
- **Notifications**: Check dynamic SMS-based alerts and in-app system notifications.
- **Vaccine Information**: Explore the vaccine directory containing doses, diseases prevented, side effects, and pricing details.
- **Digital Records**: Download PDF vaccine cards, generate secure digital QR cards, and print consolidated health summaries.

### Hospital Portal
- **Vaccine Inventory**: Manage the hospital's vaccine catalog, prices, and availability statuses.
- **Appointment Management**: View child bookings, patient details, and manage schedule logs.
- **Receptionist Management**: Register and manage the clinical receptionist staff.

### Receptionist Portal
- **Check-in/Check-out**: Handle check-ins (with arrival time and RFID scans) and check-outs (recording completion details).
- **Appointment Handling**: Keep track of daily appointments, mark immunizations as completed, and log records.

### Admin Portal
- **Hospital Management**: Register partner healthcare networks and clinics.
- **City and Area Management**: Add and manage city locations and area mapping for dynamic dropdown filters.
- **Analytics**: Keep track of hospital counts, patient registration rates, and vaccination trends.

## Tech Stack
- **Backend**: Django
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript (JQuery, flatpickr)
- **Styling**: Tailwind CSS, Bootstrap

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd KIDDOVAXXX
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run database migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

## Folder Structure

- `adminapp/`: App managing cities, areas, admin tables, and settings.
- `hospitalapp/`: App managing hospital networks, receptionist accounts, and vaccine inventories.
- `patientapp/`: App managing parent profiles, children profiles, appointment bookings, and records.
- `receptionistapp/`: App managing receptionist workflows, logs, and check-in/check-out.
- `kiddovax/`: Core configuration files, routing, settings, and WSGI/ASGI endpoints.
- `static/`: Contains CSS styles, images, and other static asset resources.

## Future Improvements
- **AI OCR Records Scan**: Optimize model extraction capabilities to identify handwritten immunization record cards and automatically upload them.
- **Predictive Scheduler**: Integrate age-based catch-up date calculators to proactively forecast vaccine slots for delayed doses.
