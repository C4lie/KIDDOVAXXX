KiddoVax — Advanced Product Features PRD

Version: 3.0
Status: Product Feature Specification
Product: KiddoVax
Domain: Child Immunization & Vaccination Management

1. Purpose

This PRD defines the advanced features that will make KiddoVax more useful, engaging, and differentiated from a basic vaccination appointment portal.

These features must integrate with the existing:

Patient Portal
Hospital Portal
Receptionist Portal
Admin Portal
RFID system
Appointment system
Vaccination records
Hospital database
Existing AI features
Existing authentication
Existing backend and frontend architecture

The goal is not to rebuild KiddoVax.

The goal is to extend the existing system while preserving its current architecture, UI, theme, connections, and functionality.

2. Product Differentiation

KiddoVax should not behave like a simple:

Register → Book Appointment → Get Vaccine

website.

The intended experience is:

Family Registration
↓
RFID Assignment
↓
Child Profiles
↓
Vaccination Passport
↓
Smart Hospital Discovery
↓
Appointment
↓
RFID Arrival
↓
Digital Check-in
↓
Live Queue
↓
Vaccination
↓
Second RFID Scan
↓
Vaccination Completion
↓
Digital Record
↓
Certificate
↓
Next Vaccination

The platform should connect the physical hospital experience with the digital vaccination journey.

3. Feature Priority
   P0 — Core Experience
   RFID Family Wallet
   Live Vaccination Journey
   Digital Hospital Front Desk
   Digital Queue / "I'm Here" Mode
   Vaccination Passport
   QR Certificate Vault
   Vaccination Gap Detector
   Vaccination Recovery Journey
   P1 — Hospital Experience
   Hospital Vaccination Session Mode
   Hospital Trust / Operational Profile
   Smart Walk-in Mode
   Hospital Capacity Heatmap
   Parent Feedback System
   P2 — Engagement & Administration
   Child Vaccination Milestones
   Child Growth & Preventive-Care Timeline
   Family Health Timeline
   RFID Incident Centre
   Admin Vaccination Command Centre
   Child Switching System
4. RFID Family Wallet
   4.1 Objective

Turn the RFID device into the physical identity bridge between the family and KiddoVax.

The RFID should not represent only one child.

One RFID device belongs to a parent/family and can be associated with multiple children.

4.2 Structure
RFID
│
└── Parent / Family
│
├── Child 1
│ ├── Vaccinations
│ ├── Appointments
│ └── Certificates
│
├── Child 2
│ ├── Vaccinations
│ ├── Appointments
│ └── Certificates
│
└── Child 3
4.3 Patient Experience

Patient should be able to see:

My RFID

RFID Number:
10384721

Status:
ACTIVE

Registered Children:
• Aarav
• Siya

Assigned Hospital:
ABC Hospital

Assigned Date:
12 August 2026
4.4 Receptionist Experience

When RFID is scanned:

RFID SCANNED

Family:
Chandril Patel

Children:
Aarav
Siya
Kabir

The system should automatically identify the relevant child based on today's appointment.

4.5 Requirements
RFID number must be unique.
RFID must belong to one family/user.
One RFID may contain multiple children.
RFID must never be used as a password.
RFID assignment must be auditable.
RFID can be activated/deactivated.
Lost RFID should be capable of being marked inactive.
Replacement RFID should preserve historical records. 5. Live Vaccination Journey
5.1 Objective

Give parents a visual real-time representation of their child's vaccination process.

Instead of simply displaying:

Appointment Confirmed

show the complete journey.

5.2 Journey
✓ Appointment Booked
↓
✓ Arrived
↓
✓ RFID Verified
↓
✓ Checked In
↓
● Waiting for Vaccination
↓
○ Vaccination
↓
○ Record Updated
↓
○ Certificate Generated
5.3 After Vaccination

The timeline automatically updates:

✓ Vaccination Completed
✓ Vaccination Record Updated
✓ Certificate Generated
✓ Next Vaccination Calculated
5.4 Patient Benefit

The parent should always know:

What has happened
What is happening now
What happens next

This reduces uncertainty inside the hospital.

6. Digital Hospital Front Desk
   6.1 Objective

