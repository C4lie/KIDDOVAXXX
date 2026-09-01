from django.shortcuts import render, redirect, get_object_or_404  # type: ignore[import]  # pyre-ignore
from django.http import JsonResponse  # type: ignore[import]  # pyre-ignore
from django.views.decorators.csrf import csrf_exempt  # type: ignore[import]  # pyre-ignore
from patientapp.forms import PatientForm, AppointmentForm  # type: ignore[import]  # pyre-ignore
from django.views  import View  # type: ignore[import]  # pyre-ignore
from django.contrib import messages  # type: ignore[import]  # pyre-ignore
from adminapp.models import City,Area  # type: ignore[import]  # pyre-ignore
from patientapp.models import Patienttbl, Appointmenttbl, Childtbl, VaccinationRecord  # type: ignore[import]  # pyre-ignore
from hospitalapp.models import Vaccinetbl, Hospitaltbl  # type: ignore[import]  # pyre-ignore
from django.contrib.auth import logout
from django.contrib.auth.hashers import make_password, check_password  # type: ignore[import]  # pyre-ignore
def Home(request):
    return render(request, 'patientapp/home.html')

def About(request):
    return render(request, 'patientapp/about.html')

def Contact(request):
    return render(request, 'patientapp/contact.html')


class PatientLogout(View):
    def get(self, request):
        logout(request)
        request.session.flush()
        return render(request, 'patientapp/home.html')

class PatientLogin(View):
    def get(self, request):
        form = PatientForm()
        context={
            'form' : form
        }
        return render(request, 'patientapp/login.html',context)
    def post(self, request):
        contact = str(request.POST.get('contactno', '')).strip()
        password = str(request.POST.get('password', '')).strip()

        try:
            patient = Patienttbl.objects.get(contactNo=contact)
        except Patienttbl.DoesNotExist:
            patient = None

        if patient is not None:
            # Support both hashed and legacy plain-text passwords
            password_valid = check_password(password, patient.password)
            if not password_valid:
                # Fallback: check plain text for any un-migrated accounts
                password_valid = (patient.password == password)
                if password_valid:
                    # Upgrade to hashed password on successful plain-text login
                    patient.password = make_password(password)
                    patient.save(update_fields=['password'])

            if password_valid:
                request.session['CName'] = patient.name
                request.session['Cid'] = patient.id
                request.session['user_role'] = 'patient'

                # Check account lifecycle
                if patient.must_change_password:
                    return redirect('patient:force_password_change')
                if patient.account_status == 'PENDING_HOSPITAL_REGISTRATION':
                    return redirect('patient:pending_registration')

                return redirect('patient:homepage')
            else:
                messages.info(request, 'Invalid Password')
        else:
            messages.info(request, 'Invalid Contact Number')

        return render(request, 'patientapp/login.html')  


class PatientRegistration(View):
    def get(self, request):
        bindCity = City.objects.all().order_by('-id')
        bindData = Patienttbl.objects.select_related("cityId").select_related("areaId").all().order_by('-id')
        form = PatientForm()
        context={
                'cityData' : bindCity,
                'form' : form
        }
        return render(request, 'patientapp/register.html',context)
    def post(self,request):
        form = PatientForm(request.POST)
        contact  = request.POST['contactNo']

        if Patienttbl.objects.filter(contactNo=contact).exists():
            messages.info(request, 'Contact Number is already taken')
            return redirect('patient:registerpage')
        else:
            if form.is_valid():
                patient = form.save(commit=False)
                # Hash the password before saving
                patient.password = make_password(patient.password)
                patient.account_status = 'PENDING_HOSPITAL_REGISTRATION'
                patient.must_change_password = True
                patient.save()
                messages.info(request, "Your registration is success! Please visit your nearest hospital to complete setup and receive your RFID device.")
        return redirect('patient:loginpage')  
    
