from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import EspacioEducativo


@login_required
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