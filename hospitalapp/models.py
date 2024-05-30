from django.db import models
from adminapp.models import City, Area
# Create your models here.
class Hospitaltbl(models.Model):
    title = models.CharField(max_length=500, verbose_name="Title")
    dcrname = models.CharField(max_length=255, blank=True, null=True, default='', verbose_name="Doctor Name")
    address = models.CharField(max_length=500, verbose_name="Address")
    cityId = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="City")
    areaId = models.ForeignKey(Area, on_delete=models.CASCADE, verbose_name="Area")
    contactNo = models.IntegerField(blank=True, null=True,verbose_name="Contact")
    password = models.CharField(max_length=255, verbose_name="Password")
    img = models.ImageField(upload_to='profileimg',blank=True, null=True, verbose_name="Profile Image")

    def HospitalImageUrl(self):
        try:
            url = '../../../static' + self.img.url
        except:
            url ='../../../static/profileimg/noimg.png'            
        return url   
     
    def __str__(self):
        return f'{(self.name)(self.title)(self.drname)(self.address)(self.cityId)(self.areaId)(self.contactNo)(self.password)(self.img)(self.pk)}'
    
class Vaccinetbl(models.Model):
    hospitalId= models.ForeignKey(Hospitaltbl,null=True,blank=True,on_delete=models.CASCADE)
    vaccineName = models.CharField(max_length=255, verbose_name='Vaccine Name')   
    vaccineDescr = models.CharField(max_length=500, verbose_name='Description') 
    price = models.IntegerField(blank=True, null=True, verbose_name='Price')
    
    def __str__(self):
        return f'{(self.hospitalId),(self.vaccineName)(self.vaccineDescr)(self.price)}'

    
class Receptionisttbl(models.Model):
    hospitalid = models.ForeignKey(Hospitaltbl,blank=True, null=True, on_delete=models.CASCADE, verbose_name="Title")    
    name = models.CharField(max_length=255, verbose_name="Name")
    address = models.CharField(max_length=500, verbose_name="Address")
    gender= models.CharField(default='Male',max_length=10, verbose_name="Gender")
    cityId = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="City")
    areaId = models.ForeignKey(Area, on_delete=models.CASCADE, verbose_name="Area")
    contactNo = models.IntegerField(blank=True, null=True,verbose_name="Contact")
    password = models.CharField(max_length=255, verbose_name="Password")
    staffimg = models.ImageField(verbose_name="Upload Image",upload_to='staffimages')
    doj = models.DateField(null=True,verbose_name="DateofJoining")

    def StaffImageUrl(self):
        try:
            url = '../../../static' + self.staffimg.url
        except:
            url ='../../../static/staffimages/noimg.png'            
        return url   
    
    def __str__(self):
        return f'{(self.hospitalid)(self.name)(self.address)(self.gender)(self.cityId)(self.areaId)(self.contactNo)(self.password)(self.staffimg)(self.doj)(self.pk)}'    

# class Vaccinetbl(models.Model):    
#     title = models.CharField(max_length=255, verbose_name="Title")
#     description = models.CharField(max_length=255, verbose_name="Description")
#     price = models.IntegerField(blank=True, null=True,verbose_name="Price")

# class VaccineRecordtbl (models.Model):
        