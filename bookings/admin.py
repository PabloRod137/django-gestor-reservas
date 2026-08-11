from django.contrib import admin

from .models import Availability, Booking, Resource


class AvailabilityInline(admin.TabularInline):
    model = Availability
    extra = 1


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
    date_hierarchy = 'start_datetime'
