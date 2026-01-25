from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, Language, MCQ, Quiz, Topic, Problem

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'rank', 'points', 'current_streak')
    search_fields = ('user__username', 'skills')

@admin.register(MCQ)
class MCQAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'correct_option')

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('language', 'difficulty', 'question')
    list_filter = ('language', 'difficulty')

# Simple registration for the rest
admin.site.register(Language)
admin.site.register(Topic)
admin.site.register(Problem)