from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import  View
from hospitalapp.models import Hospitaltbl, Receptionisttbl, Vaccinetbl
from django.contrib.auth import logout
from hospitalapp.forms import ReceptionistForm,VaccineForm
from adminapp.models import City,Area
from patientapp.models import Appointmenttbl
import datetime, random
# Create your views here.


def generate_ui_number():
    for _ in range(50):
        candidate = str(random.randint(10000, 99999))
        if not Receptionisttbl.objects.filter(ui_no=candidate).exists():
            return candidate
    raise Exception('Unable to generate a unique 5-digit UI number for staff registration.')

def Logout(request):
    logout(request)
    request.session.flush()
    return redirect('hospitalapp:hospitallogin')

def Home(request):
    storage = messages.get_messages(request)
    for message in storage:
        pass
    
    if request.session.get('CName') is None or request.session.get('user_role') != 'hospital':
        return redirect('hospitalapp:hospitallogin') 

    hosp_id = request.session.get('Cid')
    hospital = Hospitaltbl.objects.get(id=hosp_id)
    
    if request.method == 'POST':
        new_name = request.POST.get('dcrname')
        new_pass = request.POST.get('password')
        if new_name and new_pass:
            hospital.dcrname = new_name
            hospital.password = new_pass
            hospital.save()
            request.session['CName'] = hospital.title
            messages.success(request, 'Hospital Profile updated successfully.')
            return redirect('hospitalapp:hospitalhome')

    today = datetime.datetime.now().date()
    
    total_vaccines_registered = Vaccinetbl.objects.filter(hospitalId_id=hosp_id).count()
    
    from django.db.models import F
    low_stock_count = Vaccinetbl.objects.filter(
        hospitalId_id=hosp_id,
        stock_quantity__lt=F('minimum_quantity')
    ).count()
    
    this_month_apps = Appointmenttbl.objects.filter(
        hospitalid_id=hosp_id, 
        aptdate__year=today.year, 
        aptdate__month=today.month
    )
    
    total_vaccines_this_month = this_month_apps.count()
    unique_children_this_month = this_month_apps.values('childname').distinct().count()

    context = {
        'hospital': hospital,
        'total_vaccines_registered': total_vaccines_registered,
        'low_stock_count': low_stock_count,
        'total_vaccines_this_month': total_vaccines_this_month,
        'unique_children_this_month': unique_children_this_month,
        'current_month_name': today.strftime("%B")
    }

    return render(request,'hospitalapp/home.html', context)
class HospitalLogin(View):
    def get(self, request):  

        return render(request, 'hospitalapp/login.html')
    
    def post(self, request):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        scontact = str(request.POST.get('contact', '')).strip()
        spassword = str(request.POST.get('password', '')).strip()
      
        try:
            checkusername = Hospitaltbl.objects.get(contactNo = scontact)
        except:
            checkusername = None   
                     
        if checkusername is not None:
            checkcontactpasswordboth = Hospitaltbl.objects.filter(contactNo=scontact,password=spassword).exists()
            if checkcontactpasswordboth:
                loggedname = Hospitaltbl.objects.filter(contactNo=scontact).values('id', 'title')
                request.session['CName'] = loggedname[0]['title']
                request.session['Cid'] = loggedname[0]['id']
                request.session['user_role'] = 'hospital'
                return redirect('hospitalapp:hospitalhome')
            else:
                messages.info(request,'Invalid Password')                
        else:
            messages.info(request,'Invalid Contact No.')

        return render(request,'hospitalapp/login.html') 
    
