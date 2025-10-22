from django.contrib import admin

from .models import Event, Nog, Settings, User, Vote


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fields = ["name", "is_admin", "has_voted"]
    readonly_fields = ["last_login"]


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    pass


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    pass


@admin.register(Nog)
class NogAdmin(admin.ModelAdmin):
    pass


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    pass
