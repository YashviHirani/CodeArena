from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

from CodeArena_app.models import Language, Quiz, UserMCQAttempt, MCQ

# from CodeArena.CodeArena_site.CodeArena_app.models import Language, Quiz, UserMCQAttempt


def home(request):
    return render(request, 'home.html')


def login(request):
    return render(request, "login.html")


def signup(request):
    return render(request, "signup.html")


def dashboard(request):
    return render(request, "dashboard.html")


def profile(request):
    return render(request, "profile.html")


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
def debugging_quiz(request):
    lang_id = request.GET.get("lang")
    if not lang_id:
        return HttpResponse("Language not provided", status=400)

    language = get_object_or_404(Language, id=lang_id)

    # ✅ Solved attempts
    solved_correct = UserMCQAttempt.objects.filter(
        user=request.user,
        is_correct=True,
        quiz__quiz_type="DEBUG"
    ).values_list("quiz_id", flat=True)

    solved_wrong = UserMCQAttempt.objects.filter(
        user=request.user,
        is_correct=False,
        quiz__quiz_type="DEBUG"
    ).values_list("quiz_id", flat=True)

    # ❌ repeat wrong
    wrong_quizzes = Quiz.objects.filter(
        id__in=solved_wrong,
        quiz_type="DEBUG",
        language=language
    )

    # 🆕 new quizzes
    new_quizzes = Quiz.objects.filter(
        quiz_type="DEBUG",
        language=language
    ).exclude(
        id__in=solved_correct
    ).exclude(
        id__in=solved_wrong
    )

    quizzes = list(wrong_quizzes) + list(new_quizzes)
    quizzes = quizzes[:10]

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
            "difficulty": quiz.get_difficulty_display(),
            "correct": q.correct_option  # needed for UI feedback
        })

    return render(request, "DebuggingQuiz.html", {
        "quiz_data": json.dumps(quiz_data),
        "lang_id": lang_id
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
