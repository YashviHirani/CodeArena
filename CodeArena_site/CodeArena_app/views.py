from django.shortcuts import render, get_object_or_404, redirect
from .models import UserProfile, Problem, Topic, DailySubmission, ProblemSubmission,ContactMessage
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.db.models import Q,OuterRef, Subquery, Value, CharField,Count
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import localtime, now  # Required for submit_solution
from datetime import date, datetime, timedelta
import json
from django.template.loader import render_to_string
from django.db.models.functions import Coalesce
from django.db import transaction
from django.views.decorators.http import require_POST
from django.contrib import messages


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
    # Fetch a problem to display. 
    # For a guest dashboard, maybe you want the first problem or a "Daily Challenge"
    problem = Problem.objects.first() 

    # if the database is empty, problem will be None
    if not problem:
        # Handle empty DB (optional: create a dummy placeholder or redirect)
        pass 

    context = {
        'problem': problem,
        # ... any other context variables
    }
    
    return render(request, 'guestdashboard.html', context)

# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # check if user exists
        if not User.objects.filter(username=username).exists():
            return render(request, "login.html", {
                "error": "No user found"
            })

        # verify encrypted password
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

        # check username
        if User.objects.filter(username=username).exists():
            return render(request, "signup.html", {
                "error": "Username already exists. Please choose another."
            })

        # check email
        if User.objects.filter(email=email).exists():
            return render(request, "signup.html", {
                "error": "Email already registered."
            })

        # create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # specify the backend to avoid the ValueError
        # we use the standard Django ModelBackend
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect("complete_profile")
    
    return render(request, "signup.html")

@login_required
def complete_profile(request):
    profile = request.user.profile

    # if already completed --> go dashboard
    if profile.profile_completed:
        return redirect("dashboard")

    if request.method == "POST":

        # if skip button clicked
        if "skip" in request.POST:
            profile.profile_completed = True
            profile.save()
            return redirect("dashboard")

        # save optional fields
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
@login_required
def dashboard_view(request):

    # Fetch filters
    query = request.GET.get("q", "").strip()
    difficulty = request.GET.get("difficulty", "all")
    topic_id = request.GET.get("topic", "all")

    # Base queryset
    user_submissions = ProblemSubmission.objects.filter(
        user=request.user,
        problem=OuterRef("pk")
    )

    problems = (
        Problem.objects
        .select_related("topic")
        .annotate(
            status=Coalesce(
                Subquery(
                    user_submissions.values("is_correct")[:1]
                ),
                Value(None)
            )
        )
    )

    # Apply filters
    if query:
        problems = problems.filter(title__icontains=query)

    if difficulty != "all":
        problems = problems.filter(difficulty=difficulty)

    if topic_id != "all":
        problems = problems.filter(topic_id=topic_id)

    # Counts
    total_problems = Problem.objects.count()
    solved_count = ProblemSubmission.objects.filter(
        user=request.user,
        is_correct=True
    ).count()

    # Rank calculation
    ranked_profiles = (
        UserProfile.objects
        .order_by('-points')
        .values_list('user_id', flat=True)
    )

    ranked_list = list(ranked_profiles)

    try:
        rank = ranked_list.index(request.user.id) + 1
    except ValueError:
        rank = None

    context = {
        "problems": problems,
        "topics": Topic.objects.all(),
        "total_problems": total_problems,
        "solved_count": solved_count,
        "rank": rank,
    }

    # AJAX response
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        # frontend replaces table without refreshing page
        html = render_to_string(
            "problem_table.html",
            context,
            request=request
        )
        return JsonResponse({"html": html})

    return render(request, "dashboard.html", context)