class ReceptionistRegister(View):
    def get(self, request, id=None, pid=None):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
           return redirect('hospitalapp:hospitallogin')
        form = ReceptionistForm()
        bindCity = City.objects.all().order_by('-id')
        bindData = Receptionisttbl.objects.select_related("cityId").select_related("areaId").all().filter(hospitalid_id = request.session['Cid'] ).order_by('-id')
      
        if pid is not None:
            data = Receptionisttbl.objects.get(pk = pid)
            data.delete()
            pid = None
            messages.info(request,'Receptionist Deleted Success!')
            return redirect('hospitalapp:receptionistregister')

        if id is not None:
            Pdata = Receptionisttbl.objects.get(pk = id)
            form = ReceptionistForm(instance = Pdata)  
            bindArea = load_areasbyCity(request,Pdata.cityId)
            selectedArea = Pdata.areaId
            context={
                'form' : form,
                'ReceptionistData' : bindData,
                'imgurl' : Pdata,
                'cityData' : bindCity,
                'areaData' : bindArea,
                'selectedCity' : Pdata.cityId,
                'selectedArea' : selectedArea,
                'selGender' : Pdata.gender
            }
            return render(request, 'hospitalapp/receptionist.html',context)   
    
       
        context={
                'cityData' : bindCity,
                'ReceptionistData' : bindData,
                'form' : form
        }
        return render(request, 'hospitalapp/receptionist.html', context)
    
    def post(self, request, id=None):
        if 'btnreset' in request.POST and request.method == 'POST':
            return redirect('hospitalapp:receptionistregister')

        if id is not None:
            try:
                data = Receptionisttbl.objects.get(pk=id)
            except Receptionisttbl.DoesNotExist:
                messages.error(request, 'Receptionist record not found.')
                return redirect('hospitalapp:receptionistregister')

            data.hospitalid_id = request.session['Cid']
            if request.POST.get('name'):
                data.name = request.POST.get('name')
            if request.POST.get('address'):
                data.address = request.POST.get('address')
            if request.POST.get('gender'):
                data.gender = request.POST.get('gender')
            if request.POST.get('contactNo'):
                data.contactNo = request.POST.get('contactNo')
            if request.POST.get('password'):
                data.password = request.POST.get('password')
            if request.POST.get('doj'):
                data.doj = request.POST.get('doj')
            if request.POST.get('areaId'):
                data.areaId_id = request.POST.get('areaId')
            if request.POST.get('cityId'):
                data.cityId_id = request.POST.get('cityId')
            if request.FILES.get('staffimg'):
                data.staffimg = request.FILES.get('staffimg')

            data.save()
            messages.info(request, 'Receptionist Updated Success!')
            return redirect('hospitalapp:receptionistregister')
        else:
            ui_no = request.POST.get('ui_no') or generate_ui_number()
            ui_no = str(ui_no).strip()

            if not ui_no.isdigit() or len(ui_no) != 5:
                messages.error(request, 'UI Number must be a 5-digit number.')
                return redirect('hospitalapp:receptionistregister')
            if Receptionisttbl.objects.filter(ui_no=ui_no).exists():
                messages.error(request, 'That UI Number is already assigned to an existing staff account.')
                return redirect('hospitalapp:receptionistregister')

            data = Receptionisttbl(
                hospitalid_id=request.session['Cid'],
                name=request.POST.get('name', ''),
                address=request.POST.get('address', ''),
                gender=request.POST.get('gender', 'Female'),
                contactNo=request.POST.get('contactNo'),
                password=request.POST.get('password', ''),
                ui_no=ui_no,
                staffimg=request.FILES.get('staffimg'),
                doj=request.POST.get('doj'),
                areaId_id=request.POST.get('areaId'),
                cityId_id=request.POST.get('cityId'),
            )
            data.save()
            messages.info(request, f'Receptionist Inserted Success! User ID: {data.ui_no}')
            return redirect('hospitalapp:receptionistregister')
    
def load_areasbyCity(request, cityid=None):
    city_id = cityid if cityid is not None else request.GET.get('city_id')
    if not city_id:
        areas = []
    else:
        raw_areas = Area.objects.filter(cityId=city_id).order_by('areaName')
        seen_names = set()
        areas = []
        for a in raw_areas:
            name_clean = a.areaName.strip().lower()
            if name_clean not in seen_names:
                seen_names.add(name_clean)
                areas.append(a)

    if cityid is not None:
        return areas
    else:     
        return render(request, 'adminapp/citytoarea.html', {'arealist': areas})    

