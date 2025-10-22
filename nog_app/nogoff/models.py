from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# Create your models here.
class User(models.Model):
    name = models.CharField("Name", max_length=200, null=True)
    last_login = models.DateTimeField("Last Login", auto_now=True)
    is_admin = models.BooleanField("Admin", default=False)
    has_voted = models.BooleanField("Voted", default=False)

    def __str__(self):
        return self.name

    def votes_for_event(self, event):
        """Return all the votes by this user for a given Event"""
        return Vote.objects.filter(user=self, event=event)


class Settings(models.Model):
    votes_per_person = models.IntegerField("Votes per Person")

    def __str__(self):
        return "NogApp Settings"

    def clean(self):
        model = self.__class__
        if model.objects.count() > 0 and self.id != model.objects.get().id:
            raise ValidationError(
                "There can be only one Settings instance"
            )  # Changed message

    def save(self, *args, **kwargs):
        if (
            not self.pk and Settings.objects.exists()
        ):  # Check if any Settings object exists
            raise ValidationError(
                "There can be only one Settings instance"
            )  # Changed message
        return super(Settings, self).save(*args, **kwargs)


class Event(models.Model):
    event_date = models.DateTimeField("Event Date")
    start_time = models.TimeField("Start Time")
    end_time = models.TimeField("End Time")
    name = models.CharField("Event Name", max_length=200)

    def __str__(self):
        return self.name

    @classmethod
    def get_nearest_future_event(cls):
        """
        Returns the nearest Event in the future, or None if no future events exist.
        """
        now = timezone.now()
        return (
            cls.objects.filter(event_date__gte=now)
            .order_by("event_date")
            .first()
        )

    @classmethod
    def get_nearest(cls):
        nearest_event = cls.get_nearest_future_event()
        if nearest_event:
            return nearest_event
        else:
            return None


class Nog(models.Model):
    number = models.IntegerField(default=99)
    creator = models.CharField("Creator", max_length=200)
    description = models.TextField("Description")
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="nogs"
    )

    def __str__(self):
        nog_str = (
            f"Nog {self.number}, Creator {self.creator} - {self.event.name} "
        )
        return nog_str

    def votes_by_user_event(self, user: User, event: Event):
        return Vote.objects.filter(user=user, event=event, nog=self)

    class Meta:
        # Each Nog must have a unique number per NogOff Event
        constraints = [
            models.UniqueConstraint(
                fields=["event", "number"], name="unique_nog_per_event"
            )
        ]


class Vote(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="votes"
    )
    nog = models.ForeignKey(Nog, on_delete=models.CASCADE, related_name="votes")
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="votes"
    )

    def __str__(self):
        return (
            self.user.name
            + " voted for "
            + self.nog.creator
            + "'s nog at "
            + self.event.name
        )
