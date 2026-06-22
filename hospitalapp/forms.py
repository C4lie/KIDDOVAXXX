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
    VACCINE_CHOICES = [
        ('', 'Select Vaccine'),
        ('BCG', 'BCG'),
        ('DTAP1/DTWP1', 'DTAP1/DTWP1'),
        ('DTAP2/DTWP2', 'DTAP2/DTWP2'),
        ('DTAP3/DTWP3', 'DTAP3/DTWP3'),
        ('DTwP/DTap Booster 1', 'DTwP/DTap Booster 1'),
        ('DTwP/DTap Booster 2', 'DTwP/DTap Booster 2'),
        ('Hepatitis B*', 'Hepatitis B*'),
        ('Hepatitis-B 1', 'Hepatitis-B 1'),
        ('Hepatitis-B 2', 'Hepatitis-B 2'),
        ('Hepatitis B 3', 'Hepatitis B 3'),
        ('Hepatitis A1', 'Hepatitis A1'),
        ('HIB1', 'HIB1'),
        ('HIB2', 'HIB2'),
        ('HiB booster', 'HiB booster'),
        ('HPV 1,2 and 3', 'HPV 1,2 and 3'),
        ('Influenza 1', 'Influenza 1'),
        ('Influenza 2', 'Influenza 2'),
        ('Influenza 3', 'Influenza 3'),
        ('Influenza 4', 'Influenza 4'),
        ('Influenza 5', 'Influenza 5'),
        ('Influenza 6', 'Influenza 6'),
        ('IPV+OPV', 'IPV+OPV'),
        ('IPV+OPV1', 'IPV+OPV1'),
        ('IPV+OPV2', 'IPV+OPV2'),
        ('IPV+OPV3', 'IPV+OPV3'),
        ('Meningococcol 1(optional)', 'Meningococcol 1(optional)'),
        ('Meningococcol 2(optional)', 'Meningococcol 2(optional)'),
        ('MMR 1', 'MMR 1'),
        ('MMR 2 with vitamin A', 'MMR 2 with vitamin A'),
        ('MMR 3', 'MMR 3'),
        ('OPV-O', 'OPV-O'),
        ('OPV4', 'OPV4'),
        ('OPV6', 'OPV6'),
        ('OVP5', 'OVP5'),
        ('Pneumococcal 1', 'Pneumococcal 1'),
        ('Pneumococcal 2', 'Pneumococcal 2'),
        ('Pneumococcal 3', 'Pneumococcal 3'),
        ('PCV booster', 'PCV booster'),
        ('Rotavirus1', 'Rotavirus1'),
        ('Rotavirus2', 'Rotavirus2'),
        ('Rotavirus3', 'Rotavirus3'),
        ('Tdap/Td', 'Tdap/Td'),
        ('Typhoid Conjugate', 'Typhoid Conjugate'),
        ('Typhoid Booster 1', 'Typhoid Booster 1'),
        ('Varicella 1', 'Varicella 1'),
        ('Varicella 2', 'Varicella 2'),
        ('COVID-19', 'COVID-19'),
    ]
   
    class Meta:
        model = Vaccinetbl
        fields ='__all__'
     
        widgets={
            'vaccineName': forms.Select(attrs={'required': True, 'class':'form-control'}),
            'vaccineDescr': forms.TextInput(attrs={'required': True,'class':'form-control'}),
            'price': forms.TextInput(attrs={'required': True, 'maxlength':"100", 'class':'form-control', 'onkeypress': 'return restrictAlphabets(event);'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = list(self.VACCINE_CHOICES)
        if self.instance and self.instance.pk and self.instance.vaccineName:
            current_name = self.instance.vaccineName
            if not any(current_name == val for val, label in choices):
                choices.append((current_name, current_name))
        self.fields['vaccineName'].widget.choices = choices

