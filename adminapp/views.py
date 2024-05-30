from django.shortcuts import render, redirect
from adminapp.models import City,Area,Admintbl
from django.views import  View
from hospitalapp.models import Hospitaltbl
from hospitalapp.forms import HospitalForm
from django.contrib import messages
from django.contrib.auth.models import User, auth
from adminapp.forms import CityForm, AreaForm, AdminForm
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
# Create your views here.

def Logout(request):
    storage = messages.get_messages(request)
    for message in storage:
        message = None
    storage.used = False
    logout(request)
    Session.objects.all().delete()
  
    return render(request, 'adminapp/login.html')
    

class AdminCreation(View):
    def get(self, request):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
          return redirect('adminapp:adminlogin') 
        adminData = Admintbl.objects.all().order_by('-id')
        form = AdminForm()
        context={
            'form' : form,
            'adminData' : adminData
        }
        return render(request, 'adminapp/createadmin.html',context)
    
    def post(self, request):
        form = AdminForm(request.POST)
        messages.info(request,'New Admin Inserted Success!')
        form.save()
        adminData = Admintbl.objects.all().order_by('-id')
        form = AdminForm()
        context={
            'form' : form,
            'adminData' : adminData
        }
        return render(request, 'adminapp/createadmin.html',context)

class AdminLogin(View):
    def get(self, request):  

        return render(request, 'adminapp/login.html')
    
    def post(self, request):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        scontact = request.POST.get('username')
        spassword = request.POST.get('password')
      
        try:
            checkusername = Admintbl.objects.get(username = scontact)
        except:
            checkusername = None   
                     
        if checkusername is not None:
            checkcontactpasswordboth = Admintbl.objects.filter(username=scontact,password=spassword).exists()
            if checkcontactpasswordboth:
                #loggedname = CustomerModel.objects.only('name').get(contactno=scontact)
                loggedname = Admintbl.objects.filter(username=scontact).values('username')
                request.session['CName'] =loggedname[0]['username']
                return redirect('adminapp:adminhome')
            else:
                messages.info(request,'Invalid Password')                
        else:
            messages.info(request,'Invalid Username')

        return render(request,'adminapp/login.html') 

def Home(request):
    storage = messages.get_messages(request)
    for message in storage:
        message = None
    if request.session.get('CName') is None:
        return redirect('adminapp:adminlogin') 
    return render(request,'adminapp/home.html')

class ManageCity(View):
    def get(self, request,id=None,cityid=None):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
           return redirect('adminapp:adminlogin')  
         

        if cityid is not None:
            data = City.objects.get(pk = cityid)
            data.delete()
            cityid = None
            messages.info(request,'City Deleted Success!')
            return redirect('adminapp:city') 
        if id is not None:
            data = City.objects.get(pk = id)
            form = CityForm(instance  = data)   
        else:    
            form = CityForm()

        cityData = City.objects.all().order_by('-id')
        context={
            'form' : form,
            'citydata' : cityData
        }
        return render(request, 'adminapp/city.html',context)    

    def post(self, request,id=None):
        if 'btnreset' in request.POST and request.method == 'POST':
            form = CityForm()
            return redirect('adminapp:city')

        cityName = request.POST["cityName"]
        if City.objects.filter(cityName=cityName).exists():
            messages.info(request, 'This city is already taken!')
            return redirect('adminapp:city')

        if  id is not None:  # Update Record
            data = City.objects.get(pk = id)
            form = CityForm(request.POST ,instance  = data)
            messages.info(request,'City Updated Success!')
        else:               # Insert Record
            form = CityForm(request.POST)
            messages.info(request,'City Inserted Success!')
        form.save()
        return redirect('adminapp:city')


def load_areasbyCity(request, cityid=None):
    if cityid is not None:
        city_id = cityid
        areas = Area.objects.filter(cityId=city_id).order_by('areaName')
        return areas
    else:     
        city_id = request.GET.get('city_id')
        areas = Area.objects.filter(cityId=city_id).order_by('areaName')
        return render(request, 'adminapp/citytoarea.html', {'arealist': areas}) 
    

