from django.http import HttpResponse
from django.shortcuts import render


# Create your views here.
def index(request):
    template = "nogoff/base.html"
    context = {"title": "NogApp Home"}
    return render(request, template, context=context)
