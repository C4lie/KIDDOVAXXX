from django.urls import path
from receptionistapp import views

app_name = 'receptionist'
urlpatterns = [
    path('logout/', views.Logout, name='logout'),
    path('', views.Home, name='receptionisthome'),
    path('login/', views.ReceptionistLogin.as_view(), name='receptionistlogin'),
    path('booking/', views.ManagePatient.as_view(), name='managepatients'),
    path('showbooking/<int:id>/', views.ManagePatient.as_view(), name='showappointment'),
    
]
