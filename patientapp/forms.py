from django import forms
from patientapp.models import Patienttbl, Appointmenttbl



class PatientForm(forms.ModelForm):
    class Meta:
        model  = Patienttbl
        exclude = ['account_status', 'must_change_password', 'registered_hospital']

        widgets = {
            'name' : forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'address' : forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'cityId' : forms.TextInput(attrs={'required': True,'onkeypress': 'return isNumberKey(event);','class':'form-control'}),
            'areaId' : forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'contactNo': forms.TextInput(attrs={'required': True, 'maxlength':"10", 'class':'form-control', 'onkeypress': 'return restrictAlphabets(event);'}),
            'password' : forms.PasswordInput(attrs={'required': True,'class':'form-control'}),
        }

class AppointmentForm(forms.ModelForm):
    class Meta:
        model  = Appointmenttbl
        fields  ='__all__'

        