from django.urls import path
from . import views

urlpatterns = [
    # Autenticacion basica y pagina protegida principal
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Recuperación de contraseña (flujo de 3 pasos)
    path('recuperar-password/', views.recuperar_password_view, name='recuperar_password'),
    path('verificar-codigo/', views.verificar_codigo_view, name='verificar_codigo'),
    path('nueva-password/', views.nueva_password_view, name='nueva_password'),
]