Replace manual receptionist searching with a single operational interface.

6.2 Main Interface
DIGITAL FRONT DESK

[TAP / SCAN RFID]

        ↓

SIYA PATEL

Age:
2 Years

Appointment:
10:30 AM

Vaccine:
MMR

✓ RFID matched
✓ Child matched
✓ Appointment matched
✓ Hospital matched

[CHECK IN]
6.3 Receptionist Workflow
Scan RFID
↓
Identify Family
↓
Identify Children
↓
Find Today's Appointment
↓
Verify
↓
Check In
↓
Add to Queue

Receptionist should not manually enter the child's information.

7. Digital Queue / "I'm Here" Mode
   7.1 Objective

Remove traditional paper/token queue management.

7.2 Patient Flow

Patient arrives.

They scan RFID.

System automatically:

RFID
↓
Appointment
↓
Hospital
↓
Check-in
↓
Queue

Patient sees:

YOU ARE CHECKED IN

Queue Position:
#4

Estimated Waiting:
12 minutes

Status:
WAITING
7.3 Queue States
NOT_ARRIVED
CHECKED_IN
WAITING
CALLED
IN_VACCINATION
COMPLETED
7.4 Receptionist Dashboard
TODAY'S QUEUE

#1 Aarav
10:00 AM
Waiting

#2 Siya
10:30 AM
Vaccination

#3 Kabir
10:45 AM
Not Arrived
7.5 Queue Automation

When the receptionist/staff calls the patient:

WAITING
↓
CALLED

When vaccination begins:

CALLED
↓
IN_VACCINATION

After completion:

IN_VACCINATION
↓
COMPLETED 8. Vaccination Passport
8.1 Objective

Create a child-centric digital vaccination passport.

This should become one of KiddoVax's signature features.

8.2 Example
AARAV'S VACCINATION PASSPORT

Vaccination Progress

████████████░░ 82%

Completed
✓ BCG
✓ OPV
✓ DTaP Dose 1
✓ DTaP Dose 2

Upcoming
● MMR

Next Milestone:
12 Days
8.3 Passport Sections
Overview
Child name
Date of birth
Vaccination progress
Next vaccination
Completed
Vaccine
Dose
Date
Hospital
Upcoming
Vaccine
Due date
Appointment
Certificates
Digital certificate
QR verification 9. QR Certificate Vault
9.1 Objective

Store all vaccination certificates digitally.

9.2 Structure
MY CHILDREN

Aarav
├── Vaccination Passport
├── Certificates
├── History
└── QR Verification

Siya
├── Vaccination Passport
├── Certificates
├── History
└── QR Verification
9.3 QR Verification

Every generated certificate can contain a verification QR.

Scanning it should lead to a secure verification page.

The verification page should reveal only information necessary to confirm authenticity.

9.4 Security

Do not expose sensitive patient information through publicly accessible QR codes.

Use:

Secure verification tokens
Expiring tokens where appropriate
Minimal information
Server-side validation 10. Vaccination Gap Detector
10.1 Objective

Identify possible gaps between the child's recorded vaccination history and the configured vaccination schedule.

10.2 Example
IMMUNIZATION REVIEW

✓ 8 vaccinations recorded

⚠ Possible gap detected

Expected vaccination:
MMR

Status:
Requires review

[VIEW DETAILS]
10.3 Important Rule

The system should not independently make medical decisions.

A gap should be treated as:

Requires review

rather than:

"The child definitely missed this vaccine."

10.4 Hospital Review

Hospital staff can see:

PATIENT REVIEW REQUIRED

Child:
Siya Patel

Potential Gap:
MMR

Action:
Review vaccination history

Authorized medical staff make the final determination.

11. Vaccination Recovery Journey
    11.1 Objective

Help families who have incomplete vaccination records understand the next steps.

11.2 Example
VACCINATION RECOVERY

3 items require review.

Step 1
Review previous records

✓ Completed

Step 2
Hospital review

● Pending

Step 3
Vaccination plan

○ Pending

Step 4
Return to regular schedule

○ Pending
11.3 Medical Safety

KiddoVax must not automatically prescribe a catch-up vaccination schedule.