class ManageVaccine(View):
    def get(self, request,id=None,vid=None):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
            return redirect('hospitalapp:hospitallogin')
         

        if vid is not None:
            data = Vaccinetbl.objects.get(pk = vid)
            data.delete()
            vid = None
            messages.info(request,'Vaccine Deleted Success!')
            return redirect('hospitalapp:vaccineregister') 
        if id is not None:
            data = Vaccinetbl.objects.get(pk = id)
            form = VaccineForm(instance  = data)   
        else:    
            form = VaccineForm()

        vaccineData = Vaccinetbl.objects.all().filter(hospitalId_id=request.session.get('Cid')).order_by('-id')
        
        # Predefined short descriptions
        VACCINE_DESCRIPTIONS = {
            'BCG': 'Tuberculosis vaccine, given at birth to prevent severe TB meningitis.',
            'Hepatitis-B 1': 'Hepatitis B dose 1, given at birth to prevent viral liver infection.',
            'Hepatitis B*': 'Hepatitis B initial dose, given at birth.',
            'Hepatitis-B 2': 'Hepatitis B dose 2, usually given at 1 month.',
            'Hepatitis B 3': 'Hepatitis B dose 3, usually given at 6 months.',
            'OPV-O': 'Oral Polio Vaccine birth dose, given orally.',
            'IPV+OPV1': 'Inactivated Polio + Oral Polio Vaccine dose 1.',
            'IPV+OPV2': 'Inactivated Polio + Oral Polio Vaccine dose 2.',
            'IPV+OPV3': 'Inactivated Polio + Oral Polio Vaccine dose 3.',
            'IPV+OPV': 'Inactivated Polio + Oral Polio Vaccine combo.',
            'DTAP1/DTWP1': 'Diphtheria, Tetanus, and Pertussis vaccine dose 1.',
            'DTAP2/DTWP2': 'Diphtheria, Tetanus, and Pertussis vaccine dose 2.',
            'DTAP3/DTWP3': 'Diphtheria, Tetanus, and Pertussis vaccine dose 3.',
            'HIB1': 'Haemophilus influenzae type b (Hib) vaccine dose 1.',
            'HIB2': 'Haemophilus influenzae type b (Hib) vaccine dose 2.',
            'HiB booster': 'Haemophilus influenzae type b (Hib) booster vaccine.',
            'Pneumococcal 1': 'Pneumococcal Conjugate Vaccine (PCV) dose 1.',
            'Pneumococcal 2': 'Pneumococcal Conjugate Vaccine (PCV) dose 2.',
            'Pneumococcal 3': 'Pneumococcal Conjugate Vaccine (PCV) dose 3.',
            'PCV booster': 'Pneumococcal Conjugate Vaccine (PCV) booster.',
            'Rotavirus1': 'Rotavirus vaccine dose 1, oral vaccine for severe diarrhea.',
            'Rotavirus2': 'Rotavirus vaccine dose 2, oral vaccine for severe diarrhea.',
            'Rotavirus3': 'Rotavirus vaccine dose 3, oral vaccine for severe diarrhea.',
            'Influenza 1': 'Seasonal Influenza (Flu) vaccine dose 1.',
            'Influenza 2': 'Seasonal Influenza (Flu) vaccine dose 2.',
            'Influenza 3': 'Seasonal Influenza (Flu) vaccine dose 3.',
            'Influenza 4': 'Seasonal Influenza (Flu) vaccine dose 4.',
            'Influenza 5': 'Seasonal Influenza (Flu) vaccine dose 5.',
            'Influenza 6': 'Seasonal Influenza (Flu) vaccine dose 6.',
            'MMR 1': 'Measles, Mumps, and Rubella (MMR) vaccine dose 1.',
            'MMR 2 with vitamin A': 'Measles, Mumps, and Rubella (MMR) vaccine dose 2 with Vitamin A.',
            'MMR 3': 'Measles, Mumps, and Rubella (MMR) vaccine dose 3.',
            'Varicella 1': 'Varicella (Chickenpox) vaccine dose 1.',
            'Varicella 2': 'Varicella (Chickenpox) vaccine dose 2.',
            'Hepatitis A1': 'Hepatitis A vaccine dose 1, protecting against liver infection.',
            'Typhoid Conjugate': 'Typhoid Conjugate Vaccine protecting against typhoid fever.',
            'Typhoid Booster 1': 'Typhoid vaccine booster dose.',
            'DTwP/DTap Booster 1': 'Diphtheria, Tetanus, Pertussis booster dose 1.',
            'DTwP/DTap Booster 2': 'Diphtheria, Tetanus, Pertussis booster dose 2.',
            'OPV4': 'Oral Polio Vaccine booster dose 4.',
            'OVP5': 'Oral Polio Vaccine booster dose 5.',
            'OPV6': 'Oral Polio Vaccine booster dose 6.',
            'Meningococcol 1(optional)': 'Meningococcal vaccine dose 1, protecting against meningitis.',
            'Meningococcol 2(optional)': 'Meningococcal vaccine dose 2, protecting against meningitis.',
            'HPV 1,2 and 3': 'Human Papillomavirus vaccine series for cervical cancer prevention.',
            'Tdap/Td': 'Tetanus, Diphtheria, Pertussis booster for older children/adolescents.',
            'COVID-19': 'COVID-19 vaccine for children.',
        }
        from hospitalapp.services.inventory_forecast_service import generate_inventory_forecast_for_hospital
        days_param = request.GET.get('days', '14')
        try:
            forecast_days = int(days_param)
            if forecast_days not in [7, 14, 30]:
                forecast_days = 14
        except ValueError:
            forecast_days = 14

        forecasts = generate_inventory_forecast_for_hospital(request.session.get('Cid'), forecast_days)
        forecast_map = {f['vaccine_id']: f for f in forecasts}

        for v in vaccineData:
            v.forecast = forecast_map.get(v.id, {})
        
        import json
        inventory_dict = {}
        for v in vaccineData:
            inventory_dict[v.vaccineName] = {
                'id': v.id,
                'price': str(v.price),
                'descr': v.vaccineDescr,
                'stock': v.stock_quantity,
                'min': v.minimum_quantity
            }

        context={
            'form' : form,
            'vaccinedata' : vaccineData,
            'forecast_days': forecast_days,
            'vaccine_descriptions_json': json.dumps(VACCINE_DESCRIPTIONS),
            'inventory_json': json.dumps(inventory_dict)
        }
        return render(request, 'hospitalapp/managevaccine.html',context)    

    def post(self, request, id=None):
        if 'btnreset' in request.POST and request.method == 'POST':
            return redirect('hospitalapp:vaccineregister')

        hosp_id = request.session.get('Cid')
        vName = request.POST.get("vaccineName")
        existing_id = request.POST.get("existing_vaccine_id") or id

        if not vName and not existing_id:
            messages.error(request, "Vaccine name is required.")
            return redirect('hospitalapp:vaccineregister')

        # Check if vaccine already exists in hospital inventory
        existing_vaccine = None
        if existing_id:
            existing_vaccine = Vaccinetbl.objects.filter(id=existing_id, hospitalId_id=hosp_id).first()
        if not existing_vaccine and vName:
            existing_vaccine = Vaccinetbl.objects.filter(vaccineName=vName, hospitalId_id=hosp_id).first()

        added_stock = int(request.POST.get('added_stock', 0) or 0)
        price_val = request.POST.get('price')
        descr_val = request.POST.get('vaccineDescr')
        min_qty = int(request.POST.get('minimum_quantity', 5) or 5)

        if existing_vaccine:
            # Restock existing vaccine or update price / description / min threshold
            msg_parts = []
            if added_stock > 0:
                existing_vaccine.stock_quantity += added_stock
                msg_parts.append(f"+{added_stock} doses added (New Total: {existing_vaccine.stock_quantity})")
            
            if price_val is not None and price_val != '':
                existing_vaccine.price = price_val
            if descr_val is not None:
                existing_vaccine.vaccineDescr = descr_val
            existing_vaccine.minimum_quantity = min_qty
            existing_vaccine.save()

            if msg_parts:
                messages.info(request, f"Updated stock for '{existing_vaccine.vaccineName}'! {', '.join(msg_parts)}")
            else:
                messages.info(request, f"Successfully updated vaccine details for '{existing_vaccine.vaccineName}'!")
            return redirect('hospitalapp:vaccineregister')
        else:
            # Insert new vaccine
            initial_stock = int(request.POST.get('stock_quantity', 50) or 50)
            if added_stock > 0:
                initial_stock = added_stock

            Vaccinetbl.objects.create(
                hospitalId_id=hosp_id,
                vaccineName=vName,
                vaccineDescr=descr_val or '',
                price=price_val or 0,
                stock_quantity=initial_stock,
                minimum_quantity=min_qty
            )
            messages.info(request, f"Vaccine '{vName}' added to inventory with {initial_stock} doses!")
            return redirect('hospitalapp:vaccineregister')


