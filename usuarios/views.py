from django.shortcuts import render


def home(request):
    """
    Vista principal de la aplicación.
    """
    return render(request, 'usuarios/home.html')
