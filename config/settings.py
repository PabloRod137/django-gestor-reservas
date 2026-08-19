"""
Configuración general del proyecto Django "Gestor de Reservas".

Este archivo lo genera automáticamente 'django-admin startproject' y luego
se va ajustando a mano. Aquí solo se tocan los valores que el proyecto
necesita de verdad; el resto se deja tal cual lo trae Django por defecto.

Documentación oficial de settings:
https://docs.djangoproject.com/en/6.1/ref/settings/
"""

import os
from pathlib import Path

# BASE_DIR es la carpeta raíz del proyecto (donde está manage.py). A partir
# de aquí se construyen el resto de rutas (plantillas, estáticos, la base
# de datos SQLite...) para que funcionen sin importar desde qué carpeta se
# lance el servidor.
BASE_DIR = Path(__file__).resolve().parent.parent


# --- Seguridad básica ---
#
# SECRET_KEY se usa internamente para firmar cookies de sesión, tokens CSRF,
# etc. En un proyecto real NUNCA debería estar escrita a fuego en el código
# ni subida a un repositorio público. Aquí leemos primero la variable de
# entorno DJANGO_SECRET_KEY y, si no existe (por ejemplo, al clonar este
# repo y arrancarlo en local para probarlo), usamos una clave de repuesto.
# Esa clave de repuesto lleva el prefijo 'django-insecure-' a propósito:
# es la misma convención que usa Django para recordarte que NO es apta
# para producción.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure--zmo0yi*9)2@u^oo+c090iykf@xhov+)#7$f#&t%b@)u6p8$i(',
)

# DEBUG=True hace que Django muestre páginas de error muy detalladas y sirva
# los archivos estáticos sin necesidad de configuración extra: perfecto para
# desarrollar y para que un profesor/evaluador pueda levantar el proyecto
# sin complicaciones. En un despliegue real esto debe ser False.
DEBUG = True

# Con DEBUG=True, Django permite automáticamente peticiones a localhost/
# 127.0.0.1 aunque ALLOWED_HOSTS esté vacío, así que no hace falta tocar
# esto para desarrollo local.
ALLOWED_HOSTS = []


# --- Aplicaciones instaladas ---
# Las seis primeras son las apps que trae Django "de fábrica" (admin, login,
# tipos de contenido, sesiones, mensajes flash y archivos estáticos).
# 'bookings' es nuestra app, la que contiene toda la lógica del negocio.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bookings',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Además de las plantillas propias de cada app (templates/bookings/...,
        # que Django encuentra solo gracias a APP_DIRS=True), aquí le decimos
        # dónde están las plantillas "compartidas" del proyecto, como
        # base.html o las de registro/login.
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# --- Internacionalización ---
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'es-es'  # textos del admin, mensajes de validación, etc. en español

# Zona horaria "de referencia" del proyecto. Con USE_TZ=True (recomendado),
# Django guarda TODAS las fechas en la base de datos en UTC, y usa esta
# zona horaria solo para convertir de/hacia UTC cuando el usuario introduce
# o visualiza una fecha (por ejemplo, en las plantillas con el filtro
# |date, o con timezone.localtime() en el código Python). Ver los
# comentarios en bookings/forms.py y bookings/models.py para más detalle
# sobre por qué esto importa.
TIME_ZONE = 'Europe/Madrid'

USE_I18N = True
USE_TZ = True


# --- Archivos estáticos (CSS, JS, imágenes) ---
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'
# Carpeta donde Django busca los estáticos "propios del proyecto" (además
# de los de cada app, en bookings/static/, que aquí no usamos).
STATICFILES_DIRS = [BASE_DIR / 'static']

# --- Autenticación ---
# A dónde redirigir en cada caso. LOGIN_URL es la página a la que Django
# manda automáticamente a un usuario anónimo cuando intenta entrar en una
# vista protegida con @login_required.
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'booking_list'
LOGOUT_REDIRECT_URL = 'login'


# --- Correo ---
# https://docs.djangoproject.com/en/6.1/topics/email/
#
# En este proyecto no se envían emails de verdad, pero se deja la
# configuración lista con el backend de "consola": en vez de enviar el
# correo por SMTP, Django lo imprime en la terminal donde corre
# `runserver`. Es la forma estándar de probar envíos de email en
# desarrollo sin necesidad de un servidor de correo real.
MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
