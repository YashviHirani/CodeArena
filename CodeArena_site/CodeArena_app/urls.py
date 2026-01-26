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
    path('quiz/', views.quiz_view, name='quiz'),
    path('insideQuiz/', views.insideQuiz_view, name='insideQuiz'),
    path('DebuggingQuiz/', views.DebuggingQuiz_view, name='DebuggingQuiz'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
]
