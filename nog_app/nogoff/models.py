from django.db import models


# Create your models here.
class User(models.Model):
    name = models.CharField("Name", max_length=200, null=True)
    last_login = models.DateTimeField("Last Login", auto_now=True)
    is_admin = models.BooleanField("Admin", default=False)
    has_voted = models.BooleanField("Voted", default=False)

    def __str__(self):
        return self.name


class Settings(models.Model):
    votes_per_person = models.IntegerField("Votes per Person")

    def __str__(self):
        return "NogApp Settings"


class Event(models.Model):
    event_date = models.DateTimeField("Event Date")
    start_time = models.TimeField("Start Time")
    end_time = models.TimeField("End Time")
    name = models.CharField("Event Name", max_length=200)

    def __str__(self):
        return self.name


class Nog(models.Model):
    creator = models.CharField("Name", max_length=200)
    description = models.TextField("Description")
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return self.creator + " - Nog for " + self.event.name


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    nog = models.ForeignKey(Nog, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return (
            self.user.name
            + " voted for "
            + self.nog.creator
            + "'s nog at "
            + self.event.name
        )
