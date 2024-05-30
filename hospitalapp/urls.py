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
]
