from patientapp import views
from django.urls import path

app_name = 'patient'
urlpatterns = [
    path('', views.Home, name='homepage'),
    path('about/', views.About, name='aboutpage'),
    path('contact/', views.Contact, name='contactpage'),
    path('login/', views.PatientLogin.as_view(), name='loginpage'),
    path('register/', views.PatientRegistration.as_view(), name='registerpage'),
    path('logout/',views.PatientLogout.as_view(), name='patientlogout'),
    path('booking/',views.BookedAppointment.as_view(), name='vaccinebooking'),
    path('bindvaccines/', views.load_vaccinebyhospital, name='load_vaccines'),
    path('deletebooking/<int:aid>/', views.BookedAppointment.as_view(), name='deleteappointment'),
    path('changepass/', views.ChangeAuthentication.as_view(), name='changeauth'),
    path('viewvaccines/', views.ViewVaccineList.as_view(), name='showdata'),
    path('loadvaccinedata/', views.loadVaccines, name='loaddata'),
]
  