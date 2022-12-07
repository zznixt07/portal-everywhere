from django.shortcuts import render

def home(request):
    return render(request, 'home/home.html')

def docs(request):
    return render(request, 'home/docs.html')