import logging

from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import render

from .models import Event, Nog, Settings, Vote

# Get loggers
logger = logging.getLogger("nogoff")
user_logger = logging.getLogger("nogoff.user_actions")


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


def event(request: HttpRequest, nog_id: int) -> HttpResponse:
    template = "nogoff/event.html"
    try:
        nog_off = Event.objects.get(pk=nog_id)
        user = getattr(request, "device_user", None)

        current_votes = user.votes_for_event(nog_off)
        logger.info(f"Retrieved votes for user {user} in event {nog_off}")

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
    except Event.DoesNotExist:
        logger.error(f"Event with id {nog_id} not found")
        raise Http404("Event not found")
    except Exception:
        logger.exception("Unexpected error in event view")
        raise


def vote(request: HttpRequest, nog_id: int) -> HttpResponse:
    if request.method == "POST":
        try:
            user = getattr(request, "device_user", None)
            nogoff = Event.objects.get(pk=nog_id)
            data = dict(request.POST)
            _ = data.pop("csrfmiddlewaretoken")

            logger.info(f"Processing votes for event {nogoff}")
            user_logger.info(f"User {user} voting in event {nogoff}")

            for id in data.keys():
                nog = Nog.objects.get(pk=int(id))
                votes = int(data[id][0])
                logger.debug(f"Processing {votes} votes for nog {nog}")
                # Your vote processing logic here
                for i in range(votes):
                    Vote(user=user, nog=nog, event=nogoff).save()
                    logger.debug(f"User {user} voted for Nog {nog}")

            user.has_voted = True
            user.save()
            user_logger.info(f"User {user} completed voting in event {nogoff}")

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Your votes have been recorded successfully!",
                }
            )
        except Event.DoesNotExist:
            logger.error(f"Event {nog_id} not found during voting")
            return JsonResponse(
                {"status": "error", "message": "Event not found"}, status=404
            )
        except Exception as e:
            logger.exception("Error processing votes")
            return JsonResponse(
                {"status": "error", "message": str(e)}, status=500
            )
    else:
        logger.warning(f"Invalid method {request.method} for voting")
        return HttpResponseForbidden(content="GET method not permitted")


def reset_votes(request: HttpRequest, nog_id: int) -> HttpResponse:
    if request.method == "POST":
        try:
            user = getattr(request, "device_user", None)
            nogoff = Event.objects.get(pk=nog_id)
            user_logger.info(f"User {user} resetting votes for event {nogoff}")
            # Clearing votes
            Vote.objects.filter(user=user, event=nogoff).delete()

            # resetting user voted.
            user.has_voted = False
            user.save()
            user_logger.info(
                f"User {user} successfully reset votes for event {nogoff}"
            )

            return HttpResponse("Votes reset successfully")
        except Exception as e:
            logger.exception("Error resetting votes")
            return JsonResponse({"message": str(e)}, status=500)
    else:
        logger.warning(f"Invalid method {request.method} for reset_votes")
        return HttpResponseForbidden(content="GET method not permitted")
