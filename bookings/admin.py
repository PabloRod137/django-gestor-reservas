"""
Configuración del panel de administración (/admin/) para la app "bookings".

Django genera un CRUD completo automáticamente para cualquier modelo que
registremos aquí con @admin.register(...). Lo que hacemos en este archivo
es personalizar un poco cómo se ve y se busca esa información, no crear
nada desde cero.
"""

from django.contrib import admin

from .models import Availability, Booking, Resource


class AvailabilityInline(admin.TabularInline):
    """
    Permite editar las franjas de disponibilidad de un recurso directamente
    dentro de la propia página del recurso (como una tabla incrustada), en
    vez de tener que ir a una pantalla aparte para cada franja horaria.
    """

    model = Availability
    extra = 1  # cuántas filas vacías se muestran de más, listas para rellenar


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'capacity', 'is_active')
    list_filter = ('is_active', 'location')
    search_fields = ('name', 'location')
    inlines = [AvailabilityInline]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('resource', 'user', 'start_datetime', 'end_datetime', 'status', 'recurrence')
    list_filter = ('status', 'recurrence', 'resource')
    search_fields = ('resource__name', 'user__username')
    # Añade un desplegable de navegación por fechas encima del listado
    # (año -> mes -> día), muy típico para modelos con muchos registros.
    date_hierarchy = 'start_datetime'
