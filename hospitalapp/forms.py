from django import forms
from hospitalapp.models import Hospitaltbl, Receptionisttbl, Vaccinetbl



class HospitalForm(forms.ModelForm):
    class Meta:
        model = Hospitaltbl
        fields ='__all__'

        widgets={
            'title': forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'dcrname': forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'address': forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'contactNo': forms.TextInput(attrs={'required': True, 'maxlength':"10", 'class':'form-control', 'onkeypress': 'return restrictAlphabets(event);'}),
            'password': forms.TextInput(attrs={'required': True,'class':'form-control'}),
        }



class ReceptionistForm(forms.ModelForm):
   
    class Meta:
        model = Receptionisttbl
        fields ='__all__'
     
        widgets={
            'name': forms.TextInput(attrs={'required': True,'class':'form-control'}),
           
            'address': forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'contactNo': forms.TextInput(attrs={'required': True, 'maxlength':"10", 'class':'form-control', 'onkeypress': 'return restrictAlphabets(event);'}),
            'password': forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'doj' : forms.DateInput(attrs={'type': 'date', 'placeholder': 'yyyy-mm-dd (DOB)','class': 'form-control'})
        }

class VaccineForm(forms.ModelForm):
   
    class Meta:
        model = Vaccinetbl
        fields ='__all__'
     
        widgets={
            'vaccineName': forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'vaccineDescr': forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'price': forms.TextInput(attrs={'required': True, 'maxlength':"100", 'class':'form-control', 'onkeypress': 'return restrictAlphabets(event);'}),
           
        }        

