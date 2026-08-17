from .models import UserProfile


def session_profile(request):
    """Expose the current session profile to all templates (for navigation)."""
    profile_id = request.session.get('profile_id')
    profile = None
    if profile_id:
        profile = UserProfile.objects.filter(pk=profile_id).first()
    return {'current_profile': profile}
