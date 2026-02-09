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
from .models import ExampleTestCase

# Move these to the TOP of views.py (after imports)

# ================== PROBLEM POINT CONFIG ==================
PROBLEM_POINTS = {
    "easy": 10,
    "medium": 15,
    "hard": 20,
}

# ================== QUIZ POINT CONFIG ==================
QUIZ_POINTS = {
    "H": {1: 10, 2: 9, 3: 8},
    "M": {1: 8,  2: 7, 3: 6},
    "E": {1: 6,  2: 5, 3: 4},
}
AFTER_THIRD_ATTEMPT_POINTS = 2
# for Error page 

def custom_404_view(request, exception):
    return render(request, "404.html", status=404)
# ---------------- HOME ----------------

def home_view(request):
    return render(request, "home.html")

# ---------------- LOGIN ----------------

User = get_user_model()
def guestdashboard(request):
    return render(request,"guestdashboard.html")
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

from django.contrib import messages

def signup_view(request):
    if request.method == "POST":
        username = request.POST["username"].strip()
        email = request.POST["email"].strip()
        password = request.POST["password"]

        # ✅ CHECK USERNAME
        if User.objects.filter(username=username).exists():
            return render(request, "signup.html", {
                "error": "Username already exists. Please choose another."
            })

        # ✅ CHECK EMAIL (optional but recommended)
        if User.objects.filter(email=email).exists():
            return render(request, "signup.html", {
                "error": "Email already registered."
            })

        # ✅ CREATE USER
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        login(request, user)
        return redirect("complete_profile")


    return render(request, "signup.html")

# from django.contrib.auth.decorators import login_required

@login_required
def complete_profile(request):
    profile = request.user.profile

    # If already completed → go dashboard
    if profile.profile_completed:
        return redirect("dashboard")

    if request.method == "POST":

        # If skip button clicked
        if "skip" in request.POST:
            profile.profile_completed = True
            profile.save()
            return redirect("dashboard")

        # Save optional fields
        profile.profile_img = request.FILES.get("profile_img") or profile.profile_img
        profile.full_name = request.POST.get("full_name", "")
        profile.summary = request.POST.get("summary", "")
        profile.dob = request.POST.get("dob") or None
        profile.github = request.POST.get("github", "")
        profile.linkedin = request.POST.get("linkedin", "")
        profile.skills = request.POST.get("skills", "")

        profile.profile_completed = True
        profile.save()

        return redirect("dashboard")

    return render(request, "onboarding.html")



# ---------------- DASHBOARD ----------------

from django.db.models import Q
from django.template.loader import render_to_string
from .models import Problem, Topic

@login_required
def dashboard_view(request):

    search_query = request.GET.get("q", "").strip()
    difficulty = request.GET.get("difficulty", "all")
    topic_id = request.GET.get("topic", "all")

    problems = Problem.objects.select_related("topic").all()

    # 🔍 SEARCH FILTER
    if search_query:
        problems = problems.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(topic__name__icontains=search_query)
        )

    # 🎯 DIFFICULTY FILTER
    if difficulty != "all":
        problems = problems.filter(difficulty=difficulty)

    # 📚 TOPIC FILTER
    if topic_id != "all":
        problems = problems.filter(topic_id=topic_id)

    # ✅ AJAX RESPONSE
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "problem_table.html",
            {"problems": problems},
            request=request
        )
        return JsonResponse({"html": html})

    return render(request, "dashboard.html", {
        "problems": problems,
        "topics": Topic.objects.all(),
    })


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

from django.contrib.auth.decorators import login_required
from .models import UserProfile

# @login_required
# def leaderboard_view(request):
#     profiles = (
#         UserProfile.objects
#         .filter(points__gt=0)
#         .select_related("user")
#         .order_by("-points", "user__username")
#     )

#     ranked_profiles = []
#     last_points = None
#     rank = 0

#     for index, profile in enumerate(profiles, start=1):
#         if profile.points != last_points:
#             rank = index
#             last_points = profile.points
#         profile.rank = rank
#         ranked_profiles.append(profile)

#     # 🔥 TOP 3 USERS
#     top_users = ranked_profiles[:3]

#     return render(request, "leaderboard.html", {
#         "profiles": ranked_profiles,
#         "top_users": top_users
#     })


from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Q

@login_required
def leaderboard_view(request):
    query = request.GET.get("q", "").strip()

    # =========================
    # 🔥 GLOBAL RANKING (Cards)
    # =========================
    global_profiles = (
        UserProfile.objects
        .filter(points__gt=0)
        .select_related("user")
        .order_by("-points", "user__username")
    )

    ranked_global = []
    last_points = None
    rank = 0

    for index, profile in enumerate(global_profiles, start=1):
        if profile.points != last_points:
            rank = index
            last_points = profile.points
        profile.rank = rank
        ranked_global.append(profile)

    top_users = ranked_global[:3]  # 🔥 Always global top 3


    # =========================
    # 🔍 FILTERED TABLE SEARCH
    # =========================
    filtered_profiles = ranked_global

    if query:
        filtered_profiles = [
            p for p in ranked_global
            if query.lower() in p.user.username.lower()
        ]

    # =========================
    # AJAX RESPONSE (TABLE ONLY)
    # =========================
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        table_html = render_to_string(
            "leaderboard_table.html",
            {"profiles": filtered_profiles},
            request=request
        )

        return JsonResponse({
            "table_html": table_html
        })

    return render(request, "leaderboard.html", {
        "profiles": ranked_global,   # full table initially
        "top_users": top_users       # always global
    })


