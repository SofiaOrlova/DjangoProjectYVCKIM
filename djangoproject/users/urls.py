from django.urls import path, include
from django.views.generic import TemplateView

from users.views import Register, EmailVerify, MyLoginView, indexInstructor, student_dashboard, user_profile, schedule, teacher_dashboard, delete_event, teacher_notation, manager_dashboard, confirm_users, manager_add_users_data, add_user_data, payments, profile, generate_group_journal, manager_document_dogovor, user_dogovor, generate_hour_group, kniga_vojden_users, kniga_vojden
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

    # path('reset/done/', reset_done, name='reset_done'),
    # path('reset/done/', PasswordResetView.as_view(), name='reset_password'),
    # path('accounts/login/', MyLoginView.as_view(), name='login'),

    path('user_profile/', user_profile, name='user_profile'),
    path('user_profile/teacher_dashboard/', teacher_dashboard),
    path('user_profile/teacher_notation/', teacher_notation),
    path('user_profile/teacher_dashboard/delete_event/', delete_event, name='delete_event'),
   # path('student_dashboard/', TemplateView.as_view(template_name='student_dashboard.html'), name='student_dashboard'),
    path('user_profile/student_dashboard/', student_dashboard),
    path('user_profile/payments/', payments),
    path('user_profile/profile/', profile),
    path('user_profile/schedule/', schedule),
    # path('student_dashboard/<int:idInstructor>/', views.appointment, name='appointment'),
    path('student_dashboard/<int:idInstructor>/', views.indexInstructor, name='index_instructor'),
    path('student_dashboard/<int:idInstructor>/appointment', views.appointment, name='appointment'),
    path('user_profile/manager_dashboard/', manager_dashboard),
    path('user_profile/manager_dashboard/confirm_users/', confirm_users, name='confirm_users'),
    path('user_profile/manager_add_users_data/', manager_add_users_data, name='manager_add_users_data'),
    path('user_profile/manager_add_users_data/add_data/<int:user_id>/', add_user_data, name='add_user_data'),
    path('user_profile/manager_documents/', TemplateView.as_view(template_name='manager_documents.html'), name='manager_documents'),
    path('user_profile/manager_document_dogovor/', manager_document_dogovor, name='manager_document_dogovor'),
    path('user_profile/manager_document_dogovor/user_dogovor/<int:user_id>/', user_dogovor, name='user_dogovor'),
    path('user_profile/manager_document_group/', TemplateView.as_view(template_name='manager_document_group.html'), name='manager_document_group'),
    path('user_profile/manager_document_kniga_vojden/', kniga_vojden, name='kniga_vojden'),
    path('user_profile/manager_document_instructor/', TemplateView.as_view(template_name='manager_document_instructor.html'), name='manager_document_instructor'),
    path('get_available_times/', views.get_available_times, name='get_available_times'),
    path('user_profile/manager_documents/generate_group_journal', views.generate_group_journal, name='generate_group_journal'),
    path('user_profile/manager_documents/generate_hour_group', views.generate_hour_group, name='generate_hour_group'),
    path('user_profile/manager_document_kniga_vojden/kniga_vojden_users', kniga_vojden_users, name='kniga_vojden_users'),
]