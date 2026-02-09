from django.shortcuts import render, get_object_or_404, redirect
from .models import UserProfile, Problem, Topic, DailySubmission, ProblemSubmission
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import localtime, now  # Required for submit_solution
from datetime import date, datetime, timedelta
import json

from .bst import ProblemBST

from CodeArena_app.models import Language, Quiz, UserMCQAttempt, MCQ

# ================== PROBLEM POINT CONFIG ==================
PROBLEM_POINTS = {
    "easy": 10,
    "medium": 15,
    "hard": 20,
}
# ... rest of your code
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

User = get_user_model()

def guestdashboard(request):
    return render(request,"guestdashboard.html")

# ---------------- LOGIN ----------------
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
        dob = request.POST.get("dob")
        profile.dob = datetime.strptime(dob, "%Y-%m-%d").date() if dob else None
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

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse

from .models import ProblemSubmission

from django.db.models import Count
from .models import Problem, ProblemSubmission, UserProfile

@login_required
def dashboard_view(request):
    search_query = request.GET.get("q", "").strip()
    difficulty = request.GET.get("difficulty", "all")
    topic_id = request.GET.get("topic", "all")

    problems_queryset = Problem.objects.select_related("topic")

    # ---------------- SEARCH ----------------
    if search_query:
        bst = ProblemBST()
        for p in problems_queryset:
            bst.insert(p)
        problems = bst.search_partial(search_query)
    else:
        problems = list(problems_queryset)

    # ---------------- FILTERS ----------------
    if difficulty != "all":
        problems = [p for p in problems if p.difficulty == difficulty]

    if topic_id != "all":
        problems = [p for p in problems if str(p.topic_id) == topic_id]

    # ---------------- STATUS (Solved / Wrong / Not Attempted) ----------------
    submissions = ProblemSubmission.objects.filter(
        user=request.user,
        problem__in=problems
    )

    submission_map = {
        s.problem_id: s.is_correct
        for s in submissions
    }

    for problem in problems:
        if problem.id in submission_map:
            problem.status = "solved" if submission_map[problem.id] else "wrong"
        else:
            problem.status = "not_attempted"

    # ---------------- DASHBOARD STATS ----------------
    total_problems = Problem.objects.count()

    solved_count = ProblemSubmission.objects.filter(
        user=request.user,
        is_correct=True
    ).count()

    # Rank calculation (based on points)
    ranked_profiles = (
        UserProfile.objects
        .filter(points__gt=0)
        .order_by("-points")
        .values_list("user_id", flat=True)
    )

    try:
        rank = list(ranked_profiles).index(request.user.id) + 1
    except ValueError:
        rank = "—"

    # ---------------- AJAX ----------------
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
        "total_problems": total_problems,
        "solved_count": solved_count,
        "rank": rank,
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

# ----------------------- QUIZ ------------------------

def start_quiz(request):
    if request.method == "POST":
        lang_id = request.POST.get('language')
        return redirect(f'/insideQuiz?lang={lang_id}')
@csrf_exempt
@login_required
def save_mcq_answer(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    data = json.loads(request.body)
    quiz_id = data.get("quiz_id")
    selected_option = data.get("selected_option")

    quiz = get_object_or_404(Quiz, id=quiz_id)
    profile = request.user.profile

    is_correct = selected_option == quiz.question.correct_option

    attempt, created = UserMCQAttempt.objects.get_or_create(
        user=request.user,
        quiz=quiz,
        defaults={
            "selected_option": selected_option,
            "is_correct": is_correct,
            "completed": False,
            "attempts": 1,
        }
    )

    # ================= UPDATE ATTEMPT =================
    if not created:
        attempt.attempts += 1
        attempt.selected_option = selected_option
        attempt.is_correct = is_correct

    # ================= ADD POINTS ONLY ON FIRST SUCCESS =================
    points_added = 0

    if is_correct and not attempt.completed:
        difficulty = quiz.difficulty  # "E", "M", "H"
        attempt_no = attempt.attempts

        points_added = QUIZ_POINTS.get(difficulty, {}).get(
            attempt_no,
            AFTER_THIRD_ATTEMPT_POINTS
        )

        profile.points += points_added
        attempt.completed = True
        profile.save()

    attempt.save()

    return JsonResponse({
        "correct": is_correct,
        "attempts": attempt.attempts,
        "points_added": points_added,
        "quiz_type": quiz.quiz_type,
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

    def calc_stats(qs):
        return {
            "first": qs.filter(is_correct=True, attempts=1).count(),
            "second": qs.filter(is_correct=True, attempts=2).count(),
            "third_plus": qs.filter(is_correct=True, attempts__gte=3).count(),
            "wrong": qs.filter(is_correct=False).count(),
        }

    mcq_stats = calc_stats(attempts.filter(quiz__quiz_type="MCQ"))
    debug_stats = calc_stats(attempts.filter(quiz__quiz_type="DEBUG"))


    context = {
        "mcq_labels": json.dumps(mcq_labels),
        "mcq_points": json.dumps(mcq_points),

        # MCQ
        "mcq_first": mcq_stats["first"],
        "mcq_second": mcq_stats["second"],
        "mcq_third_plus": mcq_stats["third_plus"],
        "mcq_wrong": mcq_stats["wrong"],

        # DEBUG
        "debug_first": debug_stats["first"],
        "debug_second": debug_stats["second"],
        "debug_third_plus": debug_stats["third_plus"],
        "debug_wrong": debug_stats["wrong"],

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
        return render(request, "quiz_completed.html", {
            "message": "All MCQ questions solved 🎯",
            "sub_message": "Sorry — there are no more MCQ questions available right now. Great job completing them all!"
        })


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

def quiz_completed(request):
    return render(request, "quiz_completed.html")


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
        return render(request, "quiz_completed.html", {
            "message": "All Debugging questions solved 🎉",
            "sub_message": "Sorry — you’ve completed all available debugging challenges. New ones coming soon!"
        })



    quiz_data = []
    for quiz in quizzes:
        q = quiz.question
        quiz_data.append({
            "quiz_id": quiz.id,
            "question": q.question_text,
            "code_snippet": q.code_snippet,   # 👈 ADD THIS
            "options": [
                q.option_a,
                q.option_b,
                q.option_c,
                q.option_d,
            ],
            "correct": q.correct_option,
        })


    return render(request, "DebuggingQuiz.html", {
        "quiz_data": json.dumps(quiz_data),
        "lang_id": lang_id,
        "is_authenticated": request.user.is_authenticated
    })

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
            "code_snippet": getattr(q, "code_snippet", ""),   # safe access
            "quiz_type": att.quiz.quiz_type,
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
        }
    }
    return render(request, "problemPage.html", context)


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

    # 4️⃣ HANDLE VERDICT
    response = {"verdict": result["verdict"]}

    submission, created = ProblemSubmission.objects.get_or_create(
        user=request.user,
        problem=problem,
        defaults={"is_correct": False}
    )

    if result["verdict"] == "Accepted":
        response["time_ms"] = result["time_ms"]
        response["memory_mb"] = result["memory_mb"]

        # If not already marked correct
        if not submission.is_correct:
            submission.is_correct = True
            submission.save(update_fields=["is_correct"])

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
            response["points_added"] = 0
            response["status"] = "already_solved"

    else:
        # If failed attempt → ensure submission exists but not correct
        if created:
            submission.is_correct = False
            submission.save(update_fields=["is_correct"])

        response["failed_testcase"] = result.get("failed_testcase")
        response["error"] = result.get("error")

    profile.save()

    return JsonResponse(response)