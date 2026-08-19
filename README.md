# 📅 Gestor de Reservas

Una aplicación web hecha con Django para reservar recursos compartidos —salas de reuniones, pistas deportivas, salas de estudio, lo que se te ocurra— sin que dos personas se queden peleando por la misma franja horaria. Es uno de los proyectos que he desarrollado como práctica del módulo de Django dentro de mi máster de desarrollo full stack, e intento tenerlo con la calidad suficiente como para enseñarlo tranquilamente en mi portfolio.

> **¿Qué resuelve exactamente?** El típico lío de "¿está libre la sala a las 10?" pero automatizado: el sistema comprueba por ti que no haya solapes, te deja programar reservas que se repiten cada día o cada semana, y lleva el registro de quién ha reservado qué.

## 🧭 Índice

- [¿Qué puedes hacer con esta app?](#-qué-puedes-hacer-con-esta-app)
- [Cómo está pensado por dentro](#-cómo-está-pensado-por-dentro)
- [Stack técnico](#-stack-técnico)
- [Ponerlo en marcha en tu máquina](#-ponerlo-en-marcha-en-tu-máquina)
- [Cómo probarlo rápido](#-cómo-probarlo-rápido)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Decisiones de diseño (y sus límites)](#-decisiones-de-diseño-y-sus-límites)
- [Posibles mejoras futuras](#-posibles-mejoras-futuras)

## ✅ ¿Qué puedes hacer con esta app?

- **Registrarte, iniciar sesión y cerrarla**, como en cualquier web normal.
- **Consultar el catálogo de recursos** disponibles (salas, pistas...) sin necesidad de tener cuenta.
- **Ver la ficha de cada recurso**: su horario habitual de disponibilidad y las próximas reservas que ya tiene.
- **Reservar un recurso** indicando fecha y hora de inicio/fin. El sistema **no te deja reservar algo que ya está ocupado** en ese rango.
- **Crear reservas recurrentes**: "cada semana a esta hora" o "todos los días", hasta la fecha que tú marques. Si alguna de esas repeticiones choca con otra reserva ya existente, esa fecha en concreto se salta (y te avisa), pero el resto se reservan igualmente.
- **Consultar "Mis reservas"** y **cancelarlas** cuando ya no las necesites (dejan el hueco libre para otros).
- **Gestionarlo todo desde el panel de administración** de Django (`/admin/`): dar de alta recursos, definir sus horarios de disponibilidad semanal, revisar o anular reservas...

## 🧠 Cómo está pensado por dentro

Todo gira en torno a tres modelos, dentro de la app `bookings`:

```
Resource (recurso)  ---1:N---  Availability (franja horaria semanal)
Resource (recurso)  ---1:N---  Booking (reserva concreta)
```

- **`Resource`**: lo que se puede reservar. Tiene nombre, ubicación, aforo y un flag `is_active` para poder "retirar" un recurso sin borrar su historial.
- **`Availability`**: una franja horaria recurrente semanal ("Sala A, los lunes de 9 a 14h"). Es informativa: se muestra en la ficha del recurso, pero de momento el sistema no impide reservar fuera de esas franjas (más sobre esto en [Decisiones de diseño](#-decisiones-de-diseño-y-sus-límites)).
- **`Booking`**: la reserva en sí. Aquí está la pieza más interesante del proyecto: el método `overlapping_bookings()` calcula si una reserva se solapa con otra ya confirmada del mismo recurso, usando la condición clásica de solapamiento de intervalos (`A < D y C < B`). Esa comprobación se dispara automáticamente al guardar, así que es imposible —desde la propia app— crear dos reservas confirmadas que choquen.

Para las **reservas recurrentes** no hay una "regla mágica" guardada en la base de datos: cuando pides "cada semana hasta el 30 de septiembre", la vista calcula de golpe todas las fechas que corresponden y crea una fila de `Booking` por cada una, todas compartiendo un mismo identificador (`recurrence_group`) para saber que pertenecen al mismo lote. Es una decisión deliberada: es más sencilla de razonar y de depurar que guardar una "regla de repetición" abstracta y recalcularla cada vez.

Todo el código —modelos, vistas, formularios, admin— está comentado en español explicando el porqué de cada decisión, no solo el qué. Si algo no queda claro leyendo los comentarios, ¡es un fallo mío y hay que arreglarlo!

## 🛠️ Stack técnico

| Pieza | Tecnología |
|---|---|
| Backend | Python 3.12 + Django 6.1 |
| Base de datos | SQLite (perfecta para desarrollo/demo; en producción se recomienda PostgreSQL) |
| Frontend | Plantillas de Django + Bootstrap 5 (vía CDN, sin build de JS) |
| Autenticación | El sistema de auth propio de Django (`django.contrib.auth`) |

No hay JavaScript "propio" más allá de lo que trae Bootstrap: los formularios de fecha/hora usan el selector nativo del navegador (`<input type="datetime-local">`), así que funciona sin frameworks de frontend.

## 🚀 Ponerlo en marcha en tu máquina

Necesitas Python 3.12 (o similar) instalado. Los pasos:

```bash
# 1. Clona el repo y entra en la carpeta
git clone https://github.com/PabloRod137/django-gestor-reservas.git
cd django-gestor-reservas

# 2. Crea y activa un entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 3. Instala las dependencias
pip install -r requirements.txt

# 4. Crea la base de datos (aplica las migraciones)
python manage.py migrate

# 5. Crea un usuario administrador para poder entrar al panel /admin/
python manage.py createsuperuser

# 6. Arranca el servidor de desarrollo
python manage.py runserver
```

Y ya puedes abrir **http://127.0.0.1:8000/** en el navegador.

> 💡 Al ser un proyecto de práctica, la base de datos se crea vacía. Entra en `/admin/` con el superusuario que has creado y da de alta algún recurso (por ejemplo, "Sala de reuniones A") para poder probar el flujo de reservas de principio a fin.

## 🔍 Cómo probarlo rápido

1. Crea un recurso desde `/admin/` (o desde el propio admin te deja añadir también sus franjas de disponibilidad, como líneas dentro de la misma pantalla).
2. Regístrate como usuario normal desde `/registro/`.
3. Ve al recurso que has creado y pulsa "Reservar este recurso".
4. Prueba a crear dos reservas que se solapen: la segunda debería rechazarse con un mensaje claro.
5. Prueba una reserva "Semanal" indicando una fecha de "repetir hasta": deberías ver aparecer varias reservas de golpe en "Mis reservas".

## 📁 Estructura del proyecto

```
config/               # configuración del proyecto Django (settings, urls raíz)
bookings/              # la app: modelos, vistas, formularios, admin, urls
    models.py           # Resource, Availability, Booking (y la lógica de solapamiento)
    views.py             # listados, ficha de recurso, crear/cancelar reserva
    forms.py              # formularios de registro y de reserva
    admin.py               # configuración del panel de administración
templates/             # plantillas HTML (base.html + una por cada vista)
static/                # CSS propio
```

## 🎯 Decisiones de diseño (y sus límites)

Para que quede claro qué es "a propósito" y qué es simplemente alcance no cubierto:

- **La disponibilidad semanal (`Availability`) es informativa, no restrictiva.** Se puede reservar un recurso fuera de su horario habitual mostrado en la ficha. Añadir esa validación sería relativamente sencillo (comprobar en `Booking.clean()` que el rango pedido cae dentro de alguna `Availability` del recurso, y de paso comprobar el día de la semana), pero he preferido dejarlo fuera para no complicar el alcance del ejercicio.
- **Las reservas no se borran al cancelarlas**, solo cambian de estado a "cancelada". Así se conserva el histórico y, al mismo tiempo, ese hueco vuelve a quedar libre automáticamente (la comprobación de solapamiento solo mira reservas confirmadas).
- **Las fechas se guardan siempre en UTC internamente** (`USE_TZ=True`, estándar recomendado por Django) y se convierten a hora de Madrid (`Europe/Madrid`) solo al mostrarlas. Si alguna vez ves código que formatea una fecha "a mano" con `strftime` en vez de con `timezone.localtime()` o el filtro `|date` de las plantillas, sospecha: es la forma más habitual de que una app Django "se coma" una hora sin darte cuenta con el cambio de horario de verano.

## 🔮 Posibles mejoras futuras

- Restringir las reservas para que caigan dentro de las franjas de `Availability`.
- Notificaciones por email al crear/cancelar una reserva (la infraestructura de correo ya está configurada con el backend de consola, listo para cambiar a SMTP real).
- Exportar las reservas propias a CSV/JSON.
- Un calendario visual (tipo FullCalendar) en vez de listados en tabla.
