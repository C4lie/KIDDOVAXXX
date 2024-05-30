from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import  View
from hospitalapp.models import Hospitaltbl, Receptionisttbl, Vaccinetbl
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from hospitalapp.forms import ReceptionistForm,VaccineForm
from adminapp.models import City,Area
from patientapp.models import Appointmenttbl
import datetime
# Create your views here.

def Logout(request):
    storage = messages.get_messages(request)
    for message in storage:
        message = None
    storage.used = False
    logout(request)
    Session.objects.all().delete()
  
    return render(request, 'hospitalapp/login.html')

def Home(request):
    storage = messages.get_messages(request)
    for message in storage:
        message = None
    if request.session.get('CName') is None:
        return redirect('hospitalapp:hospitallogin') 
    return render(request,'hospitalapp/home.html')

class HospitalLogin(View):
    def get(self, request):  

        return render(request, 'hospitalapp/login.html')
    
    def post(self, request):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        scontact = request.POST.get('contact')
        spassword = request.POST.get('password')
      
        try:
            checkusername = Hospitaltbl.objects.get(contactNo = scontact)
        except:
            checkusername = None   
                     
        if checkusername is not None:
            checkcontactpasswordboth = Hospitaltbl.objects.filter(contactNo=scontact,password=spassword).exists()
            if checkcontactpasswordboth:
                #loggedname = CustomerModel.objects.only('name').get(contactno=scontact)
                loggedname = Hospitaltbl.objects.filter(contactNo=scontact).values('id', 'dcrname')
                request.session['CName'] =loggedname[0]['dcrname']
                request.session['Cid'] =loggedname[0]['id']
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
            SelectedGender = Receptionisttbl.objects.get(pk = id)
            pimg = Receptionisttbl.objects.only('staffimg').get(pk=id)
            Pdata = Receptionisttbl.objects.get(pk = id)
            form = ReceptionistForm(instance = Pdata)  
            bindArea = load_areasbyCity(request,Pdata.cityId)
            selectedArea = Pdata.areaId
            context={
                'form' : form,
                'ReceptionistData' : bindData,
                'imgurl' : pimg,
                'cityData' : bindCity,
                'areaData' : bindArea,
                'selectedCity' : Pdata.cityId,
                'selectedArea' : selectedArea,
                'selGender' : SelectedGender.gender
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
            form = ReceptionistForm()
            return redirect('hospitalapp:receptionistregister')
        if id is not None:
            data = Receptionisttbl.objects.get(pk = id)
            form = ReceptionistForm(request.POST,request.FILES or None, instance  = data)
            data = form.save(commit=False)
            data.hospitalid_id = request.session['Cid']
             
            data.name = request.POST.get('name')
            data.address = request.POST.get('address')
            data.gender = request.POST.get('gender')
            data.contactNo = request.POST.get('contactNo')
            data.password = request.POST.get('password')
            if request.FILES.get('staffimg') is not None:
                data.staffimg  = request.FILES.get('staffimg')
                
            data.doj = request.POST.get('doj')
            data.areaId_id = request.POST.get('areaId')
            data.cityId_id = request.POST.get('cityId')
         
            data.save()
            messages.info(request,'Receptionist Updated Success!')
            return redirect('hospitalapp:receptionistregister')
        else:    
            form = ReceptionistForm(request.POST,request.FILES or None)
          
            data = form.save(commit=False)
            data.hospitalid_id = request.session['Cid']
             
            data.name = request.POST.get('name')
            data.address = request.POST.get('address')
            data.gender = request.POST.get('gender')
            data.contactNo = request.POST.get('contactNo')
            data.password = request.POST.get('password')
            data.staffimg  = request.FILES.get('staffimg')
            data.doj = request.POST.get('doj')
            data.areaId_id = request.POST.get('areaId')
            data.cityId_id = request.POST.get('cityId')
         
            data.save()
            messages.info(request,'Receptionist Inserted Success!')
           
        return redirect('hospitalapp:receptionistregister')
    
def load_areasbyCity(request, cityid=None):
    if cityid is not None:
        city_id = cityid
        areas = Area.objects.filter(cityId=city_id).order_by('areaName')
        return areas
    else:     
        city_id = request.GET.get('city_id')
        areas = Area.objects.filter(cityId=city_id).order_by('areaName')
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
        context={
            'form' : form,
            'vaccinedata' : vaccineData
        }
        return render(request, 'hospitalapp/managevaccine.html',context)    

    def post(self, request,id=None):
        if 'btnreset' in request.POST and request.method == 'POST':
            form = VaccineForm()
            return redirect('hospitalapp:vaccineregister')

        vName = request.POST["vaccineName"]
        if Vaccinetbl.objects.filter(vaccineName=vName).exists():
            messages.info(request, 'This Vaccine Name is already taken!')
            return redirect('hospitalapp:vaccineregister')

        if  id is not None:  # Update Record
            data = Vaccinetbl.objects.get(pk = id)
            form = VaccineForm(request.POST ,instance  = data)
            form.save()
            messages.info(request,'Vaccine Updated Success!')
        else:               # Insert Record
            form = VaccineForm(request.POST)
           
            if form.is_valid():
                data = form.save(commit=False)
                data.vaccineName=  request.POST.get('vaccineName')
                data.vaccineDescr = request.POST.get('vaccineDescr')
                data.price = request.POST.get('price')
                data.hospitalId_id = request.session['Cid']
                data.save()
            messages.info(request,'Vaccine Inserted Success!')
      
        return redirect('hospitalapp:vaccineregister')


class ShowAppointments(View):
    def get(self, request, id=None):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
            return redirect('hospitalapp:hospitallogin')
        
        # show data
       
        getData = Appointmenttbl.objects.all().filter(hospitalid=request.session.get('Cid'),aptdate=datetime.datetime.now().date()).order_by('-id')
            #getData  =  Appointmenttbl.objects.filter(id = id).all().order_by('-id')
           
        context={
                'data' : getData,
              
                
        }
        return render(request, 'hospitalapp/showappointment.html', context)     

class ShowPastAppointments(View):
    def get(self, request, id=None):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
            return redirect('hospitalapp:hospitallogin')
        
        # show data
        dt = datetime.datetime.now().date()
        getData = Appointmenttbl.objects.all().filter(hospitalid=request.session.get('Cid'),aptdate__lt = dt).order_by('-id')
            #getData  =  Appointmenttbl.objects.filter(id = id).all().order_by('-id')
           
        context={
                'data' : getData,
              
                
        }
        return render(request, 'hospitalapp/showappointment.html', context)     

       
         
  
        # gethId = Receptionisttbl.objects.filter(id =  request.session.get('Cid')).values('hospitalid_id').distinct()
        # print(gethId)
        Status  =   Appointmenttbl.objects.filter(id = id).values('active').distinct()
        UpdateData = Appointmenttbl.objects.get(id = id)
       
        print(Status[0]['active'])
        if int(Status[0]['active']) == 0:
            UpdateData.rfidno = request.POST.get('rfidno')
            UpdateData.indt =  datetime.datetime.now()
            UpdateData.active = 1
            UpdateData.save(update_fields= ['indt','rfidno','active'])  
        elif int(Status[0]['active']) == 1:
            UpdateData.outdt =  datetime.datetime.now()
            UpdateData.active = 2
            UpdateData.save(update_fields= ['outdt','active'])  

        #return render(request,'receptionistapp/booking.html')
        return redirect('receptionist:managepatients')