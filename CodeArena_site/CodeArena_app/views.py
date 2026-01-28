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

from django.utils.timezone import localtime
from datetime import date

from .models import DailySubmission

@login_required
def profile_view(request):
    user = request.user
    profile = user.profile

    total_solved = (
        profile.easy_solved +
        profile.medium_solved +
        profile.hard_solved
    )

    submissions = DailySubmission.objects.filter(user=user)

    activity = {
        s.date.strftime("%Y-%m-%d"): min(s.count, 4)
        for s in submissions
    }

    context = {
        "user": user,
        "profile": profile,
        "total_solved": total_solved,
        "member_since": user.date_joined,
        "activity": activity,
    }

    return render(request, "profile.html", context)



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

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

# ------------------- Update skill in database -----------------------
@login_required
def update_skills(request):
    if request.method == "POST":
        skill = request.POST.get("skill", "")
        action = request.POST.get("action")

        profile = request.user.profile

        # 🔥 NORMALIZE DATA (FIXES DELETE ISSUE)
        skill = skill.strip().lower()
        skills = [s.strip().lower() for s in profile.get_skills_list()]

        if action == "add" and skill and skill not in skills:
            skills.append(skill)

        if action == "remove" and skill in skills:
            skills.remove(skill)

        # Save back as comma-separated string
        profile.skills = ",".join(skills)
        profile.save()

        return JsonResponse({"status": "ok"})

# --------------------- For total and daily submissions of user -------------------------
from django.utils.timezone import now
from .models import DailySubmission

@login_required
def submit_solution(request, problem_id):
    profile = request.user.profile

    # 1️⃣ total submissions
    profile.total_submissions += 1
    profile.save()

    # 2️⃣ daily submission
    today = now().date()
    daily, created = DailySubmission.objects.get_or_create(
        user=request.user,
        date=today
    )
    daily.count += 1
    daily.save()

# ------------------- Dashboard : to load problems from database  -----------------------

from .models import Problem

@login_required
def dashboard_view(request):
    problems = Problem.objects.all()

    return render(request, "dashboard.html", {
        "problems": problems
    })

# ------------------- PROBLEM PAGE (LOAD DATA DYNAMICALLY) -----------------------
from .models import Problem

@login_required
def problem_detail_view(request, problem_id):
    problem = Problem.objects.get(id=problem_id)

    return render(request, "problemPage.html", {
        "problem": problem
    })

# ------------------- SUBMISSION LOGIC (THIS IS THE HEART ❤️) -----------------------

from django.utils.timezone import now
from .models import DailySubmission

@login_required
def submit_solution(request, problem_id):
    if request.method == "POST":
        profile = request.user.profile

        # 1️⃣ Total submissions
        profile.total_submissions += 1
        profile.save()

        # 2️⃣ Daily submissions
        today = now().date()
        daily, created = DailySubmission.objects.get_or_create(
            user=request.user,
            date=today
        )
        daily.count += 1
        daily.save()

        return JsonResponse({"status": "accepted"})