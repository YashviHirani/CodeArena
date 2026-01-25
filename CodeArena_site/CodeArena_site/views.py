from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
import json
from CodeArena_app.models import Language, Quiz, UserMCQAttempt


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
    return render(request, 'quiz.html', {'languages': languages})


# ✅ SINGLE, CORRECT VERSION

def inside_quiz(request):
    language_id = request.GET.get('lang')

    if not language_id:
        return HttpResponse("Language not provided", status=400)

    language = get_object_or_404(Language, id=language_id)

    quizzes = (
        Quiz.objects
        .select_related('question')
        .filter(language=language)
        .order_by('?')[:10]
    )

    if not quizzes.exists():
        return HttpResponse("No quiz questions available", status=404)

    # 🔥 Convert Django objects → JS-friendly JSON
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
                q.option_d
            ],
            "answer": q.correct_option
        })

    return render(request, 'insideQuiz.html', {
        "language": language,
        "quiz_data": json.dumps(quiz_data)
    })

def start_quiz(request):
    if request.method == "POST":
        lang_id = request.POST.get('language')
        return redirect(f'/insideQuiz?lang={lang_id}')


def save_mcq_answer(request):
    if request.method == "POST":
        quiz_id = request.POST.get("quiz_id")
        selected_option = request.POST.get("selected_option")

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


def DebuggingQuiz(request):
    return render(request, "DebuggingQuiz.html")


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
