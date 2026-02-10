from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# --- Core User Model ---

class User(AbstractUser):
    # AbstractUser already contains username, email, password, etc.
    # Keep this empty unless adding platform-wide auth fields.
    class Meta:
        indexes = [
            models.Index(fields=["username"]),
        ]

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='profile',
        unique=True
    )
    profile_img = models.ImageField(upload_to='media/', default='default.png', blank=True)
    full_name = models.CharField(max_length=100, blank=True)
    summary = models.TextField(max_length=500, blank=True)
    dob = models.DateField(null=True, blank=True)
    
    # Social Links
    github = models.URLField(max_length=200, blank=True)
    linkedin = models.URLField(max_length=200, blank=True)
        

    # Add these inside class UserProfile:
    location = models.CharField(max_length=100, blank=True)
    twitter = models.URLField(max_length=200, blank=True)
    education = models.CharField(max_length=255, blank=True)
    work_experience = models.TextField(blank=True)
        
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
    
    total_submissions = models.IntegerField(default=0)
    profile_completed = models.BooleanField(default=False)
    class Meta:
        indexes = [
            models.Index(fields=["points"]),
        ]


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

    # For Debugging Questions (optional)
    code_snippet = models.TextField(blank=True, null=True)

    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)

    correct_option = models.CharField(
        max_length=1,
        choices=OPTION_CHOICES
    )

    explanation = models.TextField(blank=True)

    def is_debugging(self):
        return bool(self.code_snippet)

    def __str__(self):
        return self.question_text[:50]

class Quiz(models.Model):
    QUIZ_TYPE_CHOICES = [
        ("MCQ", "Simple MCQ"),
        ("DEBUG", "Debugging MCQ"),
    ]

    DIFFICULTY_CHOICES = [
        ("E", "Easy"),
        ("M", "Medium"),
        ("H", "Hard"),
    ]

    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="quizzes"
    )

    question = models.ForeignKey(
        "MCQ",
        on_delete=models.CASCADE,
        related_name="quizzes"
    )

    quiz_type = models.CharField(
        max_length=10,
        choices=QUIZ_TYPE_CHOICES,
        default="MCQ"
    )

    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES
    )

    def __str__(self):
        return f"{self.get_quiz_type_display()} | {self.question.question_text[:40]}"

class UserMCQAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)

    selected_option = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    attempts = models.PositiveIntegerField(default=0)  # this one is NEW guys
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'quiz')





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

    # starter code for code editor
    starter_code_java = models.TextField(blank=True)
    starter_code_python = models.TextField(blank=True)


    def __str__(self):
        return self.title
    
class DailySubmission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "date")


class ExampleTestCase(models.Model):
    problem = models.OneToOneField(
        Problem,
        on_delete=models.CASCADE,
        related_name="example"
    )
    input_data = models.TextField()
    output_data = models.TextField()
    explanation = models.TextField(blank=True)

    def __str__(self):
        return f"Example for {self.problem.title}"

class TestCase(models.Model):
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="testcases"
    )
    input_data = models.TextField()
    expected_output = models.TextField()
    is_sample = models.BooleanField(default=False)

    def __str__(self):
        return f"Testcase for {self.problem.title}"
    
    
class ExampleTestCase(models.Model):
    problem = models.OneToOneField(
        Problem,
        on_delete=models.CASCADE,
        related_name="example"
    )
    input_data = models.TextField()
    output_data = models.TextField()
    explanation = models.TextField(blank=True)

    def __str__(self):
        return f"Example for {self.problem.title}"

class TestCase(models.Model):
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="testcases"
    )
    input_data = models.TextField()
    expected_output = models.TextField()
    is_sample = models.BooleanField(default=False)

    def __str__(self):
        return f"Testcase for {self.problem.title}"
    
    
class ProblemSubmission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False)
    solved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "problem")