The platform can:

Identify possible gaps
Collect existing records
Notify the parent
Create a hospital review task
Display an approved schedule after authorized review 12. Smart Walk-in Mode
12.1 Objective

Support patients who arrive without a pre-booked appointment.

12.2 Flow
WALK-IN
↓
RFID / Patient Search
↓
Identify Child
↓
Check Vaccination Requirements
↓
Check Hospital Availability
↓
Create Walk-in Request
↓
Add to Queue
12.3 Receptionist Screen
WALK-IN PATIENT

Child:
Aarav Patel

Vaccination:
MMR

Status:
No appointment

Available options:

10:45 AM
11:15 AM
11:40 AM

[ADD TO QUEUE] 13. Hospital Vaccination Session Mode
13.1 Objective

Allow hospitals to organize vaccination operations around sessions rather than isolated appointments.

13.2 Session Example
MMR VACCINATION SESSION

Date:
18 August

Time:
09:00–12:00

Capacity:
40

Booked:
32

Checked-in:
21

Completed:
18

Waiting:
3
13.3 Session Management

Hospital staff can:

Create session
Define capacity
Select vaccines
Define date
Define time
Monitor attendance
Monitor completion
Close session
13.4 Integration

Appointments should belong to sessions where applicable.

Session
↓
Appointments
↓
RFID Check-ins
↓
Vaccinations 14. Hospital Capacity Heatmap
14.1 Objective

Show hospitals when patient demand is highest.

14.2 Example
EXPECTED PATIENT LOAD

08 AM ░░
09 AM ███
10 AM █████
11 AM ██████
12 PM ████
01 PM ██
02 PM █
14.3 Uses

Hospital can use this to:

Adjust appointment capacity
Plan staffing
Open additional vaccination sessions
Reduce waiting time 15. Hospital Operational Profile
15.1 Objective

Provide useful operational information when patients choose hospitals.

15.2 Example
ABC HOSPITAL

Vaccination Centre

Distance:
2.4 km

Next Available:
10:30 AM

Today's Availability:
HIGH

Vaccines Available:
✓ MMR
✓ DTP
✓ Hepatitis B

Average Check-in:
4 minutes
15.3 Data Rules

Only show data that actually exists in the system.

Do not invent:

Ratings
Waiting times
Vaccine availability
Hospital performance 16. Child Vaccination Milestones
16.1 Objective

Make vaccination progress engaging for parents.

16.2 Milestones

Examples:

🏆 First Vaccination
🏆 5 Vaccinations Completed
🏆 Vaccination Journey Started
🏆 On-Time Appointment
🏆 Major Milestone Completed
16.3 Important Rule

Do not gamify medical decisions.

Rewards should represent:

Record completion
Journey progress
Appointment adherence
Educational milestones

Never:

"Take more vaccines to earn points."

17. Child Growth & Preventive-Care Timeline
    17.1 Objective

Give parents a broader preventive-care view without turning KiddoVax into a complete hospital EMR.

17.2 Example
AARAV

AGE:
18 Months

IMMUNIZATION
██████████░ 85%

GROWTH
Height
Weight
Growth History

PREVENTIVE CARE
Vaccinations
Appointments
Documents
17.3 Data Entry

Authorized hospital staff may record appropriate growth information.

The system should maintain historical records.

AI may summarize trends but must not diagnose conditions.

18. Family Health Timeline
    18.1 Objective

Give parents one chronological view of their family's KiddoVax activity.

18.2 Example
2026

JAN
✓ Aarav — Vaccination

MAR
✓ Siya — Vaccination

JUN
✓ Hospital Visit

AUG
● Siya — MMR Appointment

SEP
○ Upcoming Milestone 19. Child Switching System
19.1 Objective

Parents with multiple children must be able to switch context easily.

19.2 Global Selector
CURRENT CHILD

[Aarav ▼]

Options:

Aarav
Siya
Kabir
19.3 Context Switching

When the child changes:

Vaccination History
Appointments
Certificates
Passport
Journey
Notifications
Progress

must update automatically.

20. Parent Feedback System
    20.1 Objective

Collect feedback immediately after a hospital visit.

