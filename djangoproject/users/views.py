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
from docxtpl import DocxTemplate
from django.http import FileResponse
from io import BytesIO
import io
from docx import Document
import os
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

from .models import Instructor
from .models import Appointment, Instructor, Notation, UserData, UserGroups
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
    user_ids = request.POST.getlist('user_ids')  
    users = User.objects.filter(id__in=user_ids)

    # Получаем список id пользователей до обновления
    user_ids_before_update = list(users.values_list('id', flat=True))

    # Обновляем email_verify для выбранных пользователей
    users.update(email_verify=1)  

    # Создаем записи в модели UserGroups
    user_groups_to_create = [
        UserGroups(user_id=user, group_id=2)
        for user in users
    ]
    UserGroups.objects.bulk_create(user_groups_to_create)

    response_data = {'reload_page': True}
    return JsonResponse(response_data)


def manager_add_users_data(request):
    users = User.objects.filter(email_verify=1) 
    return render(request, 'manager_add_users_data.html', {'users': users})


def add_user_data(request, user_id):
    user = User.objects.get(id=user_id)
    user_data, created = UserData.objects.get_or_create(user=user)

    formatted_date = user_data.date_of_birth.strftime('%Y-%m-%d') if user_data.date_of_birth else None

    if request.method == 'POST':
        form = UserDataForm(request.POST, instance=user_data)
        if form.is_valid():
            form.save()
            return redirect('manager_add_users_data')
    else:
        form = UserDataForm(instance=user_data)

    return render(request, 'add_user_data.html', {'user': user, 'form': form, 'formatted_date': formatted_date})


def payments(request):
    # users = User.objects.filter(email_verify=0) 
    return render(request, 'student_payments.html')

def profile(request):
    return render(request, 'student_profile.html')