class ShowAppointments(View):
    def get(self, request, id=None):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
            return redirect('hospitalapp:hospitallogin')
        
        hospital_id = request.session.get('Cid')
        from patientapp.services.queue_priority_service import get_prioritized_queue_for_hospital
        
        # Get all upcoming & today's appointments enriched with priority scores & reasons
        queue_data = get_prioritized_queue_for_hospital(hospital_id)

        # Summary counts
        high_count = sum(1 for item in queue_data if item['priority'] == 'HIGH')
        medium_count = sum(1 for item in queue_data if item['priority'] == 'MEDIUM')
        normal_count = sum(1 for item in queue_data if item['priority'] == 'NORMAL')
        low_count = sum(1 for item in queue_data if item['priority'] == 'LOW')

        context = {
            'data': queue_data,
            'high_count': high_count,
            'medium_count': medium_count,
            'normal_count': normal_count,
            'low_count': low_count,
            'today': datetime.date.today(),
            'active_tab': 'appointments'
        }
        return render(request, 'hospitalapp/showappointment.html', context)


class AIQueueView(View):
    """Hospital AI Vaccination Queue View (Consolidated into Appointments)"""
    def get(self, request):
        return redirect('hospitalapp:showappointment')


class InventoryForecastView(View):
    """Hospital AI Vaccine Inventory Forecast View (Consolidated into Vaccines page)"""
    def get(self, request):
        days = request.GET.get('days', '14')
        from django.urls import reverse
        return redirect(f"{reverse('hospitalapp:vaccineregister')}?days={days}")


