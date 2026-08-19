"""
Modelos de la app "bookings".

Aquí vive toda la lógica de negocio del Gestor de Reservas: qué recursos
existen, cuándo están disponibles y qué reservas se han hecho sobre ellos.

Hay tres modelos y se relacionan así:

    Resource (1) ---- (N) Availability   -> franjas horarias en las que el recurso se puede reservar
    Resource (1) ---- (N) Booking        -> reservas concretas hechas por un usuario
"""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Resource(models.Model):
    """
    Un recurso reservable: una sala, una pista deportiva, una furgoneta...
    cualquier cosa que un usuario pueda reservar durante un rango de tiempo.
    """

    name = models.CharField('nombre', max_length=120)
    description = models.TextField('descripción', blank=True)
    location = models.CharField('ubicación', max_length=120, blank=True)
    capacity = models.PositiveIntegerField('aforo', default=1)
    # Permite "desactivar" un recurso sin borrarlo (y sin perder su historial de reservas).
    is_active = models.BooleanField('activo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'recurso'
        verbose_name_plural = 'recursos'

    def __str__(self):
        # Esto es lo que se ve en el admin de Django y en los desplegables de formularios.
        return self.name


class Availability(models.Model):
    """
    Una franja horaria semanal en la que un recurso puede reservarse.

    Por ejemplo: "Sala A, los Lunes, de 09:00 a 14:00". No representa una
    fecha concreta, sino un patrón que se repite cada semana. Se gestiona
    desde el panel de administración (como línea "inline" dentro del recurso).

    Nota: de momento esto es solo informativo (se muestra en la ficha del
    recurso para que el usuario sepa cuándo suele estar disponible), pero
    el sistema NO impide crear una reserva fuera de estas franjas. Sería
    una buena mejora futura añadir esa validación en Booking.clean().
    """

    # Django no tiene una constante para "día de la semana" en abstracto,
    # así que definimos nuestras propias choices (0 = lunes, igual que
    # datetime.weekday(), para que sea fácil cruzar datos si hace falta).
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
        # clean() es el método que Django llama para validaciones "de negocio"
        # que no se pueden expresar solo con los tipos de campo (a diferencia
        # de max_length o unique, por ejemplo). Se ejecuta al hacer
        # full_clean(), que es lo que usan tanto los ModelForm como el admin.
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('La hora de inicio debe ser anterior a la hora de fin.')

    def __str__(self):
        # TimeField no lleva zona horaria (a diferencia de DateTimeField), así
        # que aquí formatear directamente con strftime es seguro: no hay
        # conversión de zona horaria de por medio.
        return f'{self.resource} — {self.get_weekday_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}'


def _formatear_fecha_local(dt):
    """
    Convierte un datetime "consciente de zona horaria" (aware) a la hora
    local (Europe/Madrid, según TIME_ZONE en settings.py) y lo formatea
    como texto legible.

    Por qué existe esto: con USE_TZ=True (recomendado por Django), las
    fechas se guardan siempre en la base de datos en UTC. Cuando Django
    las lee de vuelta, el objeto datetime en Python también está en UTC.
    Si formateamos ese datetime directamente con strftime (como hacíamos
    antes de esta corrección), se muestra la hora UTC en vez de la hora
    de Madrid, y en verano (horario de verano, UTC+2) el usuario ve una
    hora que no es la que introdujo. timezone.localtime() hace justo esa
    conversión de UTC -> hora local antes de formatear.
    """
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return f'{dt:%d/%m/%Y %H:%M}'


class Booking(models.Model):
    """
    Una reserva concreta de un recurso, hecha por un usuario, en un rango
    de fechas/horas determinado.

    Las dos reglas de negocio importantes están aquí:
      1) No puede haber dos reservas confirmadas que se solapen en el
         tiempo para el mismo recurso (ver overlapping_bookings/clean).
      2) Las reservas recurrentes (diarias o semanales) se representan
         como varias filas de Booking independientes, todas compartiendo
         el mismo `recurrence_group` (un UUID) para poder identificarlas
         como "parte del mismo lote" si en el futuro se quisiera, por
         ejemplo, cancelarlas todas juntas.
    """

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
    # No lo marcamos como "editable" en formularios: es un dato interno que
    # solo rellena el propio sistema al crear reservas recurrentes en lote.
    recurrence_group = models.UUIDField(null=True, blank=True, editable=False)
    notes = models.TextField('notas', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_datetime']
        verbose_name = 'reserva'
        verbose_name_plural = 'reservas'

    def __str__(self):
        return f'{self.resource} — {_formatear_fecha_local(self.start_datetime)}'

    def overlapping_bookings(self):
        """
        Devuelve las reservas CONFIRMADAS del mismo recurso que se solapan
        en el tiempo con esta reserva (excluyéndose a sí misma si ya existe).

        La condición de solapamiento clásica entre dos intervalos [A, B) y
        [C, D) es: A < D  y  C < B. Aquí "esta reserva" es [start, end) y
        comparamos contra cada reserva existente [start_datetime, end_datetime)
        de la base de datos. Con __lt (menor que) y __gt (mayor que) en vez
        de <=/>=, dos reservas que empiezan justo cuando termina la anterior
        (por ejemplo, una de 10:00 a 11:00 y otra de 11:00 a 12:00) NO se
        consideran solapadas, que es el comportamiento esperado.
        """
        qs = Booking.objects.filter(
            resource=self.resource,
            status=self.STATUS_CONFIRMED,
            start_datetime__lt=self.end_datetime,
            end_datetime__gt=self.start_datetime,
        )
        if self.pk:
            # Si la reserva ya existe (la estamos editando), hay que excluirla
            # de la comparación o siempre "se solaparía consigo misma".
            qs = qs.exclude(pk=self.pk)
        return qs

    def clean(self):
        """
        Validaciones de negocio que se ejecutan antes de guardar (a través
        de full_clean(), que se llama explícitamente en las vistas). Aquí
        es donde se impide de verdad el doble reserva de un mismo recurso.
        """
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
        """Genera un identificador único para agrupar las reservas de una misma serie recurrente."""
        return uuid.uuid4()
