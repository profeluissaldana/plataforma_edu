from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render



def login_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        usuario = authenticate(
            request,
            username=username,
            password=password
        )

        if usuario is not None:

            login(
                request,
                usuario
            )

            return redirect(settings.LOGIN_REDIRECT_URL)

        error = 'Usuario o contraseña incorrectos.'

        return render(
            request,
            'usuarios/login.html',
            {
                'error': error
            }
        )

    return render(
        request,
        'usuarios/login.html'
    )


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('inicio')