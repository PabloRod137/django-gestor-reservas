"""
URLs raíz del proyecto.

Aquí se combinan las rutas del admin de Django, las de login/logout (que
vienen ya hechas en django.contrib.auth, solo les indicamos qué plantilla
usar) y las propias de la app "bookings", incluidas en bloque desde
bookings/urls.py.
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # LoginView y LogoutView son vistas genéricas que trae Django: no hace
    # falta escribir la lógica de "comprobar usuario y contraseña" a mano,
    # solo indicarle qué plantilla usar para el formulario de login.
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('bookings.urls')),
]
