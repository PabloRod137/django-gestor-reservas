import datetime

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from .forms import BookingForm, SignUpForm
from .models import Availability, Booking, Resource


def signup(request):
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
    model = Resource
    template_name = 'bookings/resource_list.html'
    context_object_name = 'resources'

    def get_queryset(self):
        return Resource.objects.filter(is_active=True)


class ResourceDetailView(DetailView):
    model = Resource
    template_name = 'bookings/resource_detail.html'
    context_object_name = 'resource'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['availabilities'] = self.object.availabilities.all()
        context['upcoming_bookings'] = self.object.bookings.filter(
            status=Booking.STATUS_CONFIRMED,
            end_datetime__gte=datetime.datetime.now(),
        ).order_by('start_datetime')
        return context


@login_required
def booking_list(request):
    bookings = Booking.objects.filter(user=request.user).select_related('resource')
    return render(request, 'bookings/booking_list.html', {'bookings': bookings})


def _generate_occurrences(start_datetime, end_datetime, recurrence, recurrence_end):
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
                    booking.full_clean()
                    booking.save()
                    created += 1
                except ValidationError:
                    skipped.append(occ_start)

            if created:
                messages.success(request, f'{created} reserva(s) creada(s) correctamente.')
            if skipped:
                fechas = ', '.join(d.strftime('%d/%m/%Y %H:%M') for d in skipped)
                messages.warning(request, f'No se pudieron reservar estas fechas por solapamiento: {fechas}')
            if created:
                return redirect('booking_list')
    else:
        form = BookingForm()
    return render(request, 'bookings/booking_form.html', {'form': form})


@login_required
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if request.method == 'POST':
        booking.status = Booking.STATUS_CANCELLED
        booking.save()
        messages.success(request, 'Reserva cancelada.')
        return redirect('booking_list')
    return render(request, 'bookings/booking_confirm_cancel.html', {'booking': booking})
