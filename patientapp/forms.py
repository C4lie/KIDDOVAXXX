from django import forms
from patientapp.models import Patienttbl, Appointmenttbl



class PatientForm(forms.ModelForm):
    class Meta:
        model  = Patienttbl
        fields  ='__all__'

        widgets = {
            'name' : forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'address' : forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'cityId' : forms.TextInput(attrs={'required': True,'onkeypress': 'return isNumberKey(event);','class':'form-control'}),
            'areaId' : forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'contactNo': forms.TextInput(attrs={'required': True, 'maxlength':"10", 'class':'form-control', 'onkeypress': 'return restrictAlphabets(event);'}),
            'password' : forms.PasswordInput(attrs={'required': True,'class':'form-control'}),
            'rfidno': forms.TextInput(attrs={'required': True, 'maxlength':"20", 'class':'form-control', 'onkeypress': 'return restrictAlphabets(event);'}),
        }

class AppointmentForm(forms.ModelForm):
    class Meta:
        model  = Appointmenttbl
        fields  ='__all__'

        