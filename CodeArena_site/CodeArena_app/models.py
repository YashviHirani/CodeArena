from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# --- Core User Model ---

class User(AbstractUser):
    # AbstractUser already contains username, email, password, etc.
    # Keep this empty unless adding platform-wide auth fields.
    pass

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    profile_img = models.ImageField(upload_to='media/', default='default.png', blank=True)
    full_name = models.CharField(max_length=100, blank=True)
    summary = models.TextField(max_length=500, blank=True)
    dob = models.DateField(null=True, blank=True)
    
    # Social Links
    github = models.URLField(max_length=200, blank=True)
    linkedin = models.URLField(max_length=200, blank=True)
    
    # Stats 
    points = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    easy_solved = models.IntegerField(default=0)
    medium_solved = models.IntegerField(default=0)
    hard_solved = models.IntegerField(default=0)
    
    # Streak & Activity
    total_active_days = models.IntegerField(default=0)
    max_streak = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)

    skills = models.CharField(max_length=500, blank=True, help_text="Enter skills separated by commas")

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_skills_list(self):
        return [skill.strip() for skill in self.skills.split(',')] if self.skills else []

# --- Learning Content Models ---

class Language(models.Model):
    LANGUAGE_CHOICES = [
        ('PY', 'Python'),
        ('JAVA', 'Java'),
        ('JS', 'JavaScript'),
        ('HTML', "HTML"),
    ]
    TYPE_CHOICES = [
        ("F", "Frontend"),
        ("B", "Backend"),
    ]
    
    name = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    lang_type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    def __str__(self):
        return self.get_name_display()

class MCQ(models.Model):
    OPTION_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ]
    
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)

    def __str__(self):
        return self.question_text[:50]

class Quiz(models.Model):
    DIFFICULTY_CHOICES = [
        ("H", "Hard"),
        ("M", "Medium"),
        ("E", "Easy")
    ]
    
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='quizzes')
    question = models.ForeignKey(MCQ, on_delete=models.CASCADE, related_name='in_quizzes')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)

    class Meta:
        verbose_name_plural = "Quizzes"

# --- Coding Problems Models ---

class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    topic = models.ForeignKey(
        Topic, 
        on_delete=models.CASCADE, 
        related_name='problems'
    )
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_problems'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title