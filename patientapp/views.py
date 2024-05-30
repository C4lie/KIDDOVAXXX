from django.shortcuts import render,redirect
from patientapp.forms import PatientForm, AppointmentForm
from django.views  import View
from django.contrib import messages
from adminapp.models import City,Area
from patientapp.models import Patienttbl,Appointmenttbl
from hospitalapp.models import Vaccinetbl, Hospitaltbl
from django.contrib.auth.models import auth
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
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
        
        context={
                'hospitalData' : bindHospital,
                'form' : form,
                'bindData' : bindData
        }
        return render(request,'patientapp/bookvaccine.html',context)
    def post(self, request):
     
        form = AppointmentForm(request.POST)
        if form.is_valid():
        
            data = form.save(commit=False)
            data.childname=  request.POST.get('childname')
            data.hospitalid_id=  request.POST.get('hospitalid')
            data.vaccineid_id  = request.POST.get('vaccineid')
            data.patientid_id = request.session['Cid']
            data.aptdate = request.POST.get('aptdate')
            data.active = 0
            data.save()
            messages.info(request,"Your appointment is successfully booked!")
            return redirect('patient:vaccinebooking')
      

def load_vaccinebyhospital(request, h_id=None):
    if h_id  is not None:
        # v_id = h_id  
        vaccines = Vaccinetbl.objects.filter(hospitalId=h_id).order_by('-id')
        return vaccines
    else:     
        h_id = request.GET.get('h_id')
        vlist = Vaccinetbl.objects.filter(hospitalId=h_id).order_by('-id')
        return render(request, 'patientapp/hospitaltovaccine.html', {'vaccinelist': vlist})    



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
            messages.warning(request,'Current Password and Confirm Password are not match!')
            return render(request,'patientapp/changepassword.html')
        else:
            UpdateData = Patienttbl.objects.get(id = request.session.get('Cid'))
            UpdateData.password = request.POST.get('password')
            UpdateData.save(update_fields= ['password']) 
            messages.info(request,'Password changed successfully on next login!')     
            return redirect('patient:changeauth')
        
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