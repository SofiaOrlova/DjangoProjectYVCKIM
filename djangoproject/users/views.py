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

from .models import Instructor

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
            return redirect('teacher_dashboard')
        elif request.user.groups.filter(name='Ученик').exists():
            return redirect('student_dashboard/')
        elif request.user.groups.filter(name='Менеджер').exists():
            return redirect('manager_dashboard')
    else:
        return redirect('login')  # Пользователь не вошел в систему
    

def student_dashboard(request):
    items = Instructor.objects.all()
    context = {
        'items':items
    }
    return render(request, "student_dashboard.html", context)

def indexInstructor(request, idInstructor):
    item = Instructor.objects.get(id=idInstructor)
    context = {
        'item':item
    }
    return render(request, "student_pickDataTime.html", context)