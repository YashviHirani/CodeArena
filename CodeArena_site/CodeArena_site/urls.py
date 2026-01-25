"""
URL configuration for CodeArena_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/',views.login,name='login'),
    path('signup/',views.signup, name='signup'),
    path('',views.home,name='home'),
    path("dashboard/",views.dashboard,name='dashboard'),  
    path('profile/',views.profile,name='profile'),
    # path('quiz/',views.quiz,name="quiz"),
    path('insideQuiz',views.inside_quiz,name="insideQuiz"),     
    path('DebuggingQuiz',views.DebuggingQuiz,name="DebuggingQuiz"),     
    path("leaderboard",views.leaderboard,name="leaderboard"),

    path('quiz/', views.quiz_home, name='quiz'),
    path('quiz/start/', views.start_quiz, name='start_quiz'),
    path('quiz/<int:language_id>/', views.inside_quiz, name='insideQuiz'),
    path('quiz/save-answer/', views.save_mcq_answer, name='save_mcq_answer'),                                                                                    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

