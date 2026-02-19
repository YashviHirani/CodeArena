from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, Language, MCQ, Quiz, Topic, Problem, TestCase, ExampleTestCase

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
admin.site.register(TestCase)
admin.site.register(ExampleTestCase)

from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    readonly_fields = ('created_at',)

from .models import ProblemSubmission

@admin.register(ProblemSubmission)
class ProblemSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'problem', 'language_used', 'is_correct', 'solved_at')
    list_filter = ('language_used', 'is_correct')
    search_fields = ('user__username', 'problem__title')