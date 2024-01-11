from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(
        _('email address'),
        unique=True,
    )

    email_verify = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


class Instructor(models.Model):
    second_name = models.CharField(max_length=100)
    name=models.CharField(max_length=100)
    surname = models.CharField(max_length=100)

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