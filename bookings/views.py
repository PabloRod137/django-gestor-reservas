"""
Vistas de la app "bookings".

Hay una mezcla de vistas basadas en clases (las de solo lectura, donde no
necesitamos lógica extra) y vistas de función (donde sí hay decisiones de
negocio: crear una reserva, cancelarla, generar recurrencias...). En un
proyecto de aprendizaje como este, mezclar ambos estilos es intencionado:
sirve para ver las dos formas que ofrece Django de escribir una vista.
"""

import datetime

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .forms import BookingForm, SignUpForm
from .models import Booking, Resource


def signup(request):
    """Registro de un usuario nuevo. Si todo va bien, lo deja logueado directamente."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cuenta creada correctamente. ¡Bienvenido!')
            return redirect('booking_list')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


class ResourceListView(ListView):
    """Listado público (no hace falta estar logueado) de los recursos que se pueden reservar."""

    model = Resource
    template_name = 'bookings/resource_list.html'
    context_object_name = 'resources'

    def get_queryset(self):
        # Solo mostramos los recursos activos: los desactivados siguen
        # existiendo en la base de datos (por su historial de reservas),
        # pero no queremos que se puedan reservar de nuevo.
        return Resource.objects.filter(is_active=True)


class ResourceDetailView(DetailView):
    """Ficha de un recurso: su disponibilidad semanal y sus próximas reservas confirmadas."""

    model = Resource
    template_name = 'bookings/resource_detail.html'
    context_object_name = 'resource'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['availabilities'] = self.object.availabilities.all()
        context['upcoming_bookings'] = self.object.bookings.filter(
            status=Booking.STATUS_CONFIRMED,
            # OJO: usamos timezone.now() (que devuelve un datetime "aware",
            # en UTC) y NO datetime.datetime.now() (que sería "naive"). Como
            # en la base de datos las fechas se guardan en UTC (USE_TZ=True),
            # comparar con un datetime naive haría que Django asumiera una
            # zona horaria incorrecta y el filtro de "próximas reservas"
            # podría dejar fuera (o dentro) reservas equivocadas cerca de
            # medianoche. timezone.now() es la forma correcta de obtener
            # "el instante actual" en cualquier vista o modelo de Django.
            end_datetime__gte=timezone.now(),
        ).order_by('start_datetime')
        return context


@login_required
def booking_list(request):
    """"Mis reservas": todas las reservas (confirmadas o canceladas) del usuario que ha iniciado sesión."""
    bookings = Booking.objects.filter(user=request.user).select_related('resource')
    return render(request, 'bookings/booking_list.html', {'bookings': bookings})


def _generate_occurrences(start_datetime, end_datetime, recurrence, recurrence_end):
    """
    Calcula las fechas concretas (inicio, fin) de cada repetición de una
    reserva recurrente, desde la primera hasta 'recurrence_end' incluido.

    Por ejemplo, con recurrence='weekly', esto genera una tupla por cada
    semana entre la fecha de inicio y recurrence_end, manteniendo siempre
    la misma duración (end - start) que la reserva original.
    """
    duration = end_datetime - start_datetime
    step = datetime.timedelta(days=1) if recurrence == Booking.RECURRENCE_DAILY else datetime.timedelta(weeks=1)
    occurrences = []
    current_start = start_datetime
    while current_start.date() <= recurrence_end:
        occurrences.append((current_start, current_start + duration))
        current_start += step
    return occurrences


@login_required
def booking_create(request):
    """
    Crea una reserva (o varias, si es recurrente).

    La estrategia para las recurrentes es sencilla a propósito: en vez de
    guardar "una regla de repetición" y calcularla al vuelo cada vez (lo que
    sería más complejo), generamos de golpe todas las reservas individuales
    que le corresponden y las guardamos una a una. Si alguna de esas fechas
    ya está ocupada (solapa con otra reserva), esa fecha en concreto se
    salta y se avisa al usuario, pero el resto de fechas sí se reservan.
    """
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            recurrence = form.cleaned_data['recurrence']
            recurrence_end = form.cleaned_data.get('recurrence_end')
            resource = form.cleaned_data['resource']
            start_datetime = form.cleaned_data['start_datetime']
            end_datetime = form.cleaned_data['end_datetime']
            notes = form.cleaned_data['notes']

            if recurrence != Booking.RECURRENCE_NONE and recurrence_end:
                occurrences = _generate_occurrences(start_datetime, end_datetime, recurrence, recurrence_end)
                # Todas las reservas de esta serie comparten el mismo id de
                # grupo, para poder identificarlas como "el mismo lote" más
                # adelante si hiciera falta (por ejemplo, cancelarlas todas).
                group_id = Booking.new_recurrence_group()
            else:
                occurrences = [(start_datetime, end_datetime)]
                group_id = None

            created, skipped = 0, []
            for occ_start, occ_end in occurrences:
                booking = Booking(
                    resource=resource,
                    user=request.user,
                    start_datetime=occ_start,
                    end_datetime=occ_end,
                    notes=notes,
                    recurrence=recurrence,
                    recurrence_group=group_id,
                )
                try:
                    # full_clean() ejecuta las validaciones del modelo,
                    # incluida la de solapamiento (Booking.clean()). Si
                    # salta una excepción, esta fecha en concreto no se
                    # guarda, pero seguimos intentando con las demás.
                    booking.full_clean()
                    booking.save()
                    created += 1
                except ValidationError:
                    skipped.append(occ_start)

            if created:
                messages.success(request, f'{created} reserva(s) creada(s) correctamente.')
            if skipped:
                # timezone.localtime() convierte cada fecha (guardada/calculada
                # en UTC internamente) a la hora de Madrid antes de mostrarla,
                # para que el mensaje de aviso coincida con lo que el usuario
                # esperaría ver.
                fechas = ', '.join(f'{timezone.localtime(d):%d/%m/%Y %H:%M}' for d in skipped)
                messages.warning(request, f'No se pudieron reservar estas fechas por solapamiento: {fechas}')
            if created:
                return redirect('booking_list')
    else:
        form = BookingForm()
    return render(request, 'bookings/booking_form.html', {'form': form})


@login_required
def booking_cancel(request, pk):
    """
    Cancela una reserva propia.

    No la borramos de la base de datos: cambiamos su estado a "cancelada".
    Así conservamos el historial y, muy importante, una reserva cancelada
    deja de contar para el cálculo de solapamientos (ver
    Booking.overlapping_bookings, que solo mira reservas confirmadas), así
    que ese hueco vuelve a quedar libre para otros usuarios.
    """
    # get_object_or_404 con user=request.user asegura, en una sola
    # consulta, que un usuario no pueda cancelar la reserva de otro
    # simplemente cambiando el número en la URL.
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if request.method == 'POST':
        booking.status = Booking.STATUS_CANCELLED
        booking.save()
        messages.success(request, 'Reserva cancelada.')
        return redirect('booking_list')
    return render(request, 'bookings/booking_confirm_cancel.html', {'booking': booking})