class BookedAppointment(View):
    def get(self, request, aid=None):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None or request.session.get('user_role') != 'patient':
            return redirect('patient:loginpage')

        if aid is not None:
            data = Appointmenttbl.objects.get(pk = aid)
            data.delete()
            aid = None
            messages.info(request,'Appointment Deleted Success!')
            return redirect('patient:vaccinebooking') 
        
        # 1. Fetch patient profile & location coordinates
        patient = Patienttbl.objects.filter(id=request.session.get('Cid')).first()
        user_lat = request.GET.get('lat')
        user_lng = request.GET.get('lng')

        if user_lat and user_lng:
            try:
                user_lat = float(user_lat)
                user_lng = float(user_lng)
            except ValueError:
                user_lat, user_lng = None, None

        if user_lat is None and patient and patient.latitude:
            user_lat = patient.latitude
            user_lng = patient.longitude

        # Fallback to city/area geocoding if user coordinates still missing
        if user_lat is None and patient:
            from patientapp.services.geocoding_service import geocode_location
            area_name = patient.areaId.areaName if patient.areaId else None
            city_name = patient.cityId.cityName if patient.cityId else None
            user_lat, user_lng = geocode_location(area_name, city_name)

        # 2. Recommended & sorted hospitals list
        from patientapp.services.geocoding_service import sort_hospitals_by_recommendation
        all_hospitals = Hospitaltbl.objects.all().select_related('cityId', 'areaId').order_by('-id')
        recommended_hospitals = sort_hospitals_by_recommendation(
            all_hospitals,
            user_lat=user_lat,
            user_lng=user_lng
        )

        form = AppointmentForm()
        children = Childtbl.objects.filter(patient_id=request.session.get('Cid')).order_by('dob')
        bindData = Appointmenttbl.objects.select_related("hospitalid", "vaccineid").filter(patientid_id=request.session.get('Cid')).order_by('-id')

        # 3. Initial hospital & vaccines for immediate HTML dropdown population
        prefill_vaccine = request.GET.get('vaccine') or ''
        prefill_child_id = request.GET.get('child') or request.GET.get('child_id') or ''
        prefill_hospital_id = request.GET.get('hospital_id') or request.GET.get('hospitalid') or ''

        initial_hospital_id = prefill_hospital_id if prefill_hospital_id and prefill_hospital_id.isdigit() else None
        if not initial_hospital_id and recommended_hospitals:
            initial_hospital_id = recommended_hospitals[0]['hospital'].id

        if initial_hospital_id:
            initial_vaccines = Vaccinetbl.objects.filter(hospitalId_id=initial_hospital_id).order_by('vaccineName')
        else:
            initial_vaccines = Vaccinetbl.objects.all().order_by('vaccineName')

        # Filter out vaccines that the child already has booked in an active state by vaccineName (except prefill_vaccine)
        target_child_id = prefill_child_id if prefill_child_id and prefill_child_id.isdigit() else (children.first().id if children.exists() else None)
        if target_child_id:
            target_child = Childtbl.objects.filter(pk=target_child_id).first()
            if target_child:
                from django.db import models
                booked_names = list(Appointmenttbl.objects.filter(
                    models.Q(child_id=target_child.pk) | models.Q(childname__iexact=target_child.childname)
                ).exclude(active=Appointmenttbl.STATUS_CANCELLED).values_list('vaccineid__vaccineName', flat=True))
                if booked_names:
                    if prefill_vaccine:
                        booked_names = [b for b in booked_names if b and prefill_vaccine.lower() not in b.lower()]
                    if booked_names:
                        initial_vaccines = initial_vaccines.exclude(vaccineName__in=booked_names)

        initial_vaccines_list = list(initial_vaccines)
        for v in initial_vaccines_list:
            if prefill_vaccine and prefill_vaccine.lower() in v.vaccineName.lower():
                v.is_prefilled = True
            else:
                v.is_prefilled = False

        context = {
            'hospitalData': [item['hospital'] for item in recommended_hospitals],
            'recommended_hospitals': recommended_hospitals,
            'user_lat': user_lat,
            'user_lng': user_lng,
            'form': form,
            'bindData': bindData,
            'children': children,
            'initial_vaccines': initial_vaccines_list,
            'prefill_vaccine': prefill_vaccine,
            'prefill_child_id': prefill_child_id,
            'prefill_hospital_id': prefill_hospital_id
        }
        return render(request, 'patientapp/bookvaccine.html', context)

    def post(self, request):
        form = AppointmentForm(request.POST)
        if form.is_valid():
            data = form.save(commit=False)
            hospital_id = request.POST.get('hospitalid')
            data.childname = request.POST.get('childname')
            data.hospitalid_id = hospital_id
            data.vaccineid_id = request.POST.get('vaccineid')
            data.patientid_id = request.session['Cid']
            
            aptdate_str = request.POST.get('aptdate')
            apttime_str = request.POST.get('apttime')
            
            aptdate_val = _parse_date(aptdate_str)
            if not aptdate_val:
                messages.error(request, "Invalid appointment date specified.")
                return redirect('patient:vaccinebooking')

            apttime_val = None
            if apttime_str:
                for fmt in ('%H:%M:%S', '%H:%M', '%I:%M %p'):
                    try:
                        apttime_val = datetime.datetime.strptime(apttime_str, fmt).time()
                        break
                    except ValueError:
                        pass

            child_id = request.POST.get('child_id')
            vaccine_id = request.POST.get('vaccineid')
            if child_id and child_id.isdigit() and vaccine_id and vaccine_id.isdigit():
                selected_vac = Vaccinetbl.objects.filter(pk=int(vaccine_id)).first()
                child_obj = Childtbl.objects.filter(pk=int(child_id)).first()
                if selected_vac and child_obj:
                    from django.db import models
                    existing_dup = Appointmenttbl.objects.filter(
                        models.Q(child_id=child_obj.pk) | models.Q(childname__iexact=child_obj.childname),
                        vaccineid__vaccineName__iexact=selected_vac.vaccineName
                    ).exclude(active=Appointmenttbl.STATUS_CANCELLED).first()
                    
                    if existing_dup:
                        messages.error(request, f"This child already has an active appointment for {selected_vac.vaccineName}.")
                        return redirect('patient:vaccinebooking')

            # Validate server-side slot availability & capacity with row-locking
            from patientapp.services.booking_service import validate_and_reserve_slot
            from django.core.exceptions import ValidationError
            try:
                validate_and_reserve_slot(int(hospital_id), aptdate_val, apttime_val)
            except ValidationError as ve:
                messages.error(request, str(ve.message if hasattr(ve, 'message') else ve))
                return redirect('patient:vaccinebooking')

            data.aptdate = aptdate_val
            data.apttime = apttime_val
            data.active = 0
            
            if child_id and child_id.isdigit():
                data.child_id = int(child_id)
            data.save()
            
            messages.info(request, f"Your appointment for {aptdate_val.strftime('%d %b %Y')}" + 
                          (f" at {apttime_val.strftime('%I:%M %p')}" if apttime_val else "") + " is successfully booked!")
            return redirect('patient:vaccinebooking')
        else:
            messages.error(request, "Failed to book appointment. Check that all fields are selected.")
            return redirect('patient:vaccinebooking')


