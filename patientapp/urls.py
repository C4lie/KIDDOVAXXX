from . import views
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
    path('profile/', views.PatientProfile.as_view(), name='profilepage'),
    path('viewvaccines/', views.ViewVaccineList.as_view(), name='showdata'),
    path('loadvaccinedata/', views.loadVaccines, name='loaddata'),
    path('child-history/<int:child_id>/', views.ChildVaccinationHistory.as_view(), name='child_history'),
    path('recommend-vaccines/', views.recommend_vaccines, name='recommend_vaccines'),
    path('missed-vaccines/', views.missed_vaccines, name='missed_vaccines'),
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('sms-response/', views.sms_response, name='sms_response'),
]
