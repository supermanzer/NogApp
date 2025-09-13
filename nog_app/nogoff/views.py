from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import render
from .models import Event


# Create your views here.
def index(request):
    template = "nogoff/index.html"
    next_nogoff = Event.get_nearest()
    context = {"title": "NogApp Home", "next_nogoff": next_nogoff}
    return render(request, template, context=context)


def about(request):
    template = "nogoff/about.html"
    context = {"title": "About NogApp"}
    return render(request, template, context=context)


def detail(request, nog_id):
    template = "nogoff/detail.html"
    model = Event.objects.get(pk=nog_id)
    context = {"title": "Detail", "nogoff": model, "nogs": model.nogs.all()}
    return render(request, template, context=context)


def event(request, nog_id):
    template = "nogoff/event.html"
    model = Event.objects.get(pk=nog_id)
    nogs = model.nogs.all()
    context = {"title": "Event", "nogoff": model, "nogs": nogs}
    print(context)
    return render(request, template, context=context)
