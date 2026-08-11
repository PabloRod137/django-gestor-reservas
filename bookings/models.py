import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Resource(models.Model):
    name = models.CharField('nombre', max_length=120)
    description = models.TextField('descripción', blank=True)
    location = models.CharField('ubicación', max_length=120, blank=True)
    capacity = models.PositiveIntegerField('aforo', default=1)
    is_active = models.BooleanField('activo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'recurso'
        verbose_name_plural = 'recursos'

    def __str__(self):
        return self.name


class Availability(models.Model):
    WEEKDAYS = [
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'),
        (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo'),
    ]

    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='availabilities')
    weekday = models.PositiveSmallIntegerField('día de la semana', choices=WEEKDAYS)
    start_time = models.TimeField('hora de inicio')
    end_time = models.TimeField('hora de fin')

    class Meta:
        ordering = ['weekday', 'start_time']
        verbose_name = 'disponibilidad'
        verbose_name_plural = 'disponibilidades'

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('La hora de inicio debe ser anterior a la hora de fin.')

    def __str__(self):
        return f'{self.resource} — {self.get_weekday_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}'


class Booking(models.Model):
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_CONFIRMED, 'Confirmada'),
        (STATUS_CANCELLED, 'Cancelada'),
    ]

    RECURRENCE_NONE = 'none'
    RECURRENCE_DAILY = 'daily'
    RECURRENCE_WEEKLY = 'weekly'
    RECURRENCE_CHOICES = [
        (RECURRENCE_NONE, 'No recurrente'),
        (RECURRENCE_DAILY, 'Diaria'),
        (RECURRENCE_WEEKLY, 'Semanal'),
    ]

    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='bookings', verbose_name='recurso')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    start_datetime = models.DateTimeField('inicio')
    end_datetime = models.DateTimeField('fin')
    status = models.CharField('estado', max_length=20, choices=STATUS_CHOICES, default=STATUS_CONFIRMED)
    recurrence = models.CharField('recurrencia', max_length=10, choices=RECURRENCE_CHOICES, default=RECURRENCE_NONE)
    recurrence_group = models.UUIDField(null=True, blank=True, editable=False)
    notes = models.TextField('notas', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_datetime']
        verbose_name = 'reserva'
        verbose_name_plural = 'reservas'

    def __str__(self):
        return f'{self.resource} — {self.start_datetime:%d/%m/%Y %H:%M}'

    def overlapping_bookings(self):
        qs = Booking.objects.filter(
            resource=self.resource,
            status=self.STATUS_CONFIRMED,
            start_datetime__lt=self.end_datetime,
            end_datetime__gt=self.start_datetime,
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        return qs

    def clean(self):
        if self.start_datetime and self.end_datetime and self.start_datetime >= self.end_datetime:
            raise ValidationError('La fecha de inicio debe ser anterior a la fecha de fin.')
        if (
            self.start_datetime and self.end_datetime
            and self.status == self.STATUS_CONFIRMED
            and self.overlapping_bookings().exists()
        ):
            raise ValidationError('Este recurso ya está reservado en ese horario.')

    @staticmethod
    def new_recurrence_group():
        return uuid.uuid4()
