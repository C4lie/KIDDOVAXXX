from django.shortcuts import render, redirect, get_object_or_404  # type: ignore[import]  # pyre-ignore
from django.http import JsonResponse  # type: ignore[import]  # pyre-ignore
from patientapp.forms import PatientForm, AppointmentForm  # type: ignore[import]  # pyre-ignore
from django.views  import View  # type: ignore[import]  # pyre-ignore
from django.contrib import messages  # type: ignore[import]  # pyre-ignore
from adminapp.models import City,Area  # type: ignore[import]  # pyre-ignore
from patientapp.models import Patienttbl, Appointmenttbl, Childtbl, VaccinationRecord  # type: ignore[import]  # pyre-ignore
from hospitalapp.models import Vaccinetbl, Hospitaltbl  # type: ignore[import]  # pyre-ignore
from django.contrib.auth.models import auth  # type: ignore[import]  # pyre-ignore
from django.contrib.auth import logout  # type: ignore[import]  # pyre-ignore
from django.contrib.sessions.models import Session  # type: ignore[import]  # pyre-ignore
# Create your views here.
def Home(request):
    return render(request, 'patientapp/home.html')

def About(request):
    return render(request, 'patientapp/about.html')

def Contact(request):
    return render(request, 'patientapp/contact.html')


class PatientLogout(View):
    def get(self, request):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        storage.used = False
        logout(request)
        Session.objects.all().delete()
        return render(request, 'patientapp/home.html')

class PatientLogin(View):
    def get(self, request):
        form = PatientForm()
        context={
            'form' : form
        }
        return render(request, 'patientapp/login.html',context)
    def post(self, request):
        contact = request.POST['contactno']
        password = request.POST['password']

        try:
            checkusername = Patienttbl.objects.get(contactNo = contact)
        except:
            checkusername = None   
                     
        if checkusername is not None:
            checkcontactpasswordboth = Patienttbl.objects.filter(contactNo=contact,password=password).exists()
            if checkcontactpasswordboth:
                #loggedname = CustomerModel.objects.only('name').get(contactno=scontact)
                loggedname = Patienttbl.objects.filter(contactNo=contact).values('id','name')
                request.session['CName'] =loggedname[0]['name']
                request.session['Cid'] =loggedname[0]['id']
                return redirect('patient:homepage')
            else:
                messages.info(request,'Invalid Password')                
        else:
            messages.info(request,'Invalid Contact Number')

        return render(request,'patientapp/login.html')  


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
            messages.info(request,"Your registration is success!")
            if form.is_valid():
                form.save()
        return redirect('patient:loginpage')  
    
class BookedAppointment(View):
    def get(self, request, aid=None):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
            return redirect('patient:loginpage')
        # bindVaccine = Vaccinetbl.objects.all().order_by('-id')
        bindHospital = Hospitaltbl.objects.all().order_by('-id')
        bindData = Appointmenttbl.objects.select_related("hospitalid").select_related("vaccineid").all().filter(patientid_id=request.session.get('Cid')).order_by('-id')
        form = AppointmentForm()

        if aid is not None:
            data = Appointmenttbl.objects.get(pk = aid)
            data.delete()
            aid = None
            messages.info(request,'Appointment Deleted Success!')
            return redirect('patient:vaccinebooking') 
        
        from patientapp.models import Childtbl  # type: ignore[import]  # pyre-ignore
        children = Childtbl.objects.filter(patient_id=request.session.get('Cid')).order_by('dob')
        context={
                'hospitalData' : bindHospital,
                'form' : form,
                'bindData' : bindData,
                'children' : children
        }
        return render(request,'patientapp/bookvaccine.html',context)
    def post(self, request):
     
        form = AppointmentForm(request.POST)
        if form.is_valid():
        
            data = form.save(commit=False)
            data.childname = request.POST.get('childname')
            data.hospitalid_id = request.POST.get('hospitalid')
            data.vaccineid_id  = request.POST.get('vaccineid')
            data.patientid_id = request.session['Cid']
            data.aptdate = request.POST.get('aptdate')
            data.active = 0
            # Save child FK if a valid child_id was submitted
            child_id = request.POST.get('child_id')
            if child_id and child_id.isdigit():
                data.child_id = int(child_id)
            data.save()
            messages.info(request,"Your appointment is successfully booked!")
            return redirect('patient:vaccinebooking')
        else:
            messages.error(request, "Failed to book appointment. Check that all fields are selected.")
            return redirect('patient:vaccinebooking')
      

