from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import Appointment

def send_reminder_emails():
    current_date = timezone.now().date()
    tomorrow = current_date + timedelta(days=1)
    
    tomorrow_appointments = Appointment.objects.filter(date=tomorrow)
    
    for appointment in tomorrow_appointments:
        if appointment.student.email:
            send_mail(
                'Напоминание о занятии',
                f'Завтра, {appointment.date}, в {appointment.time} у вас запланировано занятие с инструктором {appointment.instructor}.',
                'orlowa.sony@ya.ru',
                ['son020802@mail.ru'],
                fail_silently=False,
            )