# ---------------- PROFILE ----------------
@login_required
def profile_view(request):
    user = request.user # gets the currently logged-in user
    # ensure streaks are updated (e.g., if a streak broke yesterday)
    update_user_streaks(user)
    profile = user.profile # made obj of UserProfile of particular user so now we have access to all fields of that model
    
   # --- LANGUAGE CALCULATIONS ---
    # --- 1. JAVA STATS ---
    total_java = Problem.objects.exclude(starter_code_java="").count()
    # Using __iexact to be case-insensitive
    solved_java = ProblemSubmission.objects.filter(
        user=user, 
        is_correct=True, 
        language_used__iexact='java'
    ).count()

    # --- 2. PYTHON STATS ---
    total_python = Problem.objects.exclude(starter_code_python="").count()
    solved_python = ProblemSubmission.objects.filter(
        user=user, 
        is_correct=True, 
        language_used__iexact='python'
    ).count()

    # --- 3. MATH CALCULATIONS ---
    java_percent = int((solved_java / total_java) * 100) if total_java > 0 else 0
    python_percent = int((solved_python / total_python) * 100) if total_python > 0 else 0

    # --- ACCURATE TOTAL SOLVED (Same logic as dashboard) ---
    # counts unique problems solved correctly
    total_solved = ProblemSubmission.objects.filter(
        user=user,
        is_correct=True
    ).count()

    # get unique topic objects for problems solved correctly by current user
    mastered_topics = Topic.objects.filter(
        problems__problemsubmission__user=user,
        problems__problemsubmission__is_correct=True
    ).distinct()

    # to get daily submissions
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
        "mastered_topics": mastered_topics,
        "java_percent": java_percent,
        "python_percent": python_percent,
        "solved_java": solved_java,
        "total_java": total_java,
        "solved_python": solved_python,
        "total_python": total_python,
    }

    return render(request, "profile.html", context)

# ---------------- QUIZ ----------------
@login_required
def leaderboard_view(request):
    query = request.GET.get("q", "").strip()

    # global ranking(cards)

    global_profiles = (
        UserProfile.objects
        .filter(points__gt=0)
        .select_related("user")
        .order_by("rank")   
    )

    ranked_global = global_profiles
    top_users = ranked_global[:3]  # always global top 3

    # filtered table search
    filtered_profiles = ranked_global

    if query:
        filtered_profiles = [
            p for p in ranked_global
            if query.lower() in p.user.username.lower()
        ]

    # AJAX response(table only)
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

def recalculate_ranks():
    """
    Dense ranking:
    Same points --> same rank.
    """

    with transaction.atomic():

        # make user's list by sorting on basis of points in descending order
        profiles = (
            UserProfile.objects
            .filter(points__gt=0)
            .order_by("-points", "user__username")
        )

        last_points = None
        current_rank = 0

        for index, profile in enumerate(profiles, start=1):
            # compare current user rank with previous user rank
            if profile.points != last_points:
                current_rank = index
                last_points = profile.points

            # if current user rank != rank in database then update rank in db
            if profile.rank != current_rank:
                profile.rank = current_rank
                profile.save(update_fields=["rank"])


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

# ------------------- Update skill in database -----------------------
@login_required
@require_POST
def update_skills(request):
    profile = request.user.profile
    skill = request.POST.get("skill", "").strip()
    action = request.POST.get("action")

    if not skill:
        return JsonResponse({"error": "Skill cannot be empty"}, status=400)

    # normalize skills (case-insensitive handling)
    skill_normalized = skill.lower()

    # convert existing skills to normalized list
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

    # ================= update attempt =================
    if not created:
        attempt.attempts += 1
        attempt.selected_option = selected_option
        attempt.is_correct = is_correct

    points_added = 0

    if is_correct:
        if not attempt.completed:

            difficulty = quiz.difficulty
            attempt_no = attempt.attempts

            if attempt_no <= 3:
                points_added = QUIZ_POINTS[difficulty][attempt_no]
            else:
                points_added = AFTER_THIRD_ATTEMPT_POINTS

            profile.points += points_added
            attempt.completed = True
            profile.save(update_fields=["points"])
            recalculate_ranks()

    attempt.save()

    return JsonResponse({
        "correct": is_correct,
        "attempts": attempt.attempts,
        "points_added": points_added,
        "quiz_type": quiz.quiz_type,
    })


def quiz(request):
    return render(request, "quiz.html")

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

    # ================= debugging attempt breakdown =================
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