def load_vaccinebyhospital(request, h_id=None):
    if h_id is not None:
        # Called internally — no child filtering needed here
        vaccines = Vaccinetbl.objects.filter(hospitalId=h_id).order_by('-id')
        return vaccines
    else:
        h_id = request.GET.get('h_id')
        child_id = request.GET.get('child_id')  # new optional param from booking form
        vlist = Vaccinetbl.objects.filter(hospitalId=h_id).order_by('-id')
        # Exclude vaccines this child has already booked or taken at this hospital
        if child_id and child_id.isdigit():
            booked_vaccine_ids = Appointmenttbl.objects.filter(
                child_id=int(child_id),
                hospitalid_id=h_id
            ).values_list('vaccineid_id', flat=True)
            vlist = vlist.exclude(id__in=booked_vaccine_ids)
        return render(request, 'patientapp/hospitaltovaccine.html', {'vaccinelist': vlist})


def recommend_vaccines(request):
    """GET /recommend-vaccines/?child_id=X&hospital_id=Y
    Returns a JSON list of age-appropriate vaccines not yet booked for this child.
    Returns [] safely on any error — never breaks the booking flow.
    """
    from patientapp.vaccine_recommender import get_recommended_vaccines  # type: ignore[import]  # pyre-ignore
    child_id = request.GET.get('child_id', '')
    hospital_id = request.GET.get('hospital_id', '')
    if not child_id.isdigit() or not hospital_id.isdigit():
        return JsonResponse({'vaccines': []})
    recs = get_recommended_vaccines(int(child_id), int(hospital_id))
    data = [
        {'id': v.pk, 'name': v.vaccineName, 'description': getattr(v, 'description', '')}
        for v in recs
    ]
    return JsonResponse({'vaccines': data})


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


class ChangeAuthentication(View):
    def get(self, request):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
            return redirect('patient:loginpage')
        return render(request, 'patientapp/changepassword.html')
    
    def post(self,request):
        passwd = Patienttbl.objects.filter(id = request.session.get('Cid')).values('password').distinct()
        if str(passwd[0]['password']) != str(request.POST.get('cpass')):
            messages.warning(request,'Current Password is Not Valid!')
            return render(request,'patientapp/changepassword.html')
        elif str(request.POST.get('password')) != str(request.POST.get('cfpass')):
            messages.warning(request,'New Password and Confirm Password do not match!')
            return render(request,'patientapp/changepassword.html')
        elif str(request.POST.get('cpass')) == str(request.POST.get('password')):
            messages.warning(request, 'Security Alert: New Password cannot be identical to your Current Password.')
            return render(request,'patientapp/changepassword.html')
        else:
            UpdateData = Patienttbl.objects.get(id = request.session.get('Cid'))
            UpdateData.password = request.POST.get('password')
            UpdateData.save(update_fields= ['password']) 
            messages.info(request,'Password changed successfully on next login!')     
            return redirect('patient:changeauth')

class PatientProfile(View):
    def get(self, request):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
            return redirect('patient:loginpage')
        bindCity = City.objects.all().order_by('-id')
        patientData = Patienttbl.objects.get(id=request.session.get('Cid'))
        bindArea = Area.objects.filter(cityId=patientData.cityId).order_by('-id')
        form = PatientForm(instance=patientData)
        from patientapp.models import Childtbl  # type: ignore[import]  # pyre-ignore
        children = Childtbl.objects.filter(patient_id=request.session.get('Cid')).prefetch_related(
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
        if request.session.get('CName') is None:
            return redirect('patient:loginpage')
            
        action = request.POST.get('action')
        if action == 'add_child':
            from patientapp.models import Childtbl  # type: ignore[import]  # pyre-ignore
            Childtbl.objects.create(
                patient_id=request.session.get('Cid'),
                childname=request.POST.get('childname'),
                dob=request.POST.get('dob'),
                gender=request.POST.get('gender')
            )
            messages.info(request, "Child profile added successfully!")
            return redirect('patient:profilepage')
        elif action == 'delete_child':
            from patientapp.models import Childtbl  # type: ignore[import]  # pyre-ignore
            Childtbl.objects.filter(id=request.POST.get('child_id'), patient_id=request.session.get('Cid')).delete()
            messages.info(request, "Child profile removed successfully!")
            return redirect('patient:profilepage')
            
        patientData = Patienttbl.objects.get(id=request.session.get('Cid'))
        
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
        bindData = Vaccinetbl.objects.select_related("hospitalId").all().order_by('id')
        context={
                'hospitalData' : bindHospital,
                'bindData' : bindData,
        }
        return render(request,'patientapp/showvaccines.html',context)
    def post(self, request):
        pass   

def loadVaccines(request,h_id=None):
    h_id = request.GET.get("h_id")
   
    if int(h_id) >0:
       
        vlist = Vaccinetbl.objects.filter(hospitalId=h_id).order_by('id')
        return render(request, 'patientapp/loadvaccinerecord.html', {'bindData': vlist})                     
    else:
        vlist = Vaccinetbl.objects.select_related("hospitalId").all().order_by('id')
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
