from django.shortcuts import render,redirect
from hospitalapp.models import Receptionisttbl
from django.contrib import messages
from django.views import  View
from django.contrib.auth import logout

from patientapp.forms import AppointmentForm
from patientapp.models import Appointmenttbl, VaccinationRecord, RFIDCard
import datetime
# Create your views here.

def Logout(request):
    logout(request)
    request.session.flush()
    return redirect('receptionist:receptionistlogin')

def Home(request):
    storage = messages.get_messages(request)
    for message in storage:
        message = None
    if request.session.get('CName') is None or request.session.get('user_role') != 'receptionist':
        return redirect('receptionist:receptionistlogin')
        
    hospital_name = ""
    queue_data = {}
    try:
        recep = Receptionisttbl.objects.select_related('hospitalid').get(id=request.session.get('Cid'))
        hospital_name = recep.hospitalid.title
        h_id = recep.hospitalid_id
        
        from receptionistapp.services.queue_assistant_service import get_receptionist_counter_queue
        queue_data = get_receptionist_counter_queue(h_id)
    except Exception as e:
        pass
        
    return render(request, 'receptionistapp/home.html', {
        'queue_data': queue_data,
        'waiting_count': queue_data.get('waiting_count', 0),
        'today_apps': queue_data.get('total_count', 0),
        'hospital_name': hospital_name
    })

class ManagePatient(View):
    def get(self, request, id=None):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None or request.session.get('user_role') != 'receptionist':
            return redirect('receptionist:receptionistlogin')
        
        # show data
        if id is not None:
            getData = Appointmenttbl.objects.filter(id=id).order_by('-id')
            apt = getData.first()
            existing_rfid = ""
            if apt:
                if apt.rfidno:
                    existing_rfid = str(apt.rfidno)
                elif apt.patientid_id:
                    from patientapp.models import RFIDCard
                    rfid_card = RFIDCard.objects.filter(patient_id=apt.patientid_id, is_active=True).first()
                    if rfid_card:
                        existing_rfid = rfid_card.card_number

            form = AppointmentForm()
            context = {
                'data': getData,
                'form': form,
                'existing_rfid': existing_rfid
            }
            return render(request, 'receptionistapp/showdata.html', context)     

        gethId = Receptionisttbl.objects.filter(id=request.session.get('Cid')).values('hospitalid_id').distinct()
        bindData = Appointmenttbl.objects.filter(hospitalid=gethId[0]['hospitalid_id']).select_related("patientid", "child", "vaccineid").all().order_by('-id')
        
        queue_data = {}
        try:
            from receptionistapp.services.queue_assistant_service import get_receptionist_counter_queue
            queue_data = get_receptionist_counter_queue(gethId[0]['hospitalid_id'])
        except Exception:
            pass

        context = {
            'bindData': bindData,
            'queue_data': queue_data,
        }
       
        return render(request, 'receptionistapp/booking.html', context)

    def post(self, request, id=None):
        UpdateData = Appointmenttbl.objects.filter(id=id).select_related('patientid', 'child').first()
        if not UpdateData:
            messages.error(request, "Appointment not found.")
            return redirect('receptionist:receptionisthome')

        patient = UpdateData.patientid
        current_status = UpdateData.active or 0
        rfid_val = str(request.POST.get('rfidno') or '').strip()

        # Strict RFID Authentication Check
        if rfid_val and patient:
            assigned_rfids = set(RFIDCard.objects.filter(patient=patient, is_active=True).values_list('card_number', flat=True))
            if assigned_rfids and rfid_val not in assigned_rfids:
                messages.error(request, "Not the verified RFID users.")
                return redirect('receptionist:showappointment', id=id)

            other_owner = RFIDCard.objects.filter(card_number=rfid_val, is_active=True).exclude(patient=patient).first()
            if other_owner:
                messages.error(request, "Not the verified RFID users.")
                return redirect('receptionist:showappointment', id=id)

        if current_status == 0:
            if not rfid_val:
                messages.error(request, "RFID card number is required for check-in.")
                return redirect('receptionist:showappointment', id=id)

            if patient and not assigned_rfids:
                from receptionistapp.services.rfid_service import link_rfid_card
                link_rfid_card(rfid_val, patient_id=patient.id, child_id=UpdateData.child_id)

            now = datetime.datetime.now()
            try:
                UpdateData.rfidno = int(rfid_val)
            except ValueError:
                UpdateData.rfidno = None
            UpdateData.checkin_rfid = rfid_val
            UpdateData.indt = now
            UpdateData.checkin_time = now
            UpdateData.active = 1
            UpdateData.save(update_fields=['indt', 'checkin_time', 'checkin_rfid', 'rfidno', 'active'])
            messages.success(request, f"Patient '{patient.name if patient else 'User'}' authenticated & checked in successfully!")

        elif current_status == 1:
            now = datetime.datetime.now()
            UpdateData.outdt = now
            UpdateData.completion_time = now
            UpdateData.completion_rfid = rfid_val or getattr(UpdateData, 'checkin_rfid', '')
            UpdateData.active = 2
            UpdateData.save(update_fields=['outdt', 'completion_time', 'completion_rfid', 'active'])

            # Automatically decrement vaccine stock quantity at the hospital by 1
            if UpdateData.vaccineid and UpdateData.vaccineid.stock_quantity > 0:
                UpdateData.vaccineid.stock_quantity = max(0, UpdateData.vaccineid.stock_quantity - 1)
                UpdateData.vaccineid.save(update_fields=['stock_quantity'])

            # Auto-create VaccinationRecord when appointment is completed
            if UpdateData.child_id:
                VaccinationRecord.objects.get_or_create(
                    child_id=UpdateData.child_id,
                    vaccine_id=UpdateData.vaccineid_id,
                    defaults={'appointment': UpdateData}
                )
                from patientapp.services.quality_checker_service import run_quality_check_for_child
                run_quality_check_for_child(UpdateData.child_id)

        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('receptionist:showappointment', id=id)

