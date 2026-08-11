from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Booking


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['resource', 'start_datetime', 'end_datetime', 'notes', 'recurrence']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    recurrence_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Repetir hasta',
        help_text='Solo aplica si eliges una recurrencia diaria o semanal.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_datetime'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_datetime'].input_formats = ['%Y-%m-%dT%H:%M']
        for name, field in self.fields.items():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs['class'] = css_class

    def clean(self):
        cleaned_data = super().clean()
        recurrence = cleaned_data.get('recurrence')
        recurrence_end = cleaned_data.get('recurrence_end')
        start_datetime = cleaned_data.get('start_datetime')
        if recurrence and recurrence != Booking.RECURRENCE_NONE:
            if not recurrence_end:
                self.add_error('recurrence_end', 'Indica hasta qué fecha se repite la reserva.')
            elif start_datetime and recurrence_end < start_datetime.date():
                self.add_error('recurrence_end', 'La fecha de fin de la recurrencia no puede ser anterior al inicio.')
        return cleaned_data
