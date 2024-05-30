from django.urls import path
from adminapp import views

app_name = 'adminapp'
urlpatterns = [
    path('', views.Home, name='adminhome'),
    path('logout/', views.Logout, name='logout'),
    path('login/', views.AdminLogin.as_view(), name='adminlogin'),
    path('newadmin/', views.AdminCreation.as_view(), name='admincreation'),
    path('city/', views.ManageCity.as_view(), name='city'),
    path('editcity/<int:id>/',views.ManageCity.as_view(),name='EditCity'),
    path('deletecity/<int:cityid>/',views.ManageCity.as_view(),name='DeleteCity'),
    path('addarea/', views.ManageArea.as_view(), name='area'),
    path('editarea/<int:id>/',views.ManageArea.as_view(),name='EditArea'),
    path('deletearea/<int:areaid>/',views.ManageArea.as_view(),name='DeleteArea'),
    path('bindareas/', views.load_areasbyCity, name='load_areas'),
    path('addhospitals/', views.ManageHospitals.as_view(), name='addhospitals'),
    path('edithospital/<int:id>/', views.ManageHospitals.as_view(), name='edithospitals'),
    path('deletehospital/<int:pid>/', views.ManageHospitals.as_view(), name='deletehospitals'),

]