class ReceptionistLogin(View):
    def get(self, request):  

        return render(request, 'receptionistapp/login.html')
    
    def post(self, request):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        scontact = str(request.POST.get('contact', '')).strip()
        spassword = str(request.POST.get('password', '')).strip()

        checkUser = Receptionisttbl.objects.filter(
            password=spassword
        ).filter(
            models.Q(contactNo=scontact) | models.Q(ui_no=scontact)
        ).first()
        if checkUser:
            request.session['CName'] = checkUser.name
            request.session['Cid'] = checkUser.id
            request.session['hId'] = checkUser.hospitalid_id
            request.session['user_role'] = 'receptionist'
            return redirect('receptionist:receptionisthome')
        else:
            messages.error(request, 'Invalid Phone Number / User ID or Password!')
            return render(request, 'receptionistapp/login.html')


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from receptionistapp.services.rfid_service import scan_rfid_card, generate_unique_rfid_number, link_rfid_card
from django.db import models
import json

@csrf_exempt
def rfid_scan_api(request):
    """POST /receptionist/api/rfid/scan/ — Hardware-ready RFID Scanner API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    card_number = data.get('rfid_number') or data.get('card_number')
    hospital_id = request.session.get('hId')

    if not hospital_id and request.session.get('Cid'):
        recep = Receptionisttbl.objects.filter(id=request.session.get('Cid')).first()
        if recep:
            hospital_id = recep.hospitalid_id

    result = scan_rfid_card(card_number, hospital_id=hospital_id)
    return JsonResponse(result)


@csrf_exempt
def rfid_generate_api(request):
    """GET/POST /receptionist/api/rfid/generate/ — Generates a unique RFID string.

    The receptionist dashboard and the legacy appointment detail page both read the
    card value from the JSON payload, but each consumer historically expected a
    different property name. Return both aliases so older templates and the modern
    scanner panel can use the same API without a JS-only compatibility layer.
    """
    card_number = generate_unique_rfid_number()
    return JsonResponse({
        'success': True,
        'card_number': card_number,
        'rfid': card_number,
        'rfid_number': card_number,
        'rfidno': card_number,
    })


@csrf_exempt
def rfid_pending_list_api(request):
    """GET /receptionist/api/pending-registrations/ — All registered patient accounts for RFID assignment."""
    if request.method != 'GET':
        return JsonResponse({'error': 'GET method required'}, status=405)

    if request.session.get('CName') is None:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    from patientapp.models import Patienttbl
    patients = Patienttbl.objects.all().order_by('-id')

    data = [
        {
            'id': p.id,
            'name': p.name,
            'contact': str(p.contactNo) if p.contactNo else '',
            'address': p.address,
            'city': p.cityId.cityName if p.cityId else '',
            'area': p.areaId.areaName if p.areaId else '',
            'status': p.account_status,
            'has_rfid': p.rfid_cards.filter(is_active=True).exists(),
        }
        for p in patients[:100]
    ]

    return JsonResponse({'patients': data})


@csrf_exempt
def rfid_assign_pending_api(request):
    """POST /receptionist/api/rfid/assign-pending/ — Assign generated RFID to a pending patient."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    if request.session.get('CName') is None:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    patient_id = data.get('patient_id')
    rfid_number = data.get('rfid_number') or data.get('card_number')
    hospital_id = request.session.get('hId') or request.session.get('Cid')
    staff_name = request.session.get('CName', '')

    if not patient_id:
        return JsonResponse({'success': False, 'message': 'A pending account must be selected.'})

    if not rfid_number:
        return JsonResponse({'success': False, 'message': 'No RFID number available for assignment.'})

    from patientapp.services.hospital_registration_service import register_patient_at_hospital
    result = register_patient_at_hospital(
        patient_id=int(patient_id),
        hospital_id=hospital_id,
        rfid_card_number=rfid_number,
        staff_name=staff_name,
    )

    return JsonResponse(result)


@csrf_exempt
def rfid_link_api(request):
    """POST /receptionist/api/rfid/link/ — Links RFID card to patient"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    card_number = data.get('card_number') or data.get('rfid_number')
    patient_id = data.get('patient_id')
    child_id = data.get('child_id')

    result = link_rfid_card(card_number, patient_id=patient_id, child_id=child_id)
    return JsonResponse(result)


@csrf_exempt
def rfid_checkin_api(request):
    """POST /receptionist/api/rfid/checkin/ — Smart Check-in Execution API with Strict Authentication"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    apt_id = data.get('appointment_id')
    rfid_num = str(data.get('rfid_number') or data.get('card_number') or '').strip()

    from receptionistapp.services.rfid_service import checkin_patient
    receptionist_id = request.session.get('Cid')
    hospital_id = request.session.get('hId')

    result = checkin_patient(
        appointment_id=int(apt_id) if (apt_id and str(apt_id).isdigit()) else 0,
        rfid_number=rfid_num,
        receptionist_id=receptionist_id,
        hospital_id=hospital_id
    )

    if not result.get('success'):
        return JsonResponse({'success': False, 'message': result.get('message', 'Authentication failed for RFID card.')}, status=400)

    return JsonResponse(result)
    

    