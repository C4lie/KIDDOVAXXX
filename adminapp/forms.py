from django import forms
from adminapp.models import City, Area, Admintbl

class AdminForm(forms.ModelForm):
    class Meta:
        model = Admintbl
        fields ='__all__'

        widgets={
            'username': forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'password': forms.TextInput(attrs={'required': True,'class':'form-control'})
        }

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = '__all__'
        
        widgets={
            'cityName': forms.TextInput(attrs={'required': True,'class':'form-control','onkeypress': 'return isNumberKey(event);'})
        }

class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = '__all__'

        widgets={
               'areaName' : forms.TextInput(attrs={'required': True,'class':'form-control','onkeypress': 'return isNumberKey(event);'})
               
        }        