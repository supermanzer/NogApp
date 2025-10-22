from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render

from .models import Event, Nog, Settings, Vote


# Create your views here.
def index(request) -> HttpResponse:
    template = "nogoff/index.html"
    next_nogoff = Event.get_nearest()
    context = {"title": "NogApp Home", "next_nogoff": next_nogoff}
    return render(request, template, context=context)


def about(request: HttpRequest) -> HttpResponse:
    template = "nogoff/about.html"
    context = {"title": "About NogApp"}
    return render(request, template, context=context)


def detail(request: HttpRequest, nog_id: int) -> HttpResponse:
    template = "nogoff/detail.html"
    model = Event.objects.get(pk=nog_id)
    context = {"title": "Detail", "nogoff": model, "nogs": model.nogs.all()}
    return render(request, template, context=context)


def event(request: HttpRequest, nog_id: int) -> HttpResponse:
    template = "nogoff/event.html"
    nog_off = Event.objects.get(pk=nog_id)
    user = getattr(request, "device_user", None)

    current_votes = user.votes_for_event(nog_off)
    print(f"CURRENT VOTES: {current_votes}")

    nogs = nog_off.nogs.all()
    settings = Settings.objects.first()

    context = {
        "title": nog_off.name,
        "nogoff": nog_off,
        "nogs": nogs,
        "n_votes": settings.votes_per_person,
        "user": user,
        "current_votes": current_votes,
    }

    return render(request, template, context=context)


def vote(request: HttpRequest, nog_id: int) -> HttpResponse:
    if request.method == "POST":
        user = getattr(request, "device_user", None)
        nogoff = Event.objects.get(pk=nog_id)
        data = dict(request.POST)
        _ = data.pop("csrfmiddlewaretoken")
        print(f"GOT DATA: {data} for {user}")
        for id in data.keys():
            nog = Nog.objects.get(pk=int(id))
            votes = int(data[id][0])
            print(f"\nGOT VOTES: {votes}\n")
            for i in range(votes):
                Vote(user=user, nog=nog, event=nogoff).save()
                print(f"User {user} voted for Nog {nog}")
        user.has_voted = True
        user.save()
        return HttpResponse("<h1>Hi</h1>")
    else:
        return HttpResponseForbidden(content="GET method not permitted")


def reset_votes(request: HttpRequest, nog_id: int) -> HttpResponse:
    if request.method == "POST":
        pass
    else:
        return HttpResponseForbidden(content="GET method not permitted")
