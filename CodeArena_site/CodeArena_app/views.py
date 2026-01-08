from django.shortcuts import render
from .models import Profile

def profile_view(request):
    # Get the profile for the logged-in user
    user_profile = Profile.objects.get(user=request.user)
    return render(request, 'profile.html', {'profile': user_profile})