20.2 Example
HOW WAS YOUR VISIT?

Check-in
★★★★★

Waiting Time
★★★★☆

Staff
★★★★★

Vaccination Process
★★★★★

Overall
★★★★★

Additional Feedback
[________________]
20.3 Hospital Dashboard

Hospital can see:

MONTHLY FEEDBACK

Overall:
4.6 / 5

Check-in:
4.8

Waiting:
4.1

Staff:
4.7 21. RFID Incident Centre
21.1 Objective

Allow administrators to monitor RFID problems.

21.2 Incident Types
Unknown RFID
Duplicate RFID
Inactive RFID
Wrong Hospital
Wrong Appointment
Failed Verification
Repeated Failed Scans
21.3 Incident Example
RFID INCIDENT

RFID:
10384721

Hospital:
ABC Hospital

Time:
10:31 AM

Issue:
Appointment belongs to another hospital.

Status:
OPEN

[REVIEW]
21.4 Admin Actions

Authorized admins may:

Review
Resolve
Deactivate RFID
Reassign RFID where appropriate
Add internal notes
View history 22. Admin Vaccination Command Centre
22.1 Objective

Provide a system-wide operational overview.

22.2 Dashboard
KIDDO VAX COMMAND CENTRE

TODAY

Patients Registered
142

Appointments
96

Checked In
71

Vaccinations Completed
63
22.3 RFID Statistics
Active RFID:
1,284

New Assignments:
32

Failed Scans:
7
22.4 Hospital Statistics
Active Hospitals:
24

High Load:
5

Low Activity:
3
22.5 Vaccine Overview
Potential Inventory Risks:
4

High Demand Vaccines:
3 23. Admin Access Control

All new features must follow role-based access.

Patient

Can access:

Own children
Own appointments
Own RFID information
Own vaccination history
Own certificates
Own journey
Receptionist

Can access:

Authorized hospital patients
Appointments
RFID verification
Queue
Check-in
Vaccination workflow
Hospital Admin

Can access:

Hospital data
Sessions
Inventory
Queue analytics
Staff workflows
Hospital operational profile
System Admin

Can access:

All hospitals
RFID management
System-wide analytics
Incident centre
Configuration
Audit logs 24. Feature Integration With Existing AI

These new features should work alongside the existing AI functionality.

Existing AI may handle:

Patient assistance
Hospital recommendations
Appointment assistance
Queue intelligence
Inventory prediction
Demand forecasting
Receptionist assistance

New features should provide the product workflow and user experience around those AI capabilities.

Do not create duplicate AI systems.

Example:

Smart Hospital Recommendation
↓
Existing AI ranking
↓
New Hospital Operational Profile
↓
Patient chooses hospital 25. Feature Integration With RFID

The central RFID workflow remains:

RFID
↓
Family
↓
Children
↓
Appointment
↓
Hospital
↓
Check-in
↓
Queue
↓
Vaccination
↓
Second RFID Scan
↓
Completion

New features must integrate with this flow rather than creating a separate RFID workflow.

26. Data Relationships

Conceptually:

User
│
├── RFID
│
├── Children
│ │
│ ├── Vaccination Records
│ ├── Appointments
│ ├── Certificates
│ ├── Growth Records
│ └── Vaccination Journey
│
└── Notifications

Hospital
│
├── Receptionists
├── Vaccination Sessions
├── Inventory
├── Appointments
├── Queue
└── Operational Data 27. Real-Time Requirements

The following should update in near real time where possible:

Queue position
Check-in status
Appointment status
Vaccination status
RFID verification
Vaccination completion
Hospital session capacity

If the existing architecture already uses WebSockets, Firebase Realtime Database, Supabase Realtime, or another real-time mechanism, reuse it.

Do not introduce a second real-time architecture unnecessarily.

28. Offline / Failure Handling

The system should handle temporary failures gracefully.

If AI fails:

Core application continues.

If RFID service fails:

Receptionist can use authorized fallback verification.

If notification service fails:

Appointment and vaccination data remain intact.

If real-time updates fail:

Page can fall back to periodic refresh.

No external AI or notification failure should corrupt medical records.