def _parse_date(date_str):
    """Parses date string supporting %Y-%m-%d, %d-%m-%Y, %d/%m/%Y, and %Y/%m/%d."""
    if not date_str:
        return None
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            return datetime.datetime.strptime(str(date_str).strip(), fmt).date()
        except ValueError:
            pass
    return None


def get_available_slots(request):
    """GET /get-slots/?h_id=X&date=YYYY-MM-DD (or DD-MM-YYYY)
    Returns dynamic time slots for a hospital and date.
    """
    hospital_id = request.GET.get('h_id')
    date_str = request.GET.get('date')
    if not hospital_id or not date_str:
        return JsonResponse({'slots': []})

    try:
        date_val = _parse_date(date_str)
        if not date_val:
            return JsonResponse({'slots': [], 'error': 'Invalid date format'})
        from patientapp.services.booking_service import generate_hospital_time_slots
        slots = generate_hospital_time_slots(int(hospital_id), date_val)
        return JsonResponse({'slots': slots})
    except Exception as e:
        return JsonResponse({'slots': [], 'error': str(e)})


def get_hospitals_for_date(request):
    """GET /get-hospitals-for-date/?date=YYYY-MM-DD
    Returns only hospitals available on the specified date (excluding closed/holiday hospitals).
    """
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'hospitals': []})

    try:
        date_val = _parse_date(date_str)
        if not date_val:
            return JsonResponse({'hospitals': [], 'error': 'Invalid date format'})
        from hospitalapp.models import HospitalHoliday, Hospitaltbl
        
        # Exclude hospitals on holiday on this date
        holiday_hospital_ids = HospitalHoliday.objects.filter(date=date_val).values_list('hospital_id', flat=True)
        hospitals = Hospitaltbl.objects.exclude(id__in=holiday_hospital_ids).select_related('cityId', 'areaId').order_by('title')

        # Distance sorting if user location is available
        patient = Patienttbl.objects.filter(id=request.session.get('Cid')).first() if request.session.get('Cid') else None
        user_lat = request.GET.get('lat') or (patient.latitude if patient else None)
        user_lng = request.GET.get('lng') or (patient.longitude if patient else None)

        if user_lat and user_lng:
            from patientapp.services.geocoding_service import sort_hospitals_by_recommendation
            recommended = sort_hospitals_by_recommendation(hospitals, user_lat=float(user_lat), user_lng=float(user_lng))
            data = [
                {
                    'id': item['hospital'].id,
                    'title': item['hospital'].title,
                    'distance_km': item['distance_km'],
                    'is_nearest': item['is_nearest']
                }
                for item in recommended
            ]
        else:
            data = [
                {
                    'id': h.id,
                    'title': h.title,
                    'distance_km': None,
                    'is_nearest': False
                }
                for h in hospitals
            ]

        return JsonResponse({'hospitals': data})
    except Exception as e:
        return JsonResponse({'hospitals': [], 'error': str(e)})


