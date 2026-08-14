from django.urls import path
from hospitalapp import views

app_name = 'hospitalapp'
urlpatterns = [
    path('', views.Home, name='hospitalhome'),
    path('logout/', views.Logout, name='logout'),
    path('login/', views.HospitalLogin.as_view(), name='hospitallogin'),
    path('bindareas/', views.load_areasbyCity, name='load_areas'),
    path('register/', views.ReceptionistRegister.as_view(), name='receptionistregister'),
    path('editreceptionist/<int:id>/', views.ReceptionistRegister.as_view(), name='editdata'),
    path('deletereceptionist/<int:pid>/', views.ReceptionistRegister.as_view(), name='deletedata'),
    path('vaccine/', views.ManageVaccine.as_view(), name='vaccineregister'),
    path('editvaccine/<int:id>/', views.ManageVaccine.as_view(), name='editvaccine'),
    path('deletevaccine/<int:vid>/', views.ManageVaccine.as_view(), name='deletevaccine'),
    path('showbooking/', views.ShowAppointments.as_view(), name='showappointment'),
    path('showpastbooking/', views.ShowPastAppointments.as_view(), name='historyappointment'),
    path('ai-queue/', views.AIQueueView.as_view(), name='ai_queue'),
    path('inventory-forecast/', views.InventoryForecastView.as_view(), name='inventory_forecast'),
    path('record-alerts/', views.RecordAlertsView.as_view(), name='record_alerts'),
    path('resolve-alert/<int:alert_id>/', views.resolve_record_alert, name='resolve_alert'),
    path('schedule-settings/', views.ScheduleSettingsView.as_view(), name='schedule_settings'),

    # Phase 3: Hospital Patient Registration & RFID Assignment
    path('patient-registration/', views.PatientRegistrationView.as_view(), name='patient_registration'),
    path('rfid-management/', views.RFIDManagementView.as_view(), name='rfid_management'),
    path('api/assign-rfid/', views.assign_rfid_api, name='assign_rfid_api'),
    path('api/generate-rfid/', views.generate_rfid_for_hospital, name='generate_rfid_api'),
    path('api/verify-registration/', views.verify_patient_registration_api, name='verify_registration_api'),
    path('api/search-patients/', views.search_pending_patients_api, name='search_patients_api'),
    path('api/deactivate-rfid/', views.deactivate_rfid_api, name='deactivate_rfid_api'),
]

