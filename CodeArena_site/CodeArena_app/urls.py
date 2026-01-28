# from django.urls import path
# from .views import signup_view, profile_view

# urlpatterns = [
#     path("signup/", signup_view, name="signup"),
#     path("profile/", profile_view, name="profile"),
# ]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('insideQuiz/', views.insideQuiz_view, name='insideQuiz'),
    path('DebuggingQuiz/', views.DebuggingQuiz_view, name='DebuggingQuiz'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path("update-skills/", views.update_skills, name="update_skills"),
    path("problem/<int:problem_id>/", views.problem_detail_view, name="problem_detail"),
    path("submit/<int:problem_id>/", views.submit_solution, name="submit_solution"),


    path('quiz/', views.quiz_home, name='quiz'),
    path('quiz/start/', views.start_quiz, name='start_quiz'),
    path('quiz/<int:language_id>/', views.inside_quiz, name='insideQuiz'),
    path('quiz/save-answer/', views.save_mcq_answer, name='save_mcq_answer'),     
]
