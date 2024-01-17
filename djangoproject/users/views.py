from django.contrib.auth import authenticate, login, get_user_model
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.utils.http import urlsafe_base64_decode
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.contrib.auth.views import LoginView
from users.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from users.utils import send_email_for_verify
from django import forms
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from datetime import time
from datetime import datetime
import json

from .models import Instructor
from .models import Appointment, Instructor
from .forms import AppointmentForm
from django.shortcuts import get_object_or_404


User = get_user_model()

class MyLoginView(LoginView):
    form_class = AuthenticationForm

class EmailVerify(View):
    
    def get(self, request, uidb64, token):
        user = self.get_user(uidb64)

        if user is not None and token_generator.check_token(user, token):
            user.email_verify = True
            user.save()
            login(request, user)

            # Проверьте роль пользователя и перенаправьте на соответствующую страницу личного кабинета
            if user.groups.filter(name='Преподаватель').exists():
                return redirect('teacher_dashboard')
            elif user.groups.filter(name='Ученик').exists():
                return redirect('student_dashboard')
           # else user.groups.filter(name='Менеджер').exists():
            if user.groups.filter(name='Менеджер').exists():
                return redirect('manager_dashboard')
            #else:
                #return redirect('invalid_role')  # Обработка случая, если у пользователя нет роли
            #return redirect('home')
        return redirect('invalid_verify')

    @staticmethod
    def get_user(uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError,
                User.DoesNotExist, ValidationError):
            user = None
        return user


class Register(View):

    template_name = 'registration/register.html'

    def get(self, request):
        context = {
            'form': UserCreationForm()
        }
        return render(request, self.template_name, context)

    def post(self, request):
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            user = authenticate(email=email, password=password)
            send_email_for_verify(request, user)
            return redirect('confirm_email')
        context = {
            'form': form 
        }
        return render(request, self.template_name, context)
    

def user_profile(request):
    if request.user.is_authenticated:
        # Проверьте принадлежность пользователя к группам и перенаправьте на соответствующую страницу
        if request.user.groups.filter(name='Преподаватель').exists():
            return redirect('teacher_dashboard/')
        elif request.user.groups.filter(name='Ученик').exists():
            return redirect('student_dashboard/')
        elif request.user.groups.filter(name='Менеджер').exists():
            return redirect('manager_dashboard')
    else:
        return redirect('login')  # Пользователь не вошел в систему
    

def student_dashboard(request):
    items = Instructor.objects.all()
    appointments = Appointment.objects.filter(date__gte=datetime.now().date())
    
    appointments_data = []
    for appointment in appointments:
        appointments_data.append({
            'id': appointment.id,
            'date': appointment.date.strftime('%d'),
            'time': appointment.time.strftime('%H:%M:%S'),
            # 'instructor': f"{appointment.instructor.second_name} {appointment.instructor.name} {appointment.instructor.surname}",
            'instructor': appointment.instructor.id,
        })

    appointments_json = json.dumps(appointments_data)
    context = {
        'items':items,
        'appointments':appointments_json
    }
    return render(request, "student_dashboard.html", context)

def student_pickDataTime(request):
    items = Instructor.objects.all()
    context = {
        'items':items
    }
    return render(request, "student_pickDataTime.html", context)

#Это робит--------------------
def indexInstructor(request, idInstructor):
    # Получение объекта инструктора по id
    item = Instructor.objects.get(id=idInstructor)
    
    return redirect('appointment', idInstructor=idInstructor)


available_times = [
    time(8, 0),
    time(9, 30),
    time(11, 0),
    time(13, 30),
    time(15, 0),
    time(16, 30),
]

def appointment(request, idInstructor):
    instructor = get_object_or_404(Instructor, pk=idInstructor)

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            time = request.POST.get('time')

            existing_appointment = Appointment.objects.filter(date=date, time=time, instructor=instructor).first()
            if existing_appointment:
                # if existing_appointment.is_available:
                #     existing_appointment.is_available = False
                #     existing_appointment.student = request.user
                #     existing_appointment.save()
                #     return redirect('success_url')
                # else:
                    return render(request, 'student_pickDataTime.html', {'form': form, 'error_message': 'Время уже занято.'})
            else:
                # Присвоение инструктора к записи перед сохранением
                appointment = form.save(commit=False)
                appointment.instructor = instructor
                appointment.is_available = False
                appointment.time = time
                appointment.student = request.user
                appointment.save()
                context = {'appointments': appointment}
                return render(request, 'success_url.html', context)
                # return redirect('success_url')
    else:
        form = AppointmentForm()

        date = form['date'].value()
        existing_appointments = Appointment.objects.filter(date=date)
        occupied_times = [appointment.time for appointment in existing_appointments if not appointment.is_available]
        available_times_filtered = [t for t in available_times if t not in occupied_times]

        time_choices = [(t.strftime('%H:%M'), t.strftime('%H:%M')) for t in available_times_filtered]
        form.fields['time'] = forms.ChoiceField(choices=time_choices)

    return render(request, 'student_pickDataTime.html', {'form': form})


# def success_url(request):
#     return render(request, 'success_url.html')


def get_available_times(request):
    selected_date = request.GET.get("date")
    instructor_id = request.GET.get("instructor_id")
    
    # Фильтруйте доступное время на основе выбранной даты
    existing_appointments = Appointment.objects.filter(date=selected_date, instructor_id=instructor_id)
    occupied_times = [appointment.time.strftime('%H:%M') for appointment in existing_appointments if not appointment.is_available]

    
    available_times = ["08:00", "09:30", "11:00", "13:30", "15:00", "16:30"]
    
    # Уберите недоступное (занятое) время из доступного времени
    available_times = [time for time in available_times if time not in occupied_times]
    
    return JsonResponse(available_times, safe=False)

def schedule(request):
    user_id = request.user.id  # Получаем id текущего пользователя
    appointments = Appointment.objects.filter(student_id=user_id)
    
    # Остальной код остается без изменений
    appointments_data = []
    for appointment in appointments:
        appointments_data.append({
            'id': appointment.id,
            'date': appointment.date.strftime('%Y-%m-%d'),
            'time': appointment.time.strftime('%H:%M:%S'),
            'instructor': f"{appointment.instructor.second_name} {appointment.instructor.name} {appointment.instructor.surname}",
        })

    appointments_json = json.dumps(appointments_data)

    context = {'appointments_json': appointments_json, 'user_id': user_id}
    return render(request, 'schedule.html', context)

    
def teacher_dashboard(request):
    # instructor_id = request.user.instructor.id  # Получаем id текущего инструктора
    user_id = request.user.id 
    instructor = Instructor.objects.get(user_id=user_id)
    instructor_id = instructor.id
    
    appointments = Appointment.objects.filter(instructor_id=instructor_id)
    
    # Остальной код остается без изменений
    appointments_data = []
    for appointment in appointments:
        appointments_data.append({
            'id': appointment.id,
            'date': appointment.date.strftime('%Y-%m-%d'),
            'time': appointment.time.strftime('%H:%M:%S'),
            'student': f"{appointment.student.first_name} {appointment.student.last_name}",
        })

    appointments_json = json.dumps(appointments_data)

    context = {'appointments_json': appointments_json, 'user_id': instructor_id}
    return render(request, 'teacher_dashboard.html', context)
