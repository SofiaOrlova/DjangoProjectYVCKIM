from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(
        _('email address'),
        unique=True,
    )

    email_verify = models.BooleanField(default=False)
    surname = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)

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
    passport_series = models.CharField(max_length=20,null=True)
    passport_number = models.CharField(max_length=20,null=True)
    group_number = models.CharField(max_length=20,null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    region = models.CharField(max_length=35,null=True)
    city_or_village = models.CharField(max_length=50,null=True)
    street = models.CharField(max_length=40,null=True)
    house = models.CharField(max_length=10,null=True)
    corps = models.CharField(max_length=5, null=True)
    apartment = models.CharField(max_length=10, null=True)
    place_of_birth= models.CharField(max_length=70, null=True)
    passport_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.username
    

class UserGroups(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    group_id = models.CharField(max_length=2,null=True)

class Payments(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_price = models.FloatField(default=20000.0)
    payment = models.FloatField(max_length=6,null= False)
    payment_date = models.DateField(default=timezone.now)

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

# user = models.OneToOneField(User, on_delete=models.CASCADE)
#     passport_series = models.CharField(max_length=20)
#     passport_number = models.CharField(max_length=20)
#     # registration = models.CharField(max_length=255)
#     group_number = models.CharField(max_length=20)
#     date_of_birth = models.DateField(null=True, blank=True)
#     region = models.CharField(max_length=35)
#     city_or_village = models.CharField(max_length=50)
#     street = models.CharField(max_length=40)
#     house = models.CharField(max_length=10)
#     corps = models.CharField(max_length=5)
#     apartment = models.CharField(max_length=10)