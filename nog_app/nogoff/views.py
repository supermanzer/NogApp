from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import render
from .models import Event


# Create your views here.
def index(request):
    template = "nogoff/index.html"
    context = {"title": "NogApp Home"}
    return render(request, template, context=context)


def about(request):
    template = "nogoff/about.html"
    context = {"title": "About NogApp"}
    return render(request, template, context=context)


def event(request, start_date):
    template = "nogoff/event.html"
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    model = Event.objects.get(
        event_date__year=start_date.year,
        event_date__month=start_date.month,
        event_date__day=start_date.day,
    )
    nogs = model.nogs.all()
    context = {"title": "Event", "nogoff": model, "nogs": nogs}
    print(context)
    return render(request, template, context=context)
