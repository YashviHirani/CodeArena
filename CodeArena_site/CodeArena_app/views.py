from django.shortcuts import render, redirect
from .models import UserProfile

from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
User = get_user_model()

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

from CodeArena_app.models import Language, Quiz, UserMCQAttempt, MCQ


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
    
# ----------------------- QUIZ ------------------------
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
import json
from CodeArena_app.models import Language, Quiz, UserMCQAttempt, MCQ
from django.views.decorators.csrf import csrf_exempt

def quiz_home(request):
    languages = Language.objects.all()
    return render(request, 'quiz.html', {'languages': languages})


# @login_required
def inside_quiz(request):
    language_id = request.GET.get('lang')
    if not language_id:
        return HttpResponse("Language not provided", status=400)

    language = get_object_or_404(Language, id=language_id)

    # ✅ quizzes already solved correctly by the user
    solved_quiz_ids = UserMCQAttempt.objects.filter(
        user_id=request.user.id,
        is_correct=True
    ).values_list('quiz_id', flat=True)

    # ✅ fetch quizzes for this language, excluding solved ones
    quizzes = (
        Quiz.objects
        .select_related('question')
        .filter(language=language)
        .exclude(id__in=solved_quiz_ids)
        .order_by('?')[:10]
    )

    if not quizzes.exists():
        return HttpResponse("You have completed all questions 🎉")

    quiz_data = [
        {
            "quiz_id": quiz.id,
            "question": quiz.question.question_text,
            "options": [
                quiz.question.option_a,
                quiz.question.option_b,
                quiz.question.option_c,
                quiz.question.option_d,
            ]
        }
        for quiz in quizzes
    ]

    return render(request, 'insideQuiz.html', {
        "language": language,
        "quiz_data": json.dumps(quiz_data)
    })

    return render(request, 'inside_quiz.html', context)
def start_quiz(request):
    if request.method == "POST":
        lang_id = request.POST.get('language')
        return redirect(f'/insideQuiz?lang={lang_id}')


# @login_required
@csrf_exempt
def save_mcq_answer(request):
    if request.method == "POST":
        data = json.loads(request.body)

        quiz_id = data.get("quiz_id")
        selected_option = data.get("selected_option")

        quiz = get_object_or_404(Quiz, id=quiz_id)
        is_correct = selected_option == quiz.question.correct_option

        UserMCQAttempt.objects.update_or_create(
            user=request.user,
            quiz=quiz,
            defaults={
                "selected_option": selected_option,
                "is_correct": is_correct,
                "completed": is_correct
            }
        )

        return JsonResponse({"correct": is_correct})


def leaderboard(request):
    return render(request, "leaderboard.html")


def get_quiz_questions(user, language, limit=10):
    attempted_wrong = UserMCQAttempt.objects.filter(
        user=user,
        is_correct=False
    ).values_list('quiz_id', flat=True)

    quizzes = Quiz.objects.filter(
        Q(id__in=attempted_wrong) |
        Q(language=language)
    ).distinct().order_by('?')[:limit]

    return quizzes


# Quiz Methods 01.1

def quiz(request):
    return render(request, "quiz.html")


def quiz_home(request):
    languages = Language.objects.all()
    return render(request, 'quiz.html', {
        'languages': languages
    })


def inside_quiz(request):
    language_id = request.GET.get("lang")
    if not language_id:
        return HttpResponse("Language not provided", status=400)

    language = get_object_or_404(Language, id=language_id)

    # ===============================
    # ✅ CASE 1: USER IS LOGGED IN
    # ===============================
    if request.user.is_authenticated:
        solved_correct = UserMCQAttempt.objects.filter(
            user=request.user,
            is_correct=True
        ).values_list("quiz_id", flat=True)

        solved_wrong = UserMCQAttempt.objects.filter(
            user=request.user,
            is_correct=False
        ).values_list("quiz_id", flat=True)

        wrong_quizzes = Quiz.objects.filter(
            id__in=solved_wrong,
            language=language,
            quiz_type="MCQ"
        )

        new_quizzes = Quiz.objects.filter(
            language=language,
            quiz_type="MCQ"
        ).exclude(
            id__in=solved_correct
        ).exclude(
            id__in=solved_wrong
        )

        quizzes = list(wrong_quizzes) + list(new_quizzes)
        quizzes = quizzes[:10]

    # ===============================
    # ❌ CASE 2: ANONYMOUS USER
    # ===============================
    else:
        quizzes = Quiz.objects.filter(
            language=language,
            quiz_type="MCQ"
        ).order_by("?")[:10]

    if not quizzes:
        return HttpResponse("No questions available")

    quiz_data = [
        {
            "quiz_id": quiz.id,
            "question": quiz.question.question_text,
            "options": [
                quiz.question.option_a,
                quiz.question.option_b,
                quiz.question.option_c,
                quiz.question.option_d,
            ]
        }
        for quiz in quizzes
    ]

    return render(request, "insideQuiz.html", {
        "language": language,
        "quiz_data": json.dumps(quiz_data),
        "is_authenticated": request.user.is_authenticated
    })


