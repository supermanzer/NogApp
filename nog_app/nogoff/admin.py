from django.contrib import admin
from django.db.models import Count

from .models import Event, Nog, Settings, User, Vote

# ================= INLINES ========================


class NogInline(admin.TabularInline):
    model = Nog
    readonly_fields = ("vote_count",)
    fields = ("number", "creator", "description", "vote_count")
    extra = 0

    def vote_count(self, obj):
        return obj.votes.count()

    vote_count.short_description = "Total Votes"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(vote_count=Count("votes"))


# ================= MODEL ADMINS ===================
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
    inlines = [NogInline]


@admin.register(Nog)
class NogAdmin(admin.ModelAdmin):
    list_display = ("number", "creator", "event", "vote_count")
    list_filter = ("event",)
    search_fields = ("creator", "description")

    def vote_count(self, obj):
        return obj.votes.count()

    vote_count.short_description = "Total Votes"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(vote_count=Count("votes"))


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    pass
