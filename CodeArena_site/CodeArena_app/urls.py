# from django.urls import path
# from .views import signup_view, profile_view

# urlpatterns = [
#     path("signup/", signup_view, name="signup"),
#     path("profile/", profile_view, name="profile"),
# ]

from django.contrib import admin
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

from django.conf.urls import handler404
from CodeArena_app.views import custom_404_view

handler404 = "CodeArena_app.views.custom_404_view"


urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    # path('insideQuiz/',views.inside_quiz,name="insideQuiz"), 
    path('DebuggingQuiz/',views.debugging_quiz,name="DebuggingQuiz"),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path("update-skills/", views.update_skills, name="update_skills"),
    path("problem/<int:problem_id>/", views.problem_detail, name="problem_detail"),
    path("submit/<int:problem_id>/", views.submit_solution, name="submit_solution"),
    # path("update-skills/", views.update_skills, name="update_skills"),

    # In your urls.py
    path('profile/edit_profile/', views.edit_profile_view, name='edit_profile'),

    path('quiz/', views.quiz_home, name='quiz_home'),
    path('quiz/start/', views.start_quiz, name='start_quiz'),
    path('quiz/mcq/', views.inside_quiz, name='insideQuiz'),
    path('quiz/debug/', views.debugging_quiz, name='debuggingQuiz'),

    path('quiz/save-answer/', views.save_mcq_answer, name='save_mcq_answer'), 
    path("quiz/summary/", views.quiz_summary, name="quiz_summary"),
    path("quiz/completed/", views.quiz_completed, name="quiz_completed"),


    path("complete-profile/", views.complete_profile, name="complete_profile"),
    
    # path("quiz/summary/", views.quiz_summary, name="quiz_summary"), 
    path("guestdashboard/",views.guestdashboard,name='guestdashboard'),   
]