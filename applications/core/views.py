from django.shortcuts import render

def home(request):
    return render(request, 'core/home.html')

def contacto(request):
    return render(request, 'core/contacto.html')