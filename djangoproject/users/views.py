from django.contrib.auth import authenticate, login, get_user_model
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.utils.http import urlsafe_base64_decode
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.contrib.auth.views import LoginView
from users.forms import UserCreationForm, AuthenticationForm, UserDataForm
from django.contrib.auth.decorators import login_required
from users.utils import send_email_for_verify
from django import forms
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from datetime import time
from datetime import datetime
import json
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import Instructor
from .models import Appointment, Instructor, Notation, UserData
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
            return redirect('manager_dashboard/')
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


@csrf_exempt
@require_POST
def delete_event(request):
    try:
        data = json.loads(request.body)
        event_id = data.get('event_id')

        if event_id is not None:
            # Ищем событие по ID и удаляем его из базы данных
            appointment = Appointment.objects.get(id=event_id)
            appointment.delete()

            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'ID события не указан.'})

    except json.JSONDecodeError as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    

def teacher_notation(request):
    # Получаем текущего пользователя
    current_user = request.user

    # Находим записи в таблице Notation, где текущий пользователь является инструктором
    notations = Notation.objects.filter(instructor_id=current_user.id)

    # Получаем ID пользователей из записей в таблице Notation
    user_ids = notations.values_list('user_id', flat=True)

    # Получаем данные пользователей из таблицы UserProfile
    users_sorted = User.objects.filter(id__in=user_ids)


    user_id_current = request.user.id 
    instructor = Instructor.objects.get(user_id=user_id_current)
    instructor_id = instructor.id


    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            time = request.POST.get('time')

            existing_appointment = Appointment.objects.filter(date=date, time=time, instructor=instructor_id).first()
            if existing_appointment:
                    return render(request, 'teacher_notation.html', {'form': form, 'error_message': 'Время уже занято.'})
            else:
                # Присвоение инструктора к записи перед сохранением
                appointment = form.save(commit=False)
                appointment.instructor = instructor
                appointment.is_available = False
                appointment.time = time
                # Извлечение выбранного пользователя из radio button
                selected_user_id = request.POST.get('user_radio')
                selected_user = User.objects.get(id=selected_user_id)
                # Присвоение выбранного пользователя к записи перед сохранением
                appointment.student = selected_user
                appointment.save()
                context = {'appointments': appointment}
                return render(request, 'success_url.html', context)
    else:
        form = AppointmentForm()

        date = form['date'].value()
        existing_appointments = Appointment.objects.filter(date=date)
        occupied_times = [appointment.time for appointment in existing_appointments if not appointment.is_available]
        available_times_filtered = [t for t in available_times if t not in occupied_times]

        time_choices = [(t.strftime('%H:%M'), t.strftime('%H:%M')) for t in available_times_filtered]
        form.fields['time'] = forms.ChoiceField(choices=time_choices)

    context = {'users': users_sorted, 'form': form}

    return render(request, 'teacher_notation.html', context)


def manager_dashboard(request):
    users = User.objects.filter(email_verify=0) 
    return render(request, 'manager_dashboard.html', {'users': users})

@require_POST
def confirm_users(request):
    user_ids = request.POST.getlist('user_ids')  # Получаем список выбранных пользователей
    User.objects.filter(id__in=user_ids).update(email_verify=1)  # Обновляем поле email_verify для выбранных пользователей

    response_data = {'reload_page': True}
    return JsonResponse(response_data)


def manager_add_users_data(request):
    users = User.objects.filter(email_verify=1) 
    return render(request, 'manager_add_users_data.html', {'users': users})


# def add_user_data(request, user_id):
#     user = User.objects.get(id=user_id)

#     if request.method == 'POST':
#         form = UserDataForm(request.POST)
#         if form.is_valid():
#             user_data = form.save(commit=False)
#             user_data.user = user
#             user_data.save()
#             return redirect('manager_add_users_data')
#     else:
#         form = UserDataForm()

#     return render(request, 'add_user_data.html', {'user': user, 'form': form})

def add_user_data(request, user_id):
    user = User.objects.get(id=user_id)
    user_data, created = UserData.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = UserDataForm(request.POST, instance=user_data)
        if form.is_valid():
            form.save()
            return redirect('manager_add_users_data')
    else:
        form = UserDataForm(instance=user_data)

    return render(request, 'add_user_data.html', {'user': user, 'form': form})

