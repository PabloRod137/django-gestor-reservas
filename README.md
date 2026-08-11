# Gestor de Reservas

Aplicación Django para reservar recursos compartidos (salas, pistas deportivas, equipamiento) evitando solapamientos y permitiendo reservas recurrentes.

Proyecto desarrollado como práctica del módulo de Django del máster de desarrollo full stack.

## Funcionalidades

- Registro, login y logout de usuarios
- Alta de recursos reservables con su disponibilidad semanal
- Calendario de disponibilidad por recurso
- Creación de reservas con validación de solapamiento (no se puede reservar un recurso ya ocupado en ese horario)
- Reservas recurrentes (diarias o semanales) con generación automática de las instancias
- Cancelación de reservas propias
- Panel de administración para gestionar recursos y reservas (Django admin)

## Modelos

- `Resource`: recurso reservable (sala, pista, equipo...)
- `Availability`: franjas horarias en las que un recurso está disponible, por día de la semana
- `Booking`: reserva concreta de un recurso por un usuario, con control de solapamiento y recurrencia

## Stack

- Python 3.12 + Django 6.1
- SQLite (desarrollo)
- Django templates + Bootstrap 5

## Puesta en marcha

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visita `http://127.0.0.1:8000/`.

## Estructura

```
config/       # configuración del proyecto Django
bookings/     # app principal: modelos, vistas, formularios, urls
templates/    # plantillas HTML
static/       # CSS/JS propios
```
