from django.shortcuts import render, redirect
from .models import UserProfile

from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
User = get_user_model()

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

# ---------------- HOME ----------------

def home_view(request):
    return render(request, "home.html")


# ---------------- LOGIN ----------------

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

User = get_user_model()

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # 🔍 Check if user exists
        if not User.objects.filter(username=username).exists():
            return render(request, "login.html", {
                "error": "No user found"
            })

        # 🔐 Verify encrypted password
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "login.html", {
                "error": "Wrong password"
            })

    return render(request, "login.html")

# ---------------- SIGNUP ----------------

def signup_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]

        # 1️⃣ Create User (password encrypted automatically)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # 2️⃣ Profile created via signal (below)

        # 3️⃣ Log user in
        login(request, user)

        return redirect("dashboard")

    return render(request, "signup.html")

# ---------------- DASHBOARD ----------------

@login_required
def dashboard_view(request):
    return render(request, "dashboard.html")

# ---------------- PROFILE ----------------

@login_required
def profile_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    return render(request, 'profile.html', {'profile': user_profile})

# ---------------- QUIZ ----------------

def quiz_view(request):
    return render(request, "quiz.html")

def insideQuiz_view(request):
    return render(request, "insideQuiz.html")

def DebuggingQuiz_view(request):
    return render(request, "DebuggingQuiz.html")

def leaderboard_view(request):
    return render(request, "leaderboard.html")

# ---------------- EDIT PROFILE ----------------

@login_required
def edit_profile_view(request):
    profile = UserProfile.objects.get(user=request.user)

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name")
        profile.dob = request.POST.get("dob")
        profile.skills = request.POST.get("skills")
        profile.save()

        return redirect("profile")

    return render(request, "edit_profile.html", {"profile": profile})

# ---------------- SIGNAL ----------------

# This guarantees profile creation even if admin creates user
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
