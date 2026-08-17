"""Session and profile helpers."""

from django.contrib import messages
from django.shortcuts import redirect

from .models import UserProfile


def get_session_profile(request):
    """Return the UserProfile stored in the session, or None."""
    profile_id = request.session.get('profile_id')
    if not profile_id:
        return None
    return UserProfile.objects.filter(pk=profile_id).first()


def require_session_profile(request):
    """
    Return the session profile or redirect to planner with a message.
    """
    profile = get_session_profile(request)
    if profile is None:
        messages.warning(
            request,
            'Please complete the Diet Planner first to start tracking food.',
        )
        return None
    return profile


def profile_owns_resource(request, profile):
    """Check that the resource belongs to the current session profile."""
    return request.session.get('profile_id') == profile.pk
