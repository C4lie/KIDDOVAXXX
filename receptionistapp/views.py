from django.shortcuts import render,redirect
from hospitalapp.models import Receptionisttbl
from django.contrib import messages
from django.views import  View
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from patientapp.forms import AppointmentForm
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
    return render(request, 'receptionistapp/login.html')

def Home(request):
    storage = messages.get_messages(request)
    for message in storage:
        message = None
    if request.session.get('CName') is None:
        return redirect('receptionist:receptionistlogin') 
    return render(request,'receptionistapp/home.html')

class ManagePatient(View):
    def get(self, request, id=None):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
            return redirect('receptionist:receptionistlogin')
        
        # show data
        if id is not None:
            getData  =  Appointmenttbl.objects.filter(id = id).all().order_by('-id')
            form = AppointmentForm()
            context={
                'data' : getData,
                'form' : form
                
            }
            return render(request, 'receptionistapp/showdata.html', context)     

        gethId = Receptionisttbl.objects.filter(id =  request.session.get('Cid')).values('hospitalid_id').distinct()
        # bindData = Appointmenttbl.objects.select_related("hospitalid").select_related("vaccineid").all().filter(patientid_id=request.session.get('Cid')).order_by('-id')
        bindData = Appointmenttbl.objects.filter(hospitalid=gethId[0]['hospitalid_id']).all().order_by('-id')
       
        context={
            'bindData' : bindData,
        }
       
        return render(request, 'receptionistapp/booking.html', context)
    def post(self, request,id=None):
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

class ReceptionistLogin(View):
    def get(self, request):  

        return render(request, 'receptionistapp/login.html')
    
    def post(self, request):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        scontact = request.POST.get('contact')
        spassword = request.POST.get('password')
      
        try:
            checkusername = Receptionisttbl.objects.get(contactNo = scontact)
        except:
            checkusername = None   
                     
        if checkusername is not None:
            checkcontactpasswordboth = Receptionisttbl.objects.filter(contactNo=scontact,password=spassword).exists()
            if checkcontactpasswordboth:
                #loggedname = CustomerModel.objects.only('name').get(contactno=scontact)
                loggedname = Receptionisttbl.objects.filter(contactNo=scontact).values('id', 'name')
                request.session['CName'] =loggedname[0]['name']
                request.session['Cid'] =loggedname[0]['id']
                return redirect('receptionist:receptionisthome')
            else:
                messages.info(request,'Invalid Password')                
        else:
            messages.info(request,'Invalid Contact No.')

        return render(request,'receptionistapp/login.html') 
    

    