def start_quiz(request):
    if request.method == "POST":
        lang_id = request.POST.get('language')
        return redirect(f'/insideQuiz?lang={lang_id}')


@csrf_exempt
def save_mcq_answer(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"error": "Login required to save progress"},
            status=401
        )

    data = json.loads(request.body)

    quiz = get_object_or_404(Quiz, id=data["quiz_id"])
    selected = data["selected_option"]
    is_correct = selected == quiz.question.correct_option

    attempt, _ = UserMCQAttempt.objects.get_or_create(
        user=request.user,
        quiz=quiz,
        defaults={
            "selected_option": selected,
            "is_correct": is_correct,
            "completed": is_correct
        }
    )

    if not attempt.is_correct:
        attempt.selected_option = selected
        attempt.is_correct = is_correct
        attempt.completed = is_correct
        attempt.save()

    return JsonResponse({"correct": is_correct})

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
import json

def debugging_quiz(request):
    lang_id = request.GET.get("lang")
    if not lang_id:
        return redirect("quiz_home")

    language = get_object_or_404(Language, id=lang_id)

    # ==========================
    # CASE 1: LOGGED-IN USER
    # ==========================
    if request.user.is_authenticated:

        solved_correct = UserMCQAttempt.objects.filter(
            user=request.user,
            quiz__quiz_type="DEBUG",
            is_correct=True
        ).values_list("quiz_id", flat=True)

        solved_wrong = UserMCQAttempt.objects.filter(
            user=request.user,
            quiz__quiz_type="DEBUG",
            is_correct=False
        ).values_list("quiz_id", flat=True)

        wrong_quizzes = Quiz.objects.filter(
            id__in=solved_wrong,
            quiz_type="DEBUG",
            language=language
        )

        new_quizzes = Quiz.objects.filter(
            quiz_type="DEBUG",
            language=language
        ).exclude(id__in=solved_correct).exclude(id__in=solved_wrong)

        quizzes = list(wrong_quizzes) + list(new_quizzes)
        quizzes = quizzes[:10]

    # ==========================
    # CASE 2: GUEST USER
    # ==========================
    else:
        quizzes = Quiz.objects.filter(
            quiz_type="DEBUG",
            language=language
        ).order_by("?")[:10]

    if not quizzes:
        return HttpResponse("All Debugging questions solved 🎉")

    quiz_data = []
    for quiz in quizzes:
        q = quiz.question
        quiz_data.append({
            "quiz_id": quiz.id,
            "question": q.question_text,
            "options": [
                q.option_a,
                q.option_b,
                q.option_c,
                q.option_d,
            ],
            "correct": q.correct_option,  # used for UI highlight
        })

    return render(request, "DebuggingQuiz.html", {
        "quiz_data": json.dumps(quiz_data),
        "lang_id": lang_id,
        "is_authenticated": request.user.is_authenticated
    })


# from django.contrib.auth.decorators import login_required

# @login_required
def quiz_summary(request):
    ids = request.GET.get("ids")

    if not ids:
        return HttpResponse("No quiz session found", status=400)

    quiz_ids = json.loads(ids)

    attempts = (
        UserMCQAttempt.objects
        .filter(
            user=request.user,
            quiz_id__in=quiz_ids   # 🔥 ONLY CURRENT QUIZ
        )
        .select_related("quiz__question")
        .order_by("attempted_at")
    )

    summary = []

    for att in attempts:
        q = att.quiz.question
        summary.append({
            "question": q.question_text,
            "options": {
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d,
            },
            "correct": q.correct_option,
            "selected": att.selected_option,
            "is_correct": att.is_correct,
            "explanation": q.explanation,
        })

    return render(request, "quiz_summary.html", {
        "summary": summary
    })


def get_quiz_questions(user, language, limit=10):
    attempted_wrong = UserMCQAttempt.objects.filter(
        user=user,
        is_correct=False
    ).values_list('quiz_id', flat=True)

    quizzes = Quiz.objects.filter(
        Q(id__in=attempted_wrong) |
        Q(language=language)
    ).distinct().order_by('?')[:limit]

    return quizzes


def get_quizzes(user, language, quiz_type, limit=10):
    solved_correct = UserMCQAttempt.objects.filter(
        user=user,
        is_correct=True
    ).values_list("quiz_id", flat=True)

    solved_wrong = UserMCQAttempt.objects.filter(
        user=user,
        is_correct=False
    ).values_list("quiz_id", flat=True)

    wrong = Quiz.objects.filter(
        id__in=solved_wrong,
        quiz_type=quiz_type,
        language=language
    )

    new = Quiz.objects.filter(
        quiz_type=quiz_type,
        language=language
    ).exclude(
        id__in=solved_correct
    ).exclude(
        id__in=solved_wrong
    )

    quizzes = list(wrong) + list(new)
    return quizzes[:limit]