# ---------------- EDIT PROFILE ----------------

@login_required
def edit_profile_view(request):
    user = request.user
    profile = user.profile

    if request.method == "POST":
        new_username = request.POST.get("username")
        
        # Check if the new username is already taken by someone ELSE
        if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
            return render(request, "edit_profile.html", {
                "profile": profile, 
                "user": user, 
                "error": "This username is already taken by another user!"
            })

        # Update User fields
        user.username = new_username
        user.email = request.POST.get("email")
        user.save()

        # Update Profile fields
        profile.full_name = request.POST.get("full_name")
        profile.github = request.POST.get("github")
        profile.linkedin = request.POST.get("linkedin")
        profile.twitter = request.POST.get("twitter")
        profile.location = request.POST.get("location")
        profile.summary = request.POST.get("summary")
        profile.education = request.POST.get("education")
        profile.work_experience = request.POST.get("experience")
        
        if request.FILES.get("profile_img"):
            profile.profile_img = request.FILES.get("profile_img")
            
        profile.save()
        
        # Redirect back to the profile page
        return redirect("profile")

    return render(request, "edit_profile.html", {"profile": profile, "user": user})
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

# ------------------- Dashboard : to load problems from database  -----------------------

from .models import Problem

@login_required
def dashboard_view(request):
    problems = Problem.objects.all()

    return render(request, "dashboard.html", {
        "problems": problems
    })

# ------------------- PROBLEM PAGE (LOAD DATA DYNAMICALLY) -----------------------
# from .models import Problem

# @login_required
# def problem_detail_view(request, problem_id):
#     problem = Problem.objects.get(id=problem_id)

#     return render(request, "problemPage.html", {
#         "problem": problem
#     })

# ------------------- SUBMISSION LOGIC (THIS IS THE HEART ❤️) -----------------------

from django.utils.timezone import now
from .models import DailySubmission
from django.db import IntegrityError
from .models import ProblemSubmission

# ----------------------- QUIZ ------------------------
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
import json
from CodeArena_app.models import Language, Quiz, UserMCQAttempt, MCQ
from django.views.decorators.csrf import csrf_exempt



# # @login_required
# def inside_quiz(request):
#     language_id = request.GET.get('lang')
#     if not language_id:
#         return HttpResponse("Language not provided", status=400)

#     language = get_object_or_404(Language, id=language_id)

#     # ✅ quizzes already solved correctly by the user
#     solved_quiz_ids = UserMCQAttempt.objects.filter(
#         user_id=request.user.id,
#         is_correct=True
#     ).values_list('quiz_id', flat=True)

#     # ✅ fetch quizzes for this language, excluding solved ones
#     quizzes = (
#         Quiz.objects
#         .select_related('question')
#         .filter(language=language)
#         .exclude(id__in=solved_quiz_ids)
#         .order_by('?')[:10]
#     )

#     if not quizzes.exists():
#         return HttpResponse("You have completed all questions 🎉")

#     quiz_data = [
#         {
#             "quiz_id": quiz.id,
#             "question": quiz.question.question_text,
#             "options": [
#                 quiz.question.option_a,
#                 quiz.question.option_b,
#                 quiz.question.option_c,
#                 quiz.question.option_d,
#             ]
#         }
#         for quiz in quizzes
#     ]

#     return render(request, 'insideQuiz.html', {
#         "language": language,
#         "quiz_data": json.dumps(quiz_data)
#     })

#     return render(request, 'inside_quiz.html', context)
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


from django.db.models import Q
from datetime import datetime, timedelta
import json

def quiz_home(request):
    user = request.user

    # ================= DAILY POINTS (Last 7 Days) =================
    today = datetime.today().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

    mcq_labels = []
    mcq_points = []

    for day in last_7_days:
        mcq_labels.append(day.strftime("%a"))

        daily_points = UserMCQAttempt.objects.filter(
            user=user,
            is_correct=True,
            attempted_at__date=day
        ).count() * 5  # or your logic for daily points

        mcq_points.append(daily_points)

    # ================= DEBUGGING ATTEMPT BREAKDOWN =================
    attempts = UserMCQAttempt.objects.filter(user=user)

    first_correct = attempts.filter(is_correct=True, attempts=1).count()
    second_correct = attempts.filter(is_correct=True, attempts=2).count()
    third_plus_correct = attempts.filter(is_correct=True, attempts__gte=3).count()

    wrong_attempts = attempts.filter(is_correct=False).count()

    context = {
        "mcq_labels": json.dumps(mcq_labels),
        "mcq_points": json.dumps(mcq_points),
        "first_correct": first_correct,
        "second_correct": second_correct,
        "third_plus_correct": third_plus_correct,
        "wrong_attempts": wrong_attempts,
        "languages": Language.objects.all(),
    }

    return render(request, "quiz.html", context)




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




