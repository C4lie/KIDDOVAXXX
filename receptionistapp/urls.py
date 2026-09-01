from django.urls import path
from receptionistapp import views

app_name = 'receptionist'
urlpatterns = [
    path('logout/', views.Logout, name='logout'),
    path('', views.Home, name='receptionisthome'),
    path('login/', views.ReceptionistLogin.as_view(), name='receptionistlogin'),
    path('booking/', views.ManagePatient.as_view(), name='managepatients'),
    path('showbooking/<int:id>/', views.ManagePatient.as_view(), name='showappointment'),

    # RFID & Smart Check-in APIs
    path('api/rfid/scan/', views.rfid_scan_api, name='rfid_scan_api'),
    path('api/rfid/generate/', views.rfid_generate_api, name='rfid_generate_api'),
    path('api/rfid/link/', views.rfid_link_api, name='rfid_link_api'),
    path('api/rfid/checkin/', views.rfid_checkin_api, name='rfid_checkin_api'),
    path('api/pending-registrations/', views.rfid_pending_list_api, name='pending_registrations_api'),
    path('api/rfid/assign-pending/', views.rfid_assign_pending_api, name='rfid_assign_pending_api'),
    path('api/registered-users/search/', views.registered_user_search_api, name='registered_user_search_api'),
]
