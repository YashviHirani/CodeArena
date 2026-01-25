from django.shortcuts import render,get_object_or_404,redirect
from django.views.decorators.csrf import csrf_exempt
import random 
from django.http import JsonResponse
from django.db.models import Q 
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from CodeArena_app.models import Language, Quiz, UserMCQAttempt

 



def home(request):
    return render(request,'home.html')
def login(request):
    return render(request,"login.html")
def signup(request):
    return render(request,"signup.html")
def dashboard(request):
    return render(request,"dashboard.html")
def profile(request):
    return render(request,"profile.html")
def quiz(request):
    return render(request,"quiz.html")

# @login_required
def inside_quiz(request, language_id):
    language = get_object_or_404(Language, id=language_id)

    quizzes = Quiz.objects.filter(language=language).exclude(
        usermcqattempt__user=request.user,
        usermcqattempt__completed=True
    ).order_by('?')[:10]

    quiz_data = []
    for quiz in quizzes:
        quiz_data.append({
            "question": quiz.question.question_text,
            "options": [
                quiz.question.option_a,
                quiz.question.option_b,
                quiz.question.option_c,
                quiz.question.option_d,
            ],
            "answer": quiz.question.correct_option,
            "quiz_id": quiz.id
        })

    return render(request, 'insideQuiz.html', {
        "language": language,
        "quiz_data": quiz_data
    })

def DebuggingQuiz(request):
    return render(request,"DebuggingQuiz.html")
def leaderboard(request):
    return render(request,"leaderboard.html")

def quiz_home(request):
    languages = Language.objects.all()
    return render(request, 'quiz.html', {'languages': languages})

def start_quiz(request):
    if request.method == "POST":
        lang_id = request.POST.get('language')
        return redirect('insideQuiz', language_id=lang_id)

# @login_required
def inside_quiz(request, language_id):
    language = get_object_or_404(Language, id=language_id)

    quizzes = list(
        Quiz.objects.filter(language=language)
        .select_related('question')
        .order_by('?')[:10]
    )

    data = []
    for q in quizzes:
        data.append({
            "question": q.question.question_text,
            "options": [
                q.question.option_a,
                q.question.option_b,
                q.question.option_c,
                q.question.option_d,
            ],
            "answer": q.question.correct_option,
            "difficulty": q.get_difficulty_display()
        })

    return render(request, 'insideQuiz.html', {
        "quiz_data": data,
        "language": language
    })


def save_mcq_answer(request):
    if request.method == "POST":
        quiz_id = request.POST.get("quiz_id")
        selected_option = request.POST.get("selected_option")

        quiz = Quiz.objects.get(id=quiz_id)
        is_correct = selected_option == quiz.question.correct_option

        UserMCQAttempt.objects.update_or_create(
            user=request.user,
            quiz=quiz,
            defaults={
                "selected_option": selected_option,
                "is_correct": is_correct,
                "completed": is_correct  # 🔥 THIS IS THE KEY
            }
        )

        return JsonResponse({
            "correct": is_correct
        })

def get_quiz_questions(user, language, limit=10):
    attempted_wrong = UserMCQAttempt.objects.filter(
        user=user,
        is_correct=False
    ).values_list('quiz_id', flat=True)

    quizzes = Quiz.objects.filter(
        Q(id__in=attempted_wrong) | Q(
            id__in=Quiz.objects.filter(language=language)
        )
    ).distinct().order_by('?')[:limit]

    return quizzes

