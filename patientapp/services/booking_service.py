import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from hospitalapp.models import Hospitaltbl, HospitalBreak, HospitalHoliday
from patientapp.models import Appointmenttbl


def generate_hospital_time_slots(hospital_id: int, date_val: datetime.date) -> list:
    """
    Dynamically generates time slots for a hospital on a given date.
    Returns a list of dicts:
    [
        {
            'time_str': '09:00 AM',
            'time_val': '09:00:00',
            'status': 'AVAILABLE' | 'FULL' | 'BREAK' | 'HOLIDAY',
            'booked': 1,
            'capacity': 2
        },
        ...
    ]
    """
    try:
        hospital = Hospitaltbl.objects.get(pk=hospital_id)
    except Hospitaltbl.DoesNotExist:
        return []

    # 1. Check if closed/holiday on this date
    if HospitalHoliday.objects.filter(hospital=hospital, date=date_val).exists():
        holiday = HospitalHoliday.objects.filter(hospital=hospital, date=date_val).first()
        return [{
            'time_str': 'Closed',
            'time_val': None,
            'status': 'HOLIDAY',
            'reason': holiday.description or 'Hospital Closed on this date',
            'booked': 0,
            'capacity': hospital.slot_capacity
        }]

    opening = hospital.opening_time or datetime.time(9, 0)
    closing = hospital.closing_time or datetime.time(17, 0)
    duration = hospital.slot_duration if hospital.slot_duration and hospital.slot_duration > 0 else 30
    capacity = 5  # Maximum 5 appointments per time slot

    # Fetch configured break periods
    breaks = list(HospitalBreak.objects.filter(hospital=hospital))

    # Fetch existing non-cancelled bookings for this date (5 = CANCELLED)
    existing_bookings = Appointmenttbl.objects.filter(
        hospitalid=hospital,
        aptdate=date_val
    ).exclude(active=Appointmenttbl.STATUS_CANCELLED)

    # Map booked count by time
    booked_counts = {}
    for apt in existing_bookings:
        if apt.apttime:
            time_key = apt.apttime.strftime('%H:%M:%S')
            booked_counts[time_key] = booked_counts.get(time_key, 0) + 1

    slots = []
    current_dt = datetime.datetime.combine(date_val, opening)
    end_dt = datetime.datetime.combine(date_val, closing)

    while current_dt + datetime.timedelta(minutes=duration) <= end_dt:
        slot_start_time = current_dt.time()
        slot_end_time = (current_dt + datetime.timedelta(minutes=duration)).time()
        time_key = slot_start_time.strftime('%H:%M:%S')

        # Check break period
        is_break = False
        for brk in breaks:
            if brk.start_time <= slot_start_time < brk.end_time:
                is_break = True
                break

        if is_break:
            slots.append({
                'time_str': current_dt.strftime('%I:%M %p'),
                'time_val': time_key,
                'status': 'BREAK',
                'booked': 0,
                'capacity': capacity
            })
        else:
            booked = booked_counts.get(time_key, 0)
            status = 'FULL' if booked >= capacity else 'AVAILABLE'
            
            slots.append({
                'time_str': current_dt.strftime('%I:%M %p'),
                'time_val': time_key,
                'status': status,
                'booked': booked,
                'capacity': capacity
            })

        current_dt += datetime.timedelta(minutes=duration)

    return slots


def validate_and_reserve_slot(hospital_id: int, date_val: datetime.date, time_val: datetime.time) -> bool:
    """
    Validates server-side that the requested slot is available and does not exceed 5 appointment capacity.
    Executes inside an atomic transaction with row locks to prevent double booking.
    Raises ValidationError if unavailable or full.
    """
    try:
        hospital = Hospitaltbl.objects.get(pk=hospital_id)
    except Hospitaltbl.DoesNotExist:
        raise ValidationError("Invalid hospital specified.")

    if not time_val:
        # Legacy date-only appointment fallback
        return True

    # Holiday check
    if HospitalHoliday.objects.filter(hospital=hospital, date=date_val).exists():
        raise ValidationError("Selected hospital is closed on this date.")

    # Break check
    breaks = HospitalBreak.objects.filter(hospital=hospital)
    for brk in breaks:
        if brk.start_time <= time_val < brk.end_time:
            raise ValidationError("Selected time slot falls within a hospital break period.")

    capacity = 5  # Maximum 5 appointments per time slot

    # Lock existing appointments for update in this transaction
    with transaction.atomic():
        booked_count = Appointmenttbl.objects.select_for_update().filter(
            hospitalid=hospital,
            aptdate=date_val,
            apttime=time_val
        ).exclude(active=Appointmenttbl.STATUS_CANCELLED).count()

        if booked_count >= capacity:
            raise ValidationError(f"The selected time slot ({time_val.strftime('%I:%M %p')}) is fully booked (5/5 capacity reached). Please select another time or date.")

    return True
