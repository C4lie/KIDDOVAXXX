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
  
    return redirect('hospitalapp:hospitallogin')

def Home(request):
    storage = messages.get_messages(request)
    for message in storage:
        pass
    
    if request.session.get('CName') is None:
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
                loggedname = Hospitaltbl.objects.filter(contactNo=scontact).values('id', 'title')
                request.session['CName'] = loggedname[0]['title']
                request.session['Cid'] = loggedname[0]['id']
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
        
        import json
        context={
            'form' : form,
            'vaccinedata' : vaccineData,
            'vaccine_descriptions_json': json.dumps(VACCINE_DESCRIPTIONS)
        }
        return render(request, 'hospitalapp/managevaccine.html',context)    

    def post(self, request,id=None):
        if 'btnreset' in request.POST and request.method == 'POST':
            form = VaccineForm()
            return redirect('hospitalapp:vaccineregister')

        vName = request.POST["vaccineName"]
        hosp_id = request.session.get('Cid')
        name_exists = Vaccinetbl.objects.filter(vaccineName=vName, hospitalId_id=hosp_id)
        if id is not None:
            name_exists = name_exists.exclude(pk=id)
        if name_exists.exists():
            messages.info(request, 'This Vaccine Name is already taken in your inventory!')
            return redirect('hospitalapp:vaccineregister')

        if  id is not None:  # Update Record
            data = Vaccinetbl.objects.get(pk = id)
            form = VaccineForm(request.POST ,instance  = data)
            if form.is_valid():
                updated_data = form.save(commit=False)
                updated_data.stock_quantity = int(request.POST.get('stock_quantity', 0))
                updated_data.minimum_quantity = int(request.POST.get('minimum_quantity', 5))
                updated_data.save()
            messages.info(request,'Vaccine Updated Success!')
        else:               # Insert Record
            form = VaccineForm(request.POST)
           
            if form.is_valid():
                data = form.save(commit=False)
                data.vaccineName=  request.POST.get('vaccineName')
                data.vaccineDescr = request.POST.get('vaccineDescr')
                data.price = request.POST.get('price')
                data.stock_quantity = int(request.POST.get('stock_quantity', 0))
                data.minimum_quantity = int(request.POST.get('minimum_quantity', 5))
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
        getData = Appointmenttbl.objects.all().filter(hospitalid=request.session.get('Cid'),aptdate__gte=datetime.datetime.now().date()).exclude(active=2).order_by('-id')
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
        getData = Appointmenttbl.objects.all().filter(hospitalid=request.session.get('Cid'),active=2).order_by('-id')
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