def generate_group_journal(request):
    if request.method == 'POST':
        group_number = request.POST.get('group_number')
        
        # Получение всех данных пользователей из модели UserData по указанной группе
        user_data_list = UserData.objects.filter(group_number=group_number)

        if user_data_list:
            # Путь к пустому шаблону документа
            template_path = "group_journal.docx"

            # Создаем новый документ на основе пустого шаблона
            doc = Document(template_path)

            # Функция для установки шрифта и размера текста в ячейке
            def set_font_and_size(cell):
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = 'Arial CYR'
                        run.font.size = Pt(10)
                        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                        paragraph.paragraph_format.space_after = Pt(0)
            def set_font_and_size_without_center(cell):
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = 'Arial CYR'
                        run.font.size = Pt(10)
                        paragraph.paragraph_format.space_after = Pt(0)
            
            # Заполняем таблицу данными из базы данных
            for i, user_data in enumerate(user_data_list):
                user = user_data.user
                context = {
                    'last_name': user.last_name if user.last_name else '',
                    'first_name': user.first_name if user.first_name else '',
                    'surname': user.surname if user.surname else '',
                    'date_of_birth': user_data.date_of_birth.strftime('%d.%m.%Y') if user_data.date_of_birth else '',
                    'region': user_data.region if user_data.region else '',
                    'city_or_village': user_data.city_or_village if user_data.city_or_village else '',
                    'street': user_data.street if user_data.street else '',
                    'house': user_data.house if user_data.house else '',
                    'corps': user_data.corps if user_data.corps else '',
                    'apartment': user_data.apartment if user_data.apartment else '',
                }
                
                # Записываем данные в существующие строки таблицы
                row = doc.tables[0].rows[i + 1].cells  # Индекс строки в таблице начинается с 1, а не с 0
                # row[0].text = str(i + 1)  # Номер строки
                row[1].text = context['last_name']  
                set_font_and_size(row[1])
                row[2].text = context['first_name']  
                set_font_and_size(row[2])
                row[3].text = context['surname']  
                set_font_and_size(row[3])
                row[4].text = context['date_of_birth']  
                set_font_and_size(row[4])

                row_table2 = doc.tables[1].rows[i + 2].cells
                row_table2[0].text = context['region']
                set_font_and_size(row_table2[0])
                row_table2[1].text = context['city_or_village'] 
                set_font_and_size(row_table2[1])   
                row_table2[2].text = context['street']
                set_font_and_size(row_table2[2])
                row_table2[3].text = context['house'] 
                set_font_and_size(row_table2[3])
                row_table2[4].text = context['corps']  
                set_font_and_size(row_table2[4])
                row_table2[5].text = context['apartment']
                set_font_and_size(row_table2[5])

                row_table3 = doc.tables[2].rows[i+3].cells
                if(i>0):
                    row_table3 = doc.tables[2].rows[i+2].cells
                    row_table3[0-i].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table3[0-i])
                else:
                    row_table3[0].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table3[0])

                row_table4 = doc.tables[4].rows[i+3].cells
                if(i>0):
                    row_table4 = doc.tables[4].rows[i+2].cells
                    row_table4[0-i].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table4[0-i])
                else:
                    row_table4[0].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table4[0])

                row_table5 = doc.tables[6].rows[i+3].cells
                row_table5[1].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                set_font_and_size_without_center(row_table5[1])

                row_table6 = doc.tables[8].rows[i+3].cells
                row_table6[1].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                set_font_and_size_without_center(row_table6[1])

                # row_table7 = doc.tables[10].rows[i+3].cells
                # row_table7[1].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                # set_font_and_size_without_center(row_table7[1])
                
                if(i>0):
                    row_table7 = doc.tables[10].rows[i+2].cells
                    row_table7[0-i].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table7[0-i])
                else:
                    row_table7 = doc.tables[10].rows[i+3].cells
                    row_table7[0-i].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table7[0-i])

                # row_table8 = doc.tables[12].rows[i+3].cells
                # row_table8[1].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                # set_font_and_size_without_center(row_table8[1])
                if(i>0):
                    row_table8 = doc.tables[12].rows[i+2].cells
                    row_table8[0-i].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table8[0-i])
                else:
                    row_table8 = doc.tables[12].rows[i+3].cells
                    row_table8[0-i].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table8[0-i])

                # # row_table9 = doc.tables[14].rows[i+3].cells
                # # row_table9[1].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                # # set_font_and_size_without_center(row_table9[1])
                if(i>0):
                    row_table9 = doc.tables[14].rows[i+2].cells
                    row_table9[0-i].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table9[0-i])
                else:
                    row_table9 = doc.tables[14].rows[i+3].cells
                    row_table9[0-i].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table9[0-i])

                # # row_table10 = doc.tables[16].rows[i+3].cells
                # # row_table10[1].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                # # set_font_and_size_without_center(row_table10[1])
                if(i>0):
                    row_table10 = doc.tables[16].rows[i+2].cells
                    row_table10[0-i].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table10[0-i])
                else:
                    row_table10 = doc.tables[16].rows[i+3].cells
                    row_table10[0-i].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table10[0-i])

                # # row_table11 = doc.tables[18].rows[i+3].cells
                # # row_table11[1].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                # # set_font_and_size_without_center(row_table11[1])
                if(i>0):
                    row_table11 = doc.tables[18].rows[i+2].cells
                    row_table11[0-i].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table11[0-i])
                else:
                    row_table11 = doc.tables[18].rows[i+3].cells
                    row_table11[0-i].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                    set_font_and_size_without_center(row_table11[0-i])

                row_table12 = doc.tables[20].rows[i+1].cells
                row_table12[1].text = context['last_name'] + ' '+ context['first_name'][0] + '. ' + context['surname'][0] + '. '
                set_font_and_size_without_center(row_table12[1])
            
            for p in doc.paragraphs:
                if "{{group_number}}" in p.text:
                    p.text = p.text.replace("{{group_number}}", group_number)
                    for run in p.runs:
                        run.font.name = 'Times New Roman'
                        run.font.bold = True
                        run.font.size = Pt(36)
                    break 

            
            output_path = "filled_group_journal.docx"
            doc.save(output_path)

            # Отправляем заполненный документ в ответе на запрос
            with open(output_path, 'rb') as docx_file:
                response = HttpResponse(docx_file.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                response['Content-Disposition'] = f'attachment; filename=filled_group_journal.docx'
                return response
                
        else:
            return HttpResponse("Пользователи с указанной группой не найдены")

    return render(request, 'manager_documents.html')

def manager_document_dogovor(request):
    users = User.objects.filter(email_verify=1) & User.objects.filter(usergroups__group_id=2)
    return render(request, 'manager_document_dogovor.html', {'users': users})

def generate_docx(user):
    # Загрузка шаблона docx документа
    doc = Document('dogovor_ob_obych_В.docx')

    user_data = user.userdata
    
    # Заполнение меток данными ученика
    for paragraph in doc.paragraphs:
        if "{{last_name}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{last_name}}", user.last_name)
        if "{{first_name}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{first_name}}", user.first_name)
        if "{{surname}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{surname}}", user.surname)
        if "{{date_of_birth}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{date_of_birth}}", str(user_data.date_of_birth.day))
        if "{{month_of_birth}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{month_of_birth}}", str(user_data.date_of_birth.month))
        if "{{year_of_birth}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{year_of_birth}}", str(user_data.date_of_birth.year))
        if "{{place_of_birth}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{place_of_birth}}", str(user_data.place_of_birth))
        if "{{passport_series}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{passport_series}}", str(user_data.passport_series))
        if "{{passport_number}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{passport_number}}", str(user_data.passport_number))
    
    # Создание временного буфера для сохранения документа
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    return buffer

def user_dogovor(request, user_id):
    print(user_id)
    user = get_object_or_404(User, id=user_id)
    
    # Создание и заполнение docx документа
    docx_buffer = generate_docx(user)
    
    # Отправка документа пользователю для скачивания
    response = HttpResponse(docx_buffer.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = 'attachment; filename="document.docx"'
    
    return response

# def user_dogovor(request, user_id):
#     if request.method == 'POST':
#         # Обработка POST-запроса для генерации и отправки документа
#         user_id = request.POST.get('user_id')
#         if user_id:
#             try:
#                 user = User.objects.get(id=user_id)
#                 doc = Document('dogovor_ob_obych_В.docx')

#                 # Заполнение меток в документе
#                 for paragraph in doc.paragraphs:
#                     if 'last_name' in paragraph.text:
#                         paragraph.text = paragraph.text.replace('last_name', user.last_name)
#                     if 'first_name' in paragraph.text:
#                         paragraph.text = paragraph.text.replace('first_name', user.first_name)
#                     if 'surname' in paragraph.text:
#                         paragraph.text = paragraph.text.replace('surname', user.surname)

#                 # Генерация HTTP-ответа с содержимым документа
#                 response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
#                 response['Content-Disposition'] = 'attachment; filename="договор_об_обучении.docx"'
#                 doc.save(response)
#                 return response
#             except User.DoesNotExist:
#                 return JsonResponse({'error': 'Пользователь с указанным ID не найден'}, status=404)
#         else:
#             return JsonResponse({'error': 'Не указан ID пользователя'}, status=400)
#     else:
#         # Если запрос не POST, вернуть ошибку метода неразрешенного доступа
#         return JsonResponse({'error': 'Метод не разрешен'}, status=405)
