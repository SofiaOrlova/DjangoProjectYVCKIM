from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(
        _('email address'),
        unique=True,
    )

    email_verify = models.BooleanField(default=False)
    surname = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


class Instructor(models.Model):
    second_name = models.CharField(max_length=100)
    name=models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    user_id = models.CharField(max_length=10)

    def __str__(self):
        return self.second_name


class Appointment(models.Model):
    date = models.DateField()
    time = models.TimeField()
    is_available = models.BooleanField(default=True)
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE,null=True, blank=True)


class AvailableTime(models.Model):
    date = models.DateField()
    time = models.TimeField()
    instructor = models.ForeignKey(User, on_delete=models.CASCADE)

class Notation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    instructor_id = models.IntegerField()

class UserData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    passport_series = models.CharField(max_length=20)
    passport_number = models.CharField(max_length=20)
    registration = models.CharField(max_length=255)
    group_number = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.username