@login_required
def inside_quiz(request):
    language_id = request.GET.get("lang")
    if not language_id:
        return HttpResponse("Language not provided", status=400)

    language = get_object_or_404(Language, id=language_id)

    # list of quiz IDs user solved correctly.
    solved_correct = UserMCQAttempt.objects.filter(
        user=request.user,
        is_correct=True
    ).values_list("quiz_id", flat=True)

    # quiz IDs answered incorrectly.
    solved_wrong = UserMCQAttempt.objects.filter(
        user=request.user,
        is_correct=False
    ).values_list("quiz_id", flat=True)

    # Previously wrong quizzes (revision questions)
    wrong_quizzes = Quiz.objects.filter(
        id__in=solved_wrong,
        language=language,
        quiz_type="MCQ"
    ).select_related("question")

    # New unseen quizzes
    new_quizzes = Quiz.objects.filter(
        language=language,
        quiz_type="MCQ"
    ).exclude(
        id__in=solved_correct
    ).exclude(
        id__in=solved_wrong
    ).select_related("question")

    # Combine --> wrong first, then new
    quizzes = list(wrong_quizzes) + list(new_quizzes)
    quizzes = quizzes[:10]

    # all quizzes completed
    if not quizzes:
        return render(request, "quiz_completed.html", {
            "message": "All MCQ questions solved 🎯",
            "sub_message": "Great job! You have completed all available MCQ questions for this language."
        })

    # prepare data for frontend
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
        "is_authenticated": True
    })

def quiz_completed(request):
    return render(request, "quiz_completed.html")