class ManageArea(View):
    def get(self, request, id=None, areaid=None):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
           return redirect('adminapp:adminlogin')

        if areaid is not None:
            data = Area.objects.get(pk = areaid)
            data.delete()
            areaid = None
            messages.info(request,'Area Deleted Success!')
            return redirect('adminapp:area')   
              
        form = AreaForm()
        bindCity  = City.objects.all().order_by('-id')
        bindData = Area.objects.select_related("cityId").all().order_by('-id')
        if id is not None:
            data = Area.objects.get(pk = id)
            form = AreaForm(instance  = data)
            selectedCity = data.cityId
            context={
                'cityData' : bindCity,
                'form' : form,
                'areaData' : bindData,
                'selectedCity' : selectedCity
            }
        else:
            form = AreaForm()    
            context={
                'cityData' : bindCity,
                'form' : form,
                'areaData' : bindData
            }
        return render(request,'adminapp/area.html',context)

    def post(self, request, id=None):
        if 'btnreset' in request.POST and request.method == 'POST':
            form = AreaForm()
            return redirect('adminapp:area')
        if id is not None:
            data = Area.objects.get(pk = id)
            form = AreaForm(request.POST, instance  = data)
            messages.info(request,'Area Updated Success!')
        else:            
            form = AreaForm(request.POST)
            messages.info(request,'Area Inserted Success!')
        form.save()
        return redirect('adminapp:area')

def load_areasbyCity(request, cityid=None):
    if cityid is not None:
        city_id = cityid
        areas = Area.objects.filter(cityId=city_id).order_by('areaName')
        return areas
    else:     
        city_id = request.GET.get('city_id')
        areas = Area.objects.filter(cityId=city_id).order_by('areaName')
        return render(request, 'adminapp/citytoarea.html', {'arealist': areas})        


class ManageHospitals(View):
    def get(self, request, id=None, pid=None):
        storage = messages.get_messages(request)
        for message in storage:
            message = None
        if request.session.get('CName') is None:
           return redirect('adminapp:adminlogin')
        form = HospitalForm()
        bindCity = City.objects.all().order_by('-id')
        bindData = Hospitaltbl.objects.select_related("cityId").select_related("areaId").all().order_by('-id')

        if pid is not None:
            data = Hospitaltbl.objects.get(pk = pid)
            data.delete()
            pid = None
            messages.info(request,'Hospital Deleted Success!')
            return redirect('adminapp:addhospitals')

        if id is not None:
        
            pimg = Hospitaltbl.objects.only('img').get(pk=id)
            Pdata = Hospitaltbl.objects.get(pk = id)
            form = HospitalForm(instance = Pdata)  
            bindArea = load_areasbyCity(request,Pdata.cityId)
            selectedArea = Pdata.areaId
            context={
                'form' : form,
                'hospitalData' : bindData,
                'imgurl' : pimg,
                'cityData' : bindCity,
                'areaData' : bindArea,
                'selectedCity' : Pdata.cityId,
                'selectedArea' : selectedArea,
            }
            return render(request, 'adminapp/hospitalreg.html',context)   
    
       
        context={
                'cityData' : bindCity,
                'hospitalData' : bindData,
                'form' : form
        }
        return render(request, 'adminapp/hospitalreg.html', context)
    
    def post(self, request, id=None):
        if 'btnreset' in request.POST and request.method == 'POST':
            form = HospitalForm()
            return redirect('adminapp:addhospitals')
        if id is not None:
            data = Hospitaltbl.objects.get(pk = id)
            form = HospitalForm(request.POST,request.FILES or None, instance  = data)
            form.save()
            messages.info(request,'Hospital Updated Success!')
        else:    
            form = HospitalForm(request.POST,request.FILES or None)
            messages.info(request,'Hospital Inserted Success!')
            form.save()
        return redirect('adminapp:addhospitals')