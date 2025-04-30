from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

def login_view(request):
    template = loader.get_template('login_page.html')
    return HttpResponse(template.render())

def register_view(request):
    template = loader.get_template('register_page.html')
    return HttpResponse(template.render())