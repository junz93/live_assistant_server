from django.db import models
from django.forms import ModelForm

# Create your models here.
class Character(models.Model):
    MALE = 'M'
    FEMALE = 'F'
    GENDER_CHOICES = [
        (MALE, 'Male'),
        (FEMALE, 'Female'),
    ]

    TYPE_CHOICES = [
        ('SALE', 'Sale'),
        ('PERFORMANCE', 'Performance'),
    ]

    EDUCATION_CHOICES = [
        ('DOCTOR', 'Doctor'),                       # 博士
        ('MASTER', 'Master'),                       # 硕士
        ('BACHELOR', 'Bachelor'),                   # 本科（学士）
        ('JUNIOR_COLLEGE', 'Junior College'),       # 大专
        ('HIGH_SCHOOL', 'High School'),             # 高中
        ('VOCATIONAL_SCHOOL', 'Vocational School'), # 中专
        ('OTHER', 'Other'),                         # 其他
    ]

    # id = models.AutoField(primary_key=True)
    # user_id = models.ForeignKey()
    name = models.CharField(max_length=20)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    subject = models.CharField(max_length=100)
    created_datetime = models.DateTimeField(auto_now_add=True, editable=False)
    updated_datetime = models.DateTimeField(auto_now=True, editable=False)
    birth_date = models.DateField(null=True, blank=True)
    education = models.CharField(max_length=30, choices=EDUCATION_CHOICES, null=True, blank=True)
    marital_status = models.CharField(max_length=20, null=True, blank=True)
    personality = models.CharField(max_length=30, null=True, blank=True)
    habit = models.CharField(max_length=50, null=True, blank=True)
    hobby = models.CharField(max_length=50, null=True, blank=True)
    advantage = models.CharField(max_length=50, null=True, blank=True)
    speaking_style = models.CharField(max_length=50, null=True, blank=True)
    audience_type = models.CharField(max_length=30, null=True, blank=True)
    worldview = models.TextField(max_length=400, null=True, blank=True)
    personal_statement = models.TextField(max_length=400, null=True, blank=True)

class CharacterForm(ModelForm):
    class Meta:
        model = Character
        fields = '__all__'
        # exclude = []
