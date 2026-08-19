"""
URLs propias de la app "bookings".

Se incluyen desde config/urls.py con include('bookings.urls'), montadas en
la raíz del sitio (''), así que las rutas de aquí abajo son también las
rutas finales que se ven en el navegador.
"""

from django.urls import path

from . import views

urlpatterns = [
    path('', views.ResourceListView.as_view(), name='resource_list'),
    path('recursos/<int:pk>/', views.ResourceDetailView.as_view(), name='resource_detail'),
    path('reservas/', views.booking_list, name='booking_list'),
    path('reservas/nueva/', views.booking_create, name='booking_create'),
    path('reservas/<int:pk>/cancelar/', views.booking_cancel, name='booking_cancel'),
    path('registro/', views.signup, name='signup'),
]