class RecordAlertsView(View):
    """Hospital AI Vaccination Record Quality Alerts View (Feature 3)"""
    def get(self, request):
        if request.session.get('CName') is None:
            return redirect('hospitalapp:hospitallogin')

        hospital_id = request.session.get('Cid')
        from hospitalapp.models import VaccinationRecordAlert
        from patientapp.services.quality_checker_service import run_quality_check_for_child
        from patientapp.models import Appointmenttbl

        # Automatically run AI Quality Audit for all hospital patients
        child_ids = Appointmenttbl.objects.filter(
            hospitalid_id=hospital_id,
            child__isnull=False
        ).values_list('child_id', flat=True).distinct()

        for c_id in child_ids:
            run_quality_check_for_child(c_id)
        
        # Fetch alerts for patients at this hospital
        alerts = VaccinationRecordAlert.objects.filter(
            appointment__hospitalid_id=hospital_id
        ).select_related('child', 'appointment', 'appointment__vaccineid').order_by('-created_at')

        pending_count = alerts.filter(status='PENDING').count()
        verified_count = alerts.filter(status='VERIFIED').count()

        context = {
            'alerts': alerts,
            'pending_count': pending_count,
            'verified_count': verified_count
        }
        return render(request, 'hospitalapp/record_alerts.html', context)


def resolve_record_alert(request, alert_id):
    """POST /hospital/resolve-alert/<alert_id>/"""
    if request.method == 'POST' and request.session.get('Cid'):
        from hospitalapp.models import VaccinationRecordAlert
        alert = Hospitaltbl.objects.filter(id=request.session.get('Cid')).first()
        if not alert:
            return redirect('hospitalapp:hospitallogin')

        new_status = request.POST.get('status', 'VERIFIED')
        if new_status in ['VERIFIED', 'CORRECTED', 'PENDING']:
            rec_alert = VaccinationRecordAlert.objects.filter(id=alert_id).first()
            if rec_alert:
                rec_alert.status = new_status
                rec_alert.save(update_fields=['status'])
                messages.success(request, f"Alert for '{rec_alert.child.childname}' marked as {new_status}.")

    return redirect('hospitalapp:record_alerts')


