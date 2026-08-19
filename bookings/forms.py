"""
Formularios de la app "bookings".

Aquí hay dos formularios:
  - SignUpForm: registro de usuarios nuevos (reutiliza el UserCreationForm
    que trae Django de serie, solo le añadimos el campo email).
  - BookingForm: formulario para crear una reserva, incluida la parte de
    "reservas recurrentes" (que en realidad no es un campo del modelo,
    sino dos campos extra que la vista usa para generar varias reservas).
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Booking


class SignUpForm(UserCreationForm):
    """
    Formulario de registro. UserCreationForm ya trae usuario + las dos
    contraseñas (con su validación de "¿coinciden?"), así que solo
    añadimos el email y lo marcamos como obligatorio.
    """

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Django no añade clases CSS a los campos por defecto; se las ponemos
        # aquí a mano para que encajen con el estilo de Bootstrap del resto
        # de la web (en vez de tener que repetirlo en cada plantilla).
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class BookingForm(forms.ModelForm):
    """
    Formulario para crear una reserva.

    Los campos 'start_datetime'/'end_datetime' sí son del modelo Booking,
    pero 'recurrence_end' NO lo es: es un campo "virtual" que solo existe
    en el formulario, para que el usuario pueda decir "repite esta reserva
    hasta el día X". La vista (booking_create) es quien usa ese dato para
    generar varias reservas (una por día/semana) en lugar de guardarlo
    directamente en el modelo.
    """

    class Meta:
        model = Booking
        fields = ['resource', 'start_datetime', 'end_datetime', 'notes', 'recurrence']
        widgets = {
            # type="datetime-local" hace que el navegador muestre su propio
            # selector de fecha y hora, sin tener que programar nada en JS.
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    # Campo extra, no ligado al modelo (por eso no está en Meta.fields).
    recurrence_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Repetir hasta',
        help_text='Solo aplica si eliges una recurrencia diaria o semanal.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # input_formats le dice al formulario cómo interpretar el texto que
        # manda el <input type="datetime-local">. Si no se especifica, Django
        # usa los formatos por defecto de settings (pensados para inputs de
        # texto normales) y puede fallar al parsear el formato ISO que
        # generan estos inputs del navegador.
        self.fields['start_datetime'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_datetime'].input_formats = ['%Y-%m-%dT%H:%M']

        # Igual que en SignUpForm: añadimos las clases de Bootstrap a mano.
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs['class'] = css_class

    def clean(self):
        cleaned_data = super().clean()
        recurrence = cleaned_data.get('recurrence')
        recurrence_end = cleaned_data.get('recurrence_end')
        start_datetime = cleaned_data.get('start_datetime')

        # --- Fix de zona horaria ---
        # El <input type="datetime-local"> no manda información de zona
        # horaria (solo "2026-08-20T18:00"), así que Django lo interpreta
        # como un datetime "naive" (sin zona horaria). Como en settings.py
        # tenemos USE_TZ=True, si guardásemos ese valor tal cual, Django
        # lanzaría un aviso y asumiría UTC por defecto en algunos casos,
        # lo que podía desplazar la hora mostrada más tarde (por ejemplo,
        # ver 16:00 en vez de las 18:00 que el usuario escribió, por el
        # cambio de horario de verano). Para evitarlo, en cuanto tenemos el
        # valor "naive" lo convertimos aquí mismo a "aware" usando la zona
        # horaria del proyecto (Europe/Madrid, definida en settings.TIME_ZONE).
        for field_name in ('start_datetime', 'end_datetime'):
            value = cleaned_data.get(field_name)
            if value and timezone.is_naive(value):
                cleaned_data[field_name] = timezone.make_aware(value)
        start_datetime = cleaned_data.get('start_datetime')

        # Si el usuario elige una recurrencia (diaria/semanal), es obligatorio
        # indicar hasta cuándo se repite, y esa fecha no puede ser anterior
        # al propio inicio de la reserva (no tendría sentido).
        if recurrence and recurrence != Booking.RECURRENCE_NONE:
            if not recurrence_end:
                self.add_error('recurrence_end', 'Indica hasta qué fecha se repite la reserva.')
            elif start_datetime and recurrence_end < start_datetime.date():
                self.add_error('recurrence_end', 'La fecha de fin de la recurrencia no puede ser anterior al inicio.')
        return cleaned_data
