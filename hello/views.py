from django.shortcuts import render

# Create your views here.

#Request handler, aciones.

from django.http import HttpResponse


def index(request):
    #Vamos a renderizar el html creado en /templates
    return render(request, "hello.html", { "name": "Juan"})

def pruebas(request):
    #Podriamos coger datos de ls DB, transformar datos, cualquier cosa.
    return HttpResponse("Comprendiendo como funciona Django.")