29. Security Requirements

All new features must maintain:

Authentication
Role-based authorization
Data isolation
Audit logging
Secure API access
Secure RFID handling
Secure QR verification
Secure certificate access

Never expose:

Passwords
Internal tokens
Private medical information
Unauthorized patient data

through public interfaces.

30. UI Requirements

The existing KiddoVax UI must remain the visual foundation.

New features must:

Use the existing theme
Use existing colors
Use existing typography
Use existing spacing
Use existing cards/components where possible
Maintain responsive behavior
Maintain mobile usability
Avoid introducing an unrelated design language

New functionality should feel like it was always part of KiddoVax.

31. Implementation Rules

Before implementation:

Inspect the entire existing codebase.
Identify existing models.
Identify existing APIs.
Identify existing RFID functionality.
Identify existing appointment functionality.
Identify existing vaccination records.
Identify existing AI functionality.
Identify existing hospital/receptionist workflows.
Identify duplicate functionality.
Create an implementation plan.

Then implement feature-by-feature.

32. Overlap Handling

If a feature already exists:

If it is complete

Reuse it.

If it partially exists

Extend it.

If the existing implementation conflicts with this PRD

Refactor it carefully.

If two features overlap

Merge them into one stronger implementation.

Do not create:

AI Queue

- Another AI Queue
- Third Queue System

Instead create:

Unified Queue Intelligence 33. Testing Requirements

Every feature must be tested across relevant portals.

RFID

Test:

Valid RFID
Unknown RFID
Duplicate RFID
Inactive RFID
Multiple children
Wrong hospital
Wrong appointment
First scan
Second scan
Patient

Test:

Single child
Multiple children
Appointment
Passport
Certificate
Journey
Notifications
Receptionist

Test:

Check-in
Queue
Walk-in
Vaccination completion
Hospital

Test:

Session
Capacity
Inventory
Operational dashboard
Admin

Test:

RFID incidents
Command centre
Access control 34. Success Metrics

KiddoVax should measure whether these features actually improve the product.

Patient
Appointment completion rate
Average booking time
Hospital selection time
Missed appointment rate
Passport usage
Certificate usage
Parent satisfaction
Receptionist
Average check-in time
Manual searches
RFID verification time
Queue processing time
Average patient waiting time
Hospital
Session utilization
Vaccination throughput
Average waiting time
Inventory shortage incidents
Walk-in processing time
Platform
Active users
Active RFID devices
Vaccinations completed
Hospital adoption
Successful RFID scans
Failed RFID scans 35. Final Product Experience

The finished KiddoVax experience should feel like this:

PARENT
│
▼
Family Dashboard
│
├── Children
├── Vaccination Passport
├── Journey
├── Appointments
├── Certificates
└── RFID
│
▼
HOSPITAL
│
▼
RFID SCAN
│
▼
DIGITAL FRONT DESK
│
▼
CHECK-IN
│
▼
DIGITAL QUEUE
│
▼
VACCINATION
│
▼
RFID SCAN
│
▼
COMPLETION
│
▼
DIGITAL PASSPORT
│
▼
CERTIFICATE
│
▼
NEXT MILESTONE

The AI layer surrounds this workflow:

                    KIDDO VAX
                        │
       ┌────────────────┼────────────────┐
       │                │                │
    PATIENT         RECEPTIONIST       HOSPITAL
       │                │                │
       ▼                ▼                ▼

AI Journey AI Verification AI Inventory
AI Assistant AI Queue AI Forecast
AI Booking AI Copilot AI Operations
│ │ │
└────────────────┼────────────────┘
│
▼
RFID + CORE DATA
│
▼
VACCINATION WORKFLOW 36. Final Product Principle

KiddoVax should ultimately solve one simple problem:

Make the entire child vaccination journey easy for the parent and effortless for the hospital.

The parent should not have to understand the hospital's internal process.

The receptionist should not have to manually search through records.

The hospital should not have to manually analyze every operational metric.

The administrator should have complete visibility.

And the RFID should connect the physical patient journey to the digital KiddoVax journey.

The system should make the vaccination process feel like one continuous journey rather than a collection of disconnected screens.
