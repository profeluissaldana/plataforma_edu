from django.shortcuts import render

from .models import EspacioEducativo


def inicio(request):

    espacios = EspacioEducativo.objects.filter(
        activo=True
    )

    return render(
        request,
        'educacion/inicio.html',
        {
            'espacios': espacios
        }
    )