from django.contrib.auth.decorators import login_required

@login_required
def quiz_summary(request):
    ids = request.GET.get("ids")

    if not ids:
        return HttpResponse("No quiz session found", status=400)

    try:
        quiz_ids = json.loads(ids)
    except ValueError:
        return HttpResponse("Invalid quiz ids", status=400)

    attempts = (
        UserMCQAttempt.objects
        .filter(
            user=request.user,
            quiz_id__in=quiz_ids
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

def problem_detail(request, problem_id):
    problem = Problem.objects.get(id=problem_id)

    example = problem.example              # OneToOne
    testcases = problem.testcases.all()    # ForeignKey

    context = {
        "problem": problem,
        "example": example,
        "testcases": testcases,
    }
    return render(request, "problemPage.html", context)


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

@login_required
@require_POST
def update_skills(request):
    profile = request.user.profile
    skill = request.POST.get("skill", "").strip()
    action = request.POST.get("action")

    if not skill:
        return JsonResponse({"error": "Skill cannot be empty"}, status=400)

    # Normalize (case-insensitive handling)
    skill_normalized = skill.lower()

    # Convert existing skills to normalized list
    skills_list = [
        s.strip().lower()
        for s in profile.skills.split(",")
        if s.strip()
    ]

    if action == "add":
        if skill_normalized in skills_list:
            return JsonResponse(
                {"error": "Skill already exists"},
                status=409
            )

        skills_list.append(skill_normalized)

    elif action == "remove":
        if skill_normalized in skills_list:
            skills_list.remove(skill_normalized)

    else:
        return JsonResponse({"error": "Invalid action"}, status=400)

    # Save back to DB (keep comma-separated format)
    profile.skills = ", ".join(skills_list)
    profile.save(update_fields=["skills"])

    return JsonResponse({"success": True})

# @login_required
# def problem_detail(request, problem_id):
#     problem = get_object_or_404(Problem, id=problem_id)

#     example = None
#     try:
#         example = problem.example
#     except ExampleTestCase.DoesNotExist:
#         example = None

#     testcases = problem.testcases.all()

#     context = {
#         "problem": problem,
#         "example": example,
#         "testcases": testcases,
#     }
#     return render(request, "problemPage.html", context)
@login_required
def problem_detail(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)

    example = getattr(problem, "example", None)   # safe OneToOne
    testcases = problem.testcases.all()            # safe FK

    context = {
        "problem": problem,
        "example": example,
        "testcases": testcases,
        # Pass starter code from views.py
        "starter_code": {
            "java": problem.starter_code_java,
            "python": problem.starter_code_python,
            "cpp": problem.starter_code_cpp,
        }
    }
    return render(request, "problemPage.html", context)

from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@login_required
def submit_solution(request, problem_id):
    from .judge import judge_code  # Keeping your judge import

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # 1️⃣ DATA RETRIEVAL
    code = data.get("code")
    language = data.get("language")
    problem = get_object_or_404(Problem, id=problem_id)
    profile = request.user.profile

    if not code or not language:
        return JsonResponse({"error": "Missing code or language"}, status=400)

    # 2️⃣ RUN THE JUDGE (Your Judge Logic)
    testcases = problem.testcases.all()
    result = judge_code(language, code, testcases)

    # 3️⃣ UPDATE SUBMISSION STATS (Your Submission Logic)
    profile.total_submissions += 1
    
    today = now().date()
    daily, _ = DailySubmission.objects.get_or_create(
        user=request.user,
        date=today
    )
    daily.count += 1
    daily.save()

    # 4️⃣ HANDLE SUCCESSFUL VERDICT (Your Points & Marking Logic)
    response = {"verdict": result["verdict"]}

    if result["verdict"] == "Accepted":
        response["time_ms"] = result["time_ms"]
        response["memory_mb"] = result["memory_mb"]

        # Prevent duplicate solving points/marking
        solved, created = ProblemSubmission.objects.get_or_create(
            user=request.user,
            problem=problem,
            defaults={"is_correct": True}
        )

        if created:
            # First time solving: Add points and update counters
            points = PROBLEM_POINTS.get(problem.difficulty, 10)
            profile.points += points

            if problem.difficulty == "easy":
                profile.easy_solved += 1
            elif problem.difficulty == "medium":
                profile.medium_solved += 1
            else:
                profile.hard_solved += 1
            
            response["points_added"] = points
        else:
            response["status"] = "already_solved"
            response["points_added"] = 0
    else:
        # Failed submission logic
        response["failed_testcase"] = result.get("failed_testcase")
        response["error"] = result.get("error")

    # Final save for the profile
    profile.save()

    return JsonResponse(response)
