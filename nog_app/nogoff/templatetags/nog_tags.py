from django import template

register = template.Library()


@register.simple_tag
def get_votes_by_user_event(nog, user, event):
    """
    Returns the number of votes for a nog by a user in an event
    Usage: {% get_votes_by_user_event nog user nogoff as vote_count %}
    """
    votes = nog.votes_by_user_event(user=user, event=event)
    return votes.count() if votes else 0
