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
    path('force-change-password/', views.ForcePasswordChange.as_view(), name='force_password_change'),
    path('pending-registration/', views.PendingRegistrationView.as_view(), name='pending_registration'),
    path('profile/', views.PatientProfile.as_view(), name='profilepage'),
    path('viewvaccines/', views.ViewVaccineList.as_view(), name='showdata'),
    path('loadvaccinedata/', views.loadVaccines, name='loaddata'),
    path('child-history/<int:child_id>/', views.ChildVaccinationHistory.as_view(), name='child_history'),
    
    # Feature 4 & 5
    path('journey/', views.VaccinationJourneyView.as_view(), name='journey'),
    path('journey/<int:child_id>/', views.VaccinationJourneyView.as_view(), name='journey_child'),
    path('education/', views.VaccineEducationView.as_view(), name='education'),

    path('recommend-vaccines/', views.recommend_vaccines, name='recommend_vaccines'),
    path('missed-vaccines/', views.missed_vaccines, name='missed_vaccines'),
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('sms-response/', views.sms_response, name='sms_response'),
    path('download-card/<int:child_id>/', views.download_vaccine_card, name='download_vaccine_card'),
    path('upload-card/', views.upload_vaccine_card_ocr, name='upload_vaccine_card_ocr'),
    path('confirm-ocr/', views.confirm_ocr_results, name='confirm_ocr_results'),
    path('set-lang/', views.set_language, name='set_language'),
    path('get-slots/', views.get_available_slots, name='get_available_slots'),
    path('get-hospitals-for-date/', views.get_hospitals_for_date, name='get_hospitals_for_date'),
    path('update-location/', views.update_location, name='update_location'),
]

