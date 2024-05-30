from django.db import models


class Admintbl(models.Model):
    username = models.CharField(max_length=100,verbose_name="Username")
    password = models.CharField(max_length=200, verbose_name="Passwords")

    def __str__(self):
        return f'{(self.username), (self.password)}'

class City(models.Model): 
    cityName  = models.CharField(max_length=255, verbose_name='City')

    def __str__(self):
        return self.cityName

class Area(models.Model):
    cityId = models.ForeignKey(City,on_delete=models.CASCADE,verbose_name="City")        
    areaName = models.CharField(max_length=255, verbose_name='Area')

    def __str__(self):
        return f'{(self.areaName) (self.cityId.cityName)}'
    

     
