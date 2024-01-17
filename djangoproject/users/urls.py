from django.urls import path, include
from django.views.generic import TemplateView

from users.views import Register, EmailVerify, MyLoginView,indexInstructor, student_dashboard, user_profile, schedule, teacher_dashboard
from . import views

urlpatterns = [

    path('login/', MyLoginView.as_view(), name='login'),

    path('', include('django.contrib.auth.urls')),

    path('invalid_verify/', TemplateView.as_view(template_name='registration/invalid_verify.html'),
         name='invalid_verify'
         ),

    path(
        'verify_email/<uidb64>/<token>/',
        EmailVerify.as_view(),
        name='verify_email',
    ),

    path('confirm_email/', 
        TemplateView.as_view(template_name='registration/confirm_email.html'), 
        name='confirm_email'
    ),
    
    path('register/', Register.as_view(), name='register'),

    path('user_profile/', user_profile, name='user_profile'),
    path('user_profile/teacher_dashboard/', teacher_dashboard),
   # path('student_dashboard/', TemplateView.as_view(template_name='student_dashboard.html'), name='student_dashboard'),
    path('user_profile/student_dashboard/', student_dashboard),
    path('user_profile/schedule/', schedule),
    # path('student_dashboard/<int:idInstructor>/', views.appointment, name='appointment'),
    path('student_dashboard/<int:idInstructor>/', views.indexInstructor, name='index_instructor'),
    path('student_dashboard/<int:idInstructor>/appointment', views.appointment, name='appointment'),
    path('manager_dashboard/', TemplateView.as_view(template_name='manager_dashboard.html'), name='manager_dashboard'),
    path('get_available_times/', views.get_available_times, name='get_available_times'),
    # path('student_dashboard/<int:idInstructor>/appointment/get_available_times/', views.get_available_times, name='get_available_times'),
    # path('api/create_appointment/', views.create_appointment_api, name='create_appointment_api'),
    # path('success_url/', views.success_url, name='success_url'),
]