class ScheduleSettingsView(View):
    """Configures hospital operating hours, breaks, and holidays (Feature 4)"""
    def get(self, request):
        if request.session.get('CName') is None:
            return redirect('hospitalapp:hospitallogin')
            
        hospital_id = request.session.get('Cid')
        hospital = Hospitaltbl.objects.get(id=hospital_id)
        from hospitalapp.models import HospitalBreak, HospitalHoliday
        breaks = HospitalBreak.objects.filter(hospital=hospital)
        holidays = HospitalHoliday.objects.filter(hospital=hospital).order_by('date')

        context = {
            'hospital': hospital,
            'breaks': breaks,
            'holidays': holidays
        }
        return render(request, 'hospitalapp/schedule_settings.html', context)

    def post(self, request):
        if request.session.get('CName') is None:
            return redirect('hospitalapp:hospitallogin')

        hospital_id = request.session.get('Cid')
        hospital = Hospitaltbl.objects.get(id=hospital_id)
        action = request.POST.get('action')

        from hospitalapp.models import HospitalBreak, HospitalHoliday

        if action == 'update_hours':
            opening = request.POST.get('opening_time')
            closing = request.POST.get('closing_time')
            duration = request.POST.get('slot_duration')
            capacity = request.POST.get('slot_capacity')

            if opening: hospital.opening_time = opening
            if closing: hospital.closing_time = closing
            if duration: hospital.slot_duration = int(duration)
            if capacity: hospital.slot_capacity = int(capacity)

            hospital.save()
            messages.success(request, "Operating hours and slot parameters updated successfully.")

        elif action == 'add_break':
            start = request.POST.get('start_time')
            end = request.POST.get('end_time')
            if start and end:
                HospitalBreak.objects.create(hospital=hospital, start_time=start, end_time=end)
                messages.success(request, f"Break period ({start} - {end}) added.")

        elif action == 'delete_break':
            break_id = request.POST.get('break_id')
            HospitalBreak.objects.filter(id=break_id, hospital=hospital).delete()
            messages.success(request, "Break period removed.")

        elif action == 'add_holiday':
            h_date = request.POST.get('date')
            h_desc = request.POST.get('description', '')
            if h_date:
                HospitalHoliday.objects.create(hospital=hospital, date=h_date, description=h_desc)
                messages.success(request, f"Closed date ({h_date}) added.")

        elif action == 'delete_holiday':
            holiday_id = request.POST.get('holiday_id')
            HospitalHoliday.objects.filter(id=holiday_id, hospital=hospital).delete()
            messages.success(request, "Closed date removed.")

        return redirect('hospitalapp:schedule_settings')

class ShowPastAppointments(View):
    def get(self, request, id=None):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
            return redirect('hospitalapp:hospitallogin')
        
        hospital_id = request.session.get('Cid')
        get_data = Appointmenttbl.objects.filter(hospitalid=hospital_id, active=2).order_by('-id')
        
        past_data = []
        for apt in get_data:
            past_data.append({
                'appointment': apt,
                'priority': 'COMPLETED',
                'reasons': ['Vaccination successfully administered and recorded.']
            })

        context = {
            'data': past_data,
            'active_tab': 'history',
            'is_past': True
        }
        return render(request, 'hospitalapp/showappointment.html', context)


# ─── Phase 3: Hospital Patient Registration & RFID Assignment ───

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


class PatientRegistrationView(View):
    """Hospital staff registers patients and assigns RFID devices."""
    def get(self, request):
        if request.session.get('CName') is None:
            return redirect('hospitalapp:hospitallogin')

        hospital_id = request.session.get('Cid')
        search_q = request.GET.get('q', '').strip()

        from patientapp.services.hospital_registration_service import find_pending_patients
        pending_patients = find_pending_patients(search_q if search_q else None)

        context = {
            'pending_patients': pending_patients,
            'search_query': search_q,
            'hospital_id': hospital_id,
        }
        return render(request, 'hospitalapp/patient_registration.html', context)


class RFIDManagementView(View):
    """Hospital staff manages RFID cards assigned at their hospital."""
    def get(self, request):
        if request.session.get('CName') is None:
            return redirect('hospitalapp:hospitallogin')

        hospital_id = request.session.get('Cid')
        search_q = request.GET.get('q', '').strip()

        from patientapp.services.hospital_registration_service import get_hospital_rfid_cards, get_rfid_assignment_logs
        rfid_cards = get_hospital_rfid_cards(hospital_id, search_q if search_q else None)
        audit_logs = get_rfid_assignment_logs(hospital_id, limit=30)

        context = {
            'rfid_cards': rfid_cards,
            'audit_logs': audit_logs,
            'search_query': search_q,
        }
        return render(request, 'hospitalapp/rfid_management.html', context)