@login_required
def debugging_quiz(request):
    lang_id = request.GET.get("lang")
    if not lang_id:
        return redirect("quiz_home")

    language = get_object_or_404(Language, id=lang_id)

    # authenticated user only 

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

    # Previously wrong debugging quizzes (revision first)
    wrong_quizzes = Quiz.objects.filter(
        id__in=solved_wrong,
        quiz_type="DEBUG",
        language=language
    ).select_related("question")

    # New unseen debugging quizzes
    new_quizzes = Quiz.objects.filter(
        quiz_type="DEBUG",
        language=language
    ).exclude(
        id__in=solved_correct
    ).exclude(
        id__in=solved_wrong
    ).select_related("question")

    # Combine --> wrong first, then new
    quizzes = list(wrong_quizzes) + list(new_quizzes)
    quizzes = quizzes[:10]

    # all quizzes completed

    if not quizzes:
        return render(request, "quiz_completed.html", {
            "message": "All Debugging questions solved 🎉",
            "sub_message": "Great job! You’ve completed all available debugging challenges."
        })

    # prepare data for frontend
    quiz_data = [
        {
            "quiz_id": quiz.id,
            "question": quiz.question.question_text,
            "code_snippet": quiz.question.code_snippet,
            "options": [
                quiz.question.option_a,
                quiz.question.option_b,
                quiz.question.option_c,
                quiz.question.option_d,
            ],
            "correct": quiz.question.correct_option,  # if needed by frontend
        }
        for quiz in quizzes
    ]

    return render(request, "DebuggingQuiz.html", {
        "quiz_data": json.dumps(quiz_data),
        "lang_id": lang_id,
        "is_authenticated": True
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
            "code_snippet": getattr(q, "code_snippet", ""),
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


@login_required
def problem_detail(request, problem_id):

    problem = get_object_or_404(Problem, id=problem_id)
    example = getattr(problem, "example", None) 
    testcases = problem.testcases.all()            

    context = {
        "problem": problem,
        "example": example,
        "testcases": testcases,
        "starter_code": {
            "java": problem.starter_code_java,
            "python": problem.starter_code_python,
        }
    }
    return render(request, "problemPage.html", context)


@csrf_exempt
@login_required
def submit_solution(request, problem_id):
    from .judge import judge_code  # imports judge function

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    # frontend sends json like {"code": "print(5)","language": "python"} 
    try:
        data = json.loads(request.body) # json.loads() --> converts it to Python dictionary & request.body = raw bytes
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # 1. collecting data
    code = data.get("code") # gets user code
    language = data.get("language") # gets selected code language by user
    problem = get_object_or_404(Problem, id=problem_id) # gets the problem solved by user
    profile = request.user.profile # gets logged in user profile

    # prevents empty submission.
    if not code or not language:
        return JsonResponse({"error": "Missing code or language"}, status=400)

    # 2. run the judge
    testcases = problem.testcases.all()
    result = judge_code(language, code, testcases)

    # 3. now we update the total submission for user
    profile.total_submissions += 1
    
    #----------- for streak ------------------
    today = now().date()
    # if entry exists for today then increment counter otherwise create and increment counter(daily count+=1)
    daily, _ = DailySubmission.objects.get_or_create(
        user=request.user,
        date=today
    )
    daily.count += 1
    daily.save()

    #----------------------------------------

    # 4. handle verdict
    response = {"verdict": result["verdict"]} # creates response dictionary to send back to frontend.

    submission, created = ProblemSubmission.objects.get_or_create(
        user=request.user,
        problem=problem,
        defaults={"is_correct": False, "language_used": language}
    )

    # recalculate streaks after updating daily submission
    update_user_streaks(request.user)

    if result["verdict"] == "Accepted":
        # sends performance metrics to frontend.
        response["time_ms"] = result["time_ms"]
        response["memory_mb"] = result["memory_mb"]

        # If not already marked correct
        if not submission.is_correct:
            submission.language_used = language # Update it if they switch languages and solve it
            submission.is_correct = True
            # submission.save(update_fields=["is_correct"])
            submission.save()

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
        # If failed attempt --> ensure submission exists but not correct
        if created:
            submission.is_correct = False
            submission.save(update_fields=["is_correct"])

        # for frontend to show exact error and failed testcase
        response["failed_testcase"] = result.get("failed_testcase")
        response["error"] = result.get("error")

    profile.save()
    recalculate_ranks()

    return JsonResponse(response) # sends JSON back to frontend --> frontend receives and updates UI

def contact_submit(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Create and save the object
        new_message = ContactMessage(
            name=name, 
            email=email, 
            subject=subject, 
            message=message
        )
        new_message.save()

        messages.success(request, "Your message has been sent successfully!")
        return redirect('home') 
    
    return redirect('home')

# this func recalculates the current streak, max streak and total active days for a user --> called after every submission
def update_user_streaks(user):
    profile = user.profile
    # filters DailySubmission table for user & orders by date descending (latest first)
    dates_query = DailySubmission.objects.filter(user=user).order_by('-date')
    dates = list(dates_query.values_list('date', flat=True)) # extracts only date field and converts QuerySet to python list

    # if user has no submission history then :-
    if not dates:
        profile.current_streak = 0
        profile.max_streak = 0
        profile.total_active_days = 0 
        profile.save()
        return

    # calculate Total Active Days
    profile.total_active_days = dates_query.count() # count = number of days user submitted.

    # to check if streak is active
    today = now().date()
    yesterday = today - timedelta(days=1)
    
    # --- Calculate Current Streak ---
    current = 0
    # Streak is active if user submitted today or yesterday
    if dates[0] == today or dates[0] == yesterday:
        expected_date = dates[0]
        for d in dates:
            if d == expected_date:
                current += 1
                expected_date -= timedelta(days=1)
            else:
                break
    else:
        current = 0
    
    # --- Calculate Max Streak ---
    # Sort ascending for max streak calculation
    dates_asc = sorted(dates)
    max_s = 0
    temp_s = 1
    for i in range(1, len(dates_asc)):
        if dates_asc[i] == dates_asc[i-1] + timedelta(days=1):
            temp_s += 1
        else:
            max_s = max(max_s, temp_s)
            temp_s = 1
    max_s = max(max_s, temp_s)

    profile.current_streak = current
    profile.max_streak = max_s
    profile.save(update_fields=['current_streak', 'max_streak', 'total_active_days'])