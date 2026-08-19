"""
Tests automatizados de la app "bookings".

Se centran en las dos reglas de negocio más importantes del proyecto: que
no se puedan solapar dos reservas confirmadas del mismo recurso, y que
cancelar una reserva libere de verdad el hueco para que otra persona
pueda ocuparlo. Para ejecutarlos:

    python manage.py test
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Booking, Resource


class BookingOverlapTests(TestCase):
    def setUp(self):
        self.resource = Resource.objects.create(name='Sala de pruebas', capacity=1)
        self.user = User.objects.create_user('tester', password='TestPass123!')
        # Usamos "mañana" como referencia para no depender de a qué hora
        # exacta se ejecuten los tests.
        self.start = timezone.now() + timedelta(days=1)
        self.end = self.start + timedelta(hours=1)

    def _booking(self, start, end, status=Booking.STATUS_CONFIRMED):
        return Booking(resource=self.resource, user=self.user, start_datetime=start, end_datetime=end, status=status)

    def test_no_permite_reservas_solapadas(self):
        self._booking(self.start, self.end).save()

        # Empieza 30 minutos después de la primera, pero sigue solapando
        # con ella (termina después de que la primera empiece).
        solapada = self._booking(self.start + timedelta(minutes=30), self.end + timedelta(minutes=30))
        with self.assertRaises(ValidationError):
            solapada.full_clean()

    def test_permite_reservas_consecutivas_sin_hueco(self):
        self._booking(self.start, self.end).save()

        # Empieza justo cuando termina la primera: no debería considerarse
        # solapamiento (ver el comentario sobre __lt/__gt en models.py).
        consecutiva = self._booking(self.end, self.end + timedelta(hours=1))
        consecutiva.full_clean()  # no debería lanzar ValidationError
        consecutiva.save()

        self.assertEqual(Booking.objects.filter(resource=self.resource).count(), 2)

    def test_cancelar_una_reserva_libera_el_hueco(self):
        primera = self._booking(self.start, self.end)
        primera.save()
        primera.status = Booking.STATUS_CANCELLED
        primera.save()

        # Mismo horario que la cancelada: ahora debería ser válida.
        nueva = self._booking(self.start, self.end)
        nueva.full_clean()
        nueva.save()

        self.assertEqual(
            Booking.objects.filter(resource=self.resource, status=Booking.STATUS_CONFIRMED).count(), 1,
        )

    def test_fecha_de_fin_anterior_al_inicio_no_es_valida(self):
        invalida = self._booking(self.end, self.start)  # start/end invertidos a propósito
        with self.assertRaises(ValidationError):
            invalida.full_clean()
