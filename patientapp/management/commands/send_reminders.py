import datetime
from django.core.management.base import BaseCommand  # type: ignore[import]  # pyre-ignore
from ...models import Appointmenttbl, Childtbl, Notification  # type: ignore[import]  # pyre-ignore
from ...utils import send_sms  # type: ignore[import]  # pyre-ignore
from ...vaccine_recommender import get_missed_vaccines  # type: ignore[import]  # pyre-ignore

class Command(BaseCommand):
    help = 'Sends SMS and In-App notifications for upcoming appointments and missed vaccines.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.HTTP_INFO("--- Starting KiddoVax Reminder Scheduler ---"))
        
        # ---------------------------------------------------------
        # 1. Upcoming Appointment Reminders (Tomorrow)
        #    Uses reminder_sent flag on the appointment itself for
        #    lightweight deduplication (no Notification table lookup).
        # ---------------------------------------------------------
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        
        # Only pending (0) or waiting (1) appointments
        upcoming_apts = Appointmenttbl.objects.filter(
            aptdate=tomorrow,
            active__in=[0, 1],
            reminder_sent=False          # <-- dedup guard
        ).select_related('patientid', 'vaccineid', 'hospitalid', 'child')

        apt_count: int = 0
        for apt in upcoming_apts:
            if not apt.patientid:
                continue

            child_name = apt.child.childname if apt.child else (apt.childname or "your child")
            vaccine_name = apt.vaccineid.vaccineName
            apt_date_str = tomorrow.strftime('%b %d, %Y')

            # Interactive two-way SMS — patient replies YES or NO
            sms_msg = (
                f"KiddoVax Reminder: '{child_name}' has a {vaccine_name} appointment "
                f"tomorrow ({apt_date_str}). "
                f"Reply YES to confirm or NO to cancel."
            )

            # 1a. In-App notification (also shown in notification bell)
            Notification.objects.create(
                patient=apt.patientid,
                message=sms_msg,
                notification_type='appointment',
                related_id=apt.id
            )

            # 1b. SMS dispatch
            if apt.patientid.contactNo:
                send_sms(apt.patientid.contactNo, sms_msg)

            # 1c. Mark reminder as sent so this appointment is never re-notified
            apt.reminder_sent = True
            apt.save(update_fields=['reminder_sent'])

            apt_count += 1

        self.stdout.write(self.style.SUCCESS(f"Processed {apt_count} appointment reminders for tomorrow."))

        # ---------------------------------------------------------
        # 2. Missed Vaccine Alerts (unchanged)
        # ---------------------------------------------------------
        children = Childtbl.objects.select_related('patient').all()
        vac_count: int = 0
        
        for child in children:
            if not child.patient:
                continue
                
            exists = Notification.objects.filter(
                notification_type='vaccine',
                related_id=child.id
            ).exists()
            
            if exists:
                continue

            missed_data = get_missed_vaccines(child.id)
            if missed_data.get('total_missed', 0) > 0:
                missed_count = missed_data['total_missed']
                
                msg = (
                    f"KiddoVax Alert: '{child.childname}' is missing {missed_count} "
                    f"due routine vaccines. Please log in to review and book."
                )
                
                Notification.objects.create(
                    patient=child.patient,
                    message=msg,
                    notification_type='vaccine',
                    related_id=child.id
                )
                
                if child.patient.contactNo:
                    send_sms(child.patient.contactNo, msg)
                    
                vac_count += 1  # pyre-ignore[58]
                
        self.stdout.write(self.style.SUCCESS(f"Processed {vac_count} missed vaccine alerts."))
        self.stdout.write(self.style.HTTP_INFO("--- Scheduler finished successfully ---"))
