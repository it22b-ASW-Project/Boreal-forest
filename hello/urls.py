from django.contrib import admin
from django.urls import path

from . import views #IMPORTANTE. Para referenciar nuestras funciones de views.py

#Aqui mapearemos todas las URL que necesitemos para nuestra aplicación

#Configuración de las URLs
urlpatterns = [
    #path("rutaEnLaURL",views.FUNCTION, name="")
    path("",views.index, name="index"),
    path("pruebas/", views.pruebas)

]