@csrf_exempt
def assign_rfid_api(request):
    """POST /hospital/api/assign-rfid/ — Assigns RFID to patient."""
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
    hospital_id = request.session.get('Cid')
    staff_name = request.session.get('CName', '')

    if not patient_id or not rfid_number:
        return JsonResponse({'success': False, 'message': 'Patient ID and RFID number are required.'})

    from patientapp.services.hospital_registration_service import register_patient_at_hospital
    result = register_patient_at_hospital(
        patient_id=int(patient_id),
        hospital_id=hospital_id,
        rfid_card_number=rfid_number,
        staff_name=staff_name,
    )
    return JsonResponse(result)


@csrf_exempt
def generate_rfid_for_hospital(request):
    """GET/POST /hospital/api/generate-rfid/ — Generates a unique RFID number.

    The UI both in the hospital registration page and the receptionist scanner page
    reads the generated number as a JSON field. Return the canonical card_number plus
    compatibility aliases used by the current templates.
    """
    from receptionistapp.services.rfid_service import generate_unique_rfid_number
    card_number = generate_unique_rfid_number()
    return JsonResponse({
        'success': True,
        'card_number': card_number,
        'rfid': card_number,
        'rfid_number': card_number,
        'rfidno': card_number,
    })


@csrf_exempt
def verify_patient_registration_api(request):
    """POST /hospital/api/verify-registration/ — Verify the patient using the registered phone."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    if request.session.get('CName') is None:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    patient_id = data.get('patient_id')
    phone_number = data.get('phone_number') or data.get('contactNo') or data.get('contact')
    staff_name = request.session.get('CName', '')

    if not patient_id:
        return JsonResponse({'success': False, 'message': 'Patient ID is required.'})

    if not phone_number:
        return JsonResponse({'success': False, 'message': 'Phone number is required.'})

    from patientapp.services.hospital_registration_service import verify_patient_registration_by_phone
    result = verify_patient_registration_by_phone(
        patient_id=int(patient_id),
        phone_number=phone_number,
        staff_name=staff_name,
    )
    return JsonResponse(result)


@csrf_exempt
def search_pending_patients_api(request):
    """GET /hospital/api/search-patients/?q=query — Search pending patients."""
    if request.session.get('CName') is None:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    query = request.GET.get('q', '').strip()
    from patientapp.services.hospital_registration_service import find_pending_patients
    patients = find_pending_patients(query if query else None)

    data = [
        {
            'id': p.id,
            'name': p.name,
            'contact': str(p.contactNo) if p.contactNo else '',
            'address': p.address,
            'city': p.cityId.cityName if p.cityId else '',
            'area': p.areaId.areaName if p.areaId else '',
            'status': p.account_status,
        }
        for p in patients[:20]
    ]
    return JsonResponse({'patients': data})


@csrf_exempt
def deactivate_rfid_api(request):
    """POST /hospital/api/deactivate-rfid/ — Deactivates an RFID card."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    if request.session.get('CName') is None:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    rfid_number = data.get('rfid_number') or data.get('card_number')
    if not rfid_number:
        return JsonResponse({'success': False, 'message': 'RFID number is required.'})

    from patientapp.models import RFIDCard, RFIDAssignmentLog
    rfid_card = RFIDCard.objects.filter(card_number=str(rfid_number).strip(), is_active=True).first()
    if not rfid_card:
        return JsonResponse({'success': False, 'message': 'Active RFID card not found.'})

    rfid_card.is_active = False
    rfid_card.save(update_fields=['is_active'])

    hospital_id = request.session.get('Cid')
    staff_name = request.session.get('CName', '')

    RFIDAssignmentLog.objects.create(
        rfid_card=rfid_card,
        patient=rfid_card.patient,
        action='DEACTIVATED',
        performed_by=staff_name,
        hospital_id=hospital_id,
    )

    return JsonResponse({
        'success': True,
        'message': f'RFID {rfid_number} has been deactivated.',
    })