def update_location(request):
    """POST /update-location/
    Updates patient's latitude and longitude from browser geolocation.
    """
    if request.method == 'POST' and request.session.get('Cid'):
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        try:
            patient = Patienttbl.objects.get(id=request.session.get('Cid'))
            patient.latitude = float(lat)
            patient.longitude = float(lng)
            patient.save(update_fields=['latitude', 'longitude'])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=400)


def load_vaccinebyhospital(request, h_id=None):
    if h_id is not None:
        # Called internally — no child filtering needed here
        vaccines = Vaccinetbl.objects.filter(hospitalId=h_id).order_by('-id')
        return vaccines
    else:
        h_id = request.GET.get('h_id')
        child_id = request.GET.get('child_id')  # optional param from booking form
        prefill_vaccine = (request.GET.get('vaccine') or '').strip()
        vlist = Vaccinetbl.objects.filter(hospitalId=h_id).order_by('vaccineName')
        # Exclude vaccines this child has already booked or taken by vaccineName (except prefill_vaccine)
        if child_id and child_id.isdigit():
            child_obj = Childtbl.objects.filter(pk=int(child_id)).first()
            if child_obj:
                from django.db import models
                booked_names = list(Appointmenttbl.objects.filter(
                    models.Q(child_id=child_obj.pk) | models.Q(childname__iexact=child_obj.childname)
                ).exclude(active=Appointmenttbl.STATUS_CANCELLED).values_list('vaccineid__vaccineName', flat=True))
                if booked_names:
                    if prefill_vaccine:
                        booked_names = [b for b in booked_names if b and prefill_vaccine.lower() not in b.lower()]
                    if booked_names:
                        vlist = vlist.exclude(vaccineName__in=booked_names)

        vaccines_list = list(vlist)
        for v in vaccines_list:
            if prefill_vaccine and prefill_vaccine.lower() in v.vaccineName.lower():
                v.is_prefilled = True
            else:
                v.is_prefilled = False

        return render(request, 'patientapp/hospitaltovaccine.html', {'vaccinelist': vaccines_list, 'prefill_vaccine': prefill_vaccine})


def recommend_vaccines(request):
    """GET /recommend-vaccines/?child_id=X&hospital_id=Y
    Returns a JSON list of compulsory age-appropriate vaccines due from birth up to child's current age.
    """
    from patientapp.vaccine_recommender import get_recommended_vaccines  # type: ignore[import]  # pyre-ignore
    child_id = request.GET.get('child_id', '')
    hospital_id = request.GET.get('hospital_id', '')

    if not child_id or not child_id.isdigit():
        return JsonResponse({
            'vaccines': [],
            'message': 'Select a child profile above to view AI smart recommendations.'
        })

    h_id = int(hospital_id) if (hospital_id and hospital_id.isdigit()) else None
    recs = get_recommended_vaccines(int(child_id), h_id)

    data = [
        {
            'id': v.pk,
            'name': v.vaccineName,
            'description': getattr(v, 'schedule_desc', '') or getattr(v, 'vaccineDescr', '') or 'Compulsory dose due for child',
            'due_stage': getattr(v, 'due_stage', 'Compulsory'),
            'price': v.price if v.price is not None else 0
        }
        for v in recs
    ]

    msg = '' if data else 'All compulsory vaccines for this child up to current age are up to date!'
    return JsonResponse({'vaccines': data, 'message': msg})


def missed_vaccines(request):
    """GET /missed-vaccines/?child_id=X
    Detects vaccines a child should have received but hasn't, based on age schedule.
    Returns a JSON dict with missed vaccine list, per-item severity, and overall severity.
    Returns empty result safely on any error.
    """
    from patientapp.vaccine_recommender import get_missed_vaccines  # type: ignore[import]  # pyre-ignore
    child_id = request.GET.get('child_id', '')
    if not child_id.isdigit():
        return JsonResponse({'missed': [], 'total_missed': 0, 'overall_severity': 'none'})
    result = get_missed_vaccines(int(child_id))
    return JsonResponse(result)


