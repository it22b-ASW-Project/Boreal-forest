"""
URL configuration for boreal_forest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include,path
from . import views

#URLConf de nuestra web
urlpatterns = [
    path("", views.homepage),

    #cada vez que creemos una nueva app, hay que añadir un path como el siguiente:
    path("hello/",include("hello.urls")),
    #esto permite que desde aquí podamos definir las rutas a todas las aplicaciónes que creemos.
    #individualmente, cada app tendrá sus rutas. Ejemplo: definimos /hello/ aqui como aplicación
    #posteriormente, en la carpeta de la aplicación en cuestión tendremos otro archivo urls.py donde
    #definir todas las extensiones de esta URL como /hello/pruebas.

    path('admin/', admin.site.urls),
]