def get_notifications(request):
    """GET /notifications/
    Returns the user's unread notifications.
    """
    if request.session.get('Cid') is None:
        return JsonResponse({'notifications': [], 'unread_count': 0})
    
    from patientapp.models import Notification  # type: ignore[import]  # pyre-ignore
    patient_id = request.session.get('Cid')
    notifs = Notification.objects.filter(patient_id=patient_id).order_by('-created_at')[:10]
    
    data = [
        {
            'id': n.id,
            'message': n.message,
            'type': n.notification_type,
            'is_read': n.is_read,
            'date': n.created_at.strftime('%b %d, %Y')
        }
        for n in notifs
    ]
    unread_count = sum(1 for n in data if not n['is_read'])
    
    return JsonResponse({'notifications': data, 'unread_count': unread_count})


def mark_notifications_read(request):
    """POST /notifications/read/
    Marks all notifications for the user as read.
    """
    if request.method == 'POST' and request.session.get('Cid'):
        from patientapp.models import Notification  # type: ignore[import]  # pyre-ignore
        Notification.objects.filter(patient_id=request.session.get('Cid'), is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


def sms_response(request):
    """
    POST /sms-response/
    A webhook-style endpoint that SMS gateways (e.g. Fast2SMS, Twilio) call when a patient
    replies to their reminder SMS with YES or NO.

    Expected POST body params:
        phone   — patient's registered contact number
        message — patient's reply text (YES / NO, case-insensitive)

    Responses (JSON):
        {status: 'confirmed' | 'cancelled' | 'not_found' | 'unknown_reply' | 'invalid'}
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'invalid', 'detail': 'Only POST allowed.'}, status=405)

    phone   = request.POST.get('phone', '').strip()
    reply   = request.POST.get('message', '').strip().upper()

    if not phone:
        return JsonResponse({'status': 'invalid', 'detail': 'phone is required.'}, status=400)

    # 1. Identify patient by phone number
    try:
        patient = Patienttbl.objects.get(contactNo=phone)
    except Patienttbl.DoesNotExist:
        return JsonResponse({'status': 'not_found', 'detail': 'No patient found with that phone number.'}, status=404)

    # 2. Find nearest UPCOMING appointment for this patient
    import datetime
    today = datetime.date.today()
    apt = (
        Appointmenttbl.objects
        .filter(patientid=patient, active__in=[0, 1], aptdate__gte=today)
        .select_related('child', 'hospitalid', 'vaccineid')
        .order_by('aptdate')
        .first()
    )

    if apt is None:
        return JsonResponse({'status': 'not_found', 'detail': 'No upcoming appointment found for this patient.'}, status=404)

    child_name = apt.child.childname if apt.child else (apt.childname or 'Patient')
    apt_date   = apt.aptdate

    # 3. Handle reply
    if reply == 'YES':
        apt.is_confirmed = True
        apt.save(update_fields=['is_confirmed'])

        # Notify hospital via SMS
        from patientapp.utils import send_hospital_sms  # type: ignore[import]  # pyre-ignore
        hospital_phone = getattr(apt.hospitalid, 'contactNo', None) or getattr(apt.hospitalid, 'contact', None)
        if hospital_phone:
            send_hospital_sms(hospital_phone, child_name, apt_date)

        return JsonResponse({
            'status': 'confirmed',
            'detail': f"Appointment for '{child_name}' on {apt_date} confirmed. Hospital notified."
        })

    elif reply == 'NO':
        # active=3 → Cancelled (new convention; 0=Pending, 1=Waiting, 2=Completed)
        apt.active = 3
        apt.save(update_fields=['active'])

        return JsonResponse({
            'status': 'cancelled',
            'detail': f"Appointment for '{child_name}' on {apt_date} has been cancelled."
        })

    else:
        return JsonResponse({
            'status': 'unknown_reply',
            'detail': f"Reply '{reply}' not understood. Please reply YES or NO."
        }, status=400)


def _update_patient_password(patient, current_pass, new_pass, confirm_pass):
    current_valid = check_password(current_pass, patient.password)
    if not current_valid:
        current_valid = (patient.password == current_pass)

    if not current_valid:
        return False, 'Current Password is Not Valid!'
    elif new_pass != confirm_pass:
        return False, 'New Password and Confirm Password do not match!'
    elif current_pass == new_pass:
        return False, 'New Password cannot be identical to your Current Password.'
    
    patient.password = make_password(new_pass)
    patient.must_change_password = False
    if patient.account_status == 'RFID_ASSIGNED':
        patient.account_status = 'ACTIVE'
    patient.save(update_fields=['password', 'must_change_password', 'account_status'])
    return True, ''

class ChangeAuthentication(View):
    def get(self, request):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
            return redirect('patient:loginpage')
        return render(request, 'patientapp/changepassword.html')
    
    def post(self,request):
        patient = Patienttbl.objects.filter(id=request.session.get('Cid')).first()
        if not patient:
            request.session.flush()
            messages.error(request, 'Session expired or patient record not found. Please log in again.')
            return redirect('patient:loginpage')

        current_pass = request.POST.get('cpass')
        new_pass = request.POST.get('password')
        confirm_pass = request.POST.get('cfpass')

        success, msg = _update_patient_password(patient, current_pass, new_pass, confirm_pass)
        if success:
            messages.info(request, 'Password changed successfully on next login!')
            return redirect('patient:changeauth')
        else:
            messages.warning(request, msg)
            return render(request, 'patientapp/changepassword.html')


class ForcePasswordChange(View):
    """Dedicated first-login password change. Users with must_change_password=True are redirected here."""
    def get(self, request):
        if request.session.get('CName') is None:
            return redirect('patient:loginpage')
        return render(request, 'patientapp/force_password_change.html')

    def post(self, request):
        if request.session.get('Cid') is None:
            return redirect('patient:loginpage')

        patient = Patienttbl.objects.filter(id=request.session.get('Cid')).first()
        if not patient:
            request.session.flush()
            messages.error(request, 'Session expired or patient record not found. Please log in again.')
            return redirect('patient:loginpage')
        current_pass = request.POST.get('current_password') or request.POST.get('cpass')
        new_pass = request.POST.get('new_password') or request.POST.get('password')
        confirm_pass = request.POST.get('confirm_password') or request.POST.get('cfpass')

        success, msg = _update_patient_password(patient, current_pass, new_pass, confirm_pass)
        if success:
            messages.info(request, 'Password changed successfully! Welcome to KiddoVax.')
            return redirect('patient:homepage')
        else:
            # Overwrite the default identical error message to match original if needed
            if msg == 'New Password cannot be identical to your Current Password.':
                msg = 'New Password cannot be the same as your current password.'
            messages.warning(request, msg)
            return render(request, 'patientapp/force_password_change.html')


class PendingRegistrationView(View):
    """Shows patients with PENDING_HOSPITAL_REGISTRATION status the hospital registration info."""
    def get(self, request):
        if request.session.get('CName') is None:
            return redirect('patient:loginpage')

        patient = Patienttbl.objects.filter(id=request.session.get('Cid')).first()
        if patient and patient.account_status not in ('PENDING_HOSPITAL_REGISTRATION',):
            return redirect('patient:homepage')

        # Get hospitals sorted by distance if coordinates available
        hospitals = Hospitaltbl.objects.all().select_related('cityId', 'areaId').order_by('title')
        if patient and patient.latitude and patient.longitude:
            from patientapp.services.geocoding_service import sort_hospitals_by_recommendation
            recommended = sort_hospitals_by_recommendation(hospitals, patient.latitude, patient.longitude)
            hospital_list = [item['hospital'] for item in recommended]
        else:
            hospital_list = list(hospitals)

        context = {
            'patient': patient,
            'hospitals': hospital_list,
        }
        return render(request, 'patientapp/pending_registration.html', context)

class PatientProfile(View):
    def get(self, request):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None or request.session.get('Cid') is None:
            return redirect('patient:loginpage')
            
        patientData = Patienttbl.objects.filter(id=request.session.get('Cid')).first()
        if not patientData:
            request.session.flush()
            messages.error(request, 'Session expired or patient account not found. Please log in again.')
            return redirect('patient:loginpage')

        bindCity = City.objects.all().order_by('-id')
        bindArea = Area.objects.filter(cityId=patientData.cityId).order_by('-id') if patientData.cityId else Area.objects.all().order_by('-id')
        form = PatientForm(instance=patientData)
        from patientapp.models import Childtbl  # type: ignore[import]  # pyre-ignore
        children = Childtbl.objects.filter(patient_id=patientData.id).prefetch_related(
            'appointments', 
            'appointments__vaccineid', 
            'appointments__hospitalid'
        ).order_by('dob')
        context = {
            'cityData': bindCity,
            'areaData': bindArea,
            'form': form,
            'selectedCity': patientData.cityId,
            'selectedArea': patientData.areaId,
            'patientData': patientData,
            'children': children
        }
        return render(request, 'patientapp/profile.html', context)
    
    def post(self, request):
        if request.session.get('CName') is None or request.session.get('Cid') is None:
            return redirect('patient:loginpage')

        patientData = Patienttbl.objects.filter(id=request.session.get('Cid')).first()
        if not patientData:
            request.session.flush()
            messages.error(request, 'Session expired or patient account not found. Please log in again.')
            return redirect('patient:loginpage')
            
        action = request.POST.get('action')
        if action == 'add_child':
            from patientapp.models import Childtbl  # type: ignore[import]  # pyre-ignore
            Childtbl.objects.create(
                patient_id=patientData.id,
                childname=request.POST.get('childname'),
                dob=request.POST.get('dob'),
                gender=request.POST.get('gender'),
                blood_group=request.POST.get('blood_group')
            )
            messages.info(request, "Child profile added successfully!")
            return redirect('patient:profilepage')
        elif action == 'delete_child':
            from patientapp.models import Childtbl  # type: ignore[import]  # pyre-ignore
            Childtbl.objects.filter(id=request.POST.get('child_id'), patient_id=patientData.id).delete()
            messages.info(request, "Child profile removed successfully!")
            return redirect('patient:profilepage')
            
        # Directly update only the profile fields — always performs an UPDATE, never INSERT
        patientData.name = request.POST.get('name', patientData.name)
        patientData.contactNo = request.POST.get('contactNo', patientData.contactNo)
        patientData.address = request.POST.get('address', patientData.address)
        patientData.relation = request.POST.get('relation', patientData.relation)
        
        city_id = request.POST.get('cityId')
        area_id = request.POST.get('areaId')
        if city_id:
            patientData.cityId_id = city_id
        if area_id:
            patientData.areaId_id = area_id
        
        patientData.save()
        request.session['CName'] = patientData.name
        messages.info(request, "Your profile has been updated successfully!")
        return redirect('patient:profilepage')

        
class ViewVaccineList(View):
    def get(self, request):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
            return redirect('patient:loginpage')
        bindHospital = Hospitaltbl.objects.all().order_by('-id')
        bindData = Vaccinetbl.objects.select_related("hospitalId").prefetch_related("education_info").all().order_by('id')
        context={
                'hospitalData' : bindHospital,
                'bindData' : bindData,
        }
        return render(request,'patientapp/showvaccines.html',context)

def loadVaccines(request,h_id=None):
    h_id = request.GET.get("h_id")
   
    if int(h_id) >0:
        vlist = Vaccinetbl.objects.filter(hospitalId=h_id).prefetch_related("education_info").order_by('id')
        return render(request, 'patientapp/loadvaccinerecord.html', {'bindData': vlist})                     
    else:
        vlist = Vaccinetbl.objects.select_related("hospitalId").prefetch_related("education_info").all().order_by('id')
        return render(request, 'patientapp/loadvaccinerecord.html', {'bindData': vlist})


class ChildVaccinationHistory(View):
    """Returns vaccination history for a child (HTML partial for AJAX or direct access)."""
    def get(self, request, child_id):
        if request.session.get('CName') is None:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        # Ensure the child belongs to the logged-in patient
        child = get_object_or_404(Childtbl, id=child_id, patient_id=request.session.get('Cid'))
        records = VaccinationRecord.objects.filter(child=child).select_related('vaccine', 'appointment').order_by('-created_at')
        return render(request, 'patientapp/child_history_partial.html', {
            'child': child,
            'records': records
        })


from django.http import HttpResponse

def download_vaccine_card(request, child_id):
    if request.session.get('CName') is None:
        return redirect('patient:loginpage')
    from patientapp.pdf_service import generate_vaccine_card_pdf
    child = get_object_or_404(Childtbl, id=child_id, patient_id=request.session.get('Cid'))
    pdf_bytes = generate_vaccine_card_pdf(child)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="vaccine_card_{child.childname.replace(" ", "_")}.pdf"'
    return response


def upload_vaccine_card_ocr(request):
    if request.method != 'POST' or request.session.get('Cid') is None:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized request'}, status=400)
    
    child_id = request.POST.get('child_id')
    card_image = request.FILES.get('card_image')
    if not child_id or not card_image:
        return JsonResponse({'status': 'error', 'message': 'Missing parameters'}, status=400)
        
    child = get_object_or_404(Childtbl, id=child_id, patient_id=request.session.get('Cid'))
    
    from patientapp.models import VaccineCardUpload
    upload_record = VaccineCardUpload.objects.create(
        patient_id=request.session.get('Cid'),
        image=card_image
    )
    
    from patientapp.ocr_service import extract_vaccine_data_from_image
    extracted = extract_vaccine_data_from_image(upload_record.image.path, child.dob)
    
    # Save the extracted JSON data to the record
    upload_record.extracted_data = extracted
    upload_record.save()
    
    return JsonResponse({
        'status': 'success',
        'upload_id': upload_record.id,
        'child_id': child.id,
        'extracted': extracted
    })


import datetime

def confirm_ocr_results(request):
    if request.method != 'POST' or request.session.get('Cid') is None:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized request'}, status=400)
        
    child_id = request.POST.get('child_id')
    vaccines_json = request.POST.get('vaccines') # JSON array of {name, date, status}
    if not child_id or not vaccines_json:
        return JsonResponse({'status': 'error', 'message': 'Missing parameters'}, status=400)
        
    child = get_object_or_404(Childtbl, id=child_id, patient_id=request.session.get('Cid'))
    
    import json
    try:
        vaccines = json.loads(vaccines_json)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
        
    from hospitalapp.models import Hospitaltbl, Vaccinetbl
    from patientapp.models import Appointmenttbl, VaccinationRecord
    
    # Find any default hospital to link appointments
    default_hospital = Hospitaltbl.objects.first()
    if not default_hospital:
        return JsonResponse({'status': 'error', 'message': 'No registered hospital found to log records.'}, status=400)
        
    created_count = 0
    for item in vaccines:
        vaccine_name = item.get('name')
        date_str = item.get('date')
        if not vaccine_name or not date_str:
            continue
            
        try:
            admin_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            continue
            
        # 1. Check or find/create a generic vaccine at default hospital matching vaccineName
        vaccine = Vaccinetbl.objects.filter(vaccineName__icontains=vaccine_name).first()
        if not vaccine:
            # Create a mock vaccine row at default hospital
            vaccine = Vaccinetbl.objects.create(
                hospitalId=default_hospital,
                vaccineName=vaccine_name,
                vaccineDescr=f"Auto-recovered from historical vaccination card upload.",
                price=0
            )
            
        # 2. Check if a VaccinationRecord already exists for this child & vaccine
        if VaccinationRecord.objects.filter(child=child, vaccine=vaccine).exists():
            continue
            
        # 3. Create a completed appointment
        appointment = Appointmenttbl.objects.create(
            hospitalid=default_hospital,
            vaccineid=vaccine,
            patientid_id=request.session.get('Cid'),
            childname=child.childname,
            child=child,
            aptdate=admin_date,
            active=2 # Completed
        )
        
        # 4. Create VaccinationRecord
        VaccinationRecord.objects.create(
            child=child,
            vaccine=vaccine,
            appointment=appointment
        )
        created_count += 1
        
    return JsonResponse({
        'status': 'success',
        'message': f'Successfully recovered and saved {created_count} vaccination records!'
    })


def set_language(request):
    lang = request.GET.get('lang', 'en')
    request.session['django_language'] = lang
    return redirect(request.META.get('HTTP_REFERER', '/'))


class VaccinationJourneyView(View):
    """Patient AI Vaccination Journey Assistant View (Feature 4)"""
    def get(self, request, child_id=None):
        if request.session.get('Cid') is None:
            return redirect('patient:loginpage')

        patient_id = request.session.get('Cid')
        children = Childtbl.objects.filter(patient_id=patient_id)
        
        if not children.exists():
            messages.warning(request, "Please register your child profile first.")
            return redirect('patient:profilepage')

        target_child = None
        if child_id:
            target_child = children.filter(pk=child_id).first()
        if not target_child:
            target_child = children.first()

        from patientapp.services.journey_assistant_service import build_child_vaccination_journey
        journey_data = build_child_vaccination_journey(target_child.id)

        context = {
            'children': children,
            'selected_child': target_child,
            'journey': journey_data
        }
        return render(request, 'patients/journey.html', context)


class VaccineEducationView(View):
    """Patient AI Vaccination Education & Safety Explainer View (Feature 5)"""
    def get(self, request):
        return render(request, 'patients/education.html')

    def post(self, request):
        query = request.POST.get('query', '').strip()
        from patientapp.services.education_explainer_service import answer_vaccine_education_query
        result = answer_vaccine_education_query(query)
        return JsonResponse(result)
