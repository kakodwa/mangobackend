from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from .models import Vacancy
from .forms import JobApplicationForm

# 1. Vacancy List View
def vacancy_list(request):
    vacancies = Vacancy.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'careers/list.html', {'vacancies': vacancies})


# 2. Vacancy Detail Page View (Shareable Link)
def vacancy_detail(request, slug):
    vacancy = get_object_or_404(Vacancy, slug=slug, is_active=True)
    
    # Split responsibilities and qualifications by line breaks for clean rendering
    responsibilities_list = [r.strip() for r in vacancy.responsibilities.split('\n') if r.strip()]
    qualifications_list = [q.strip() for q in vacancy.qualifications.split('\n') if q.strip()]

    return render(request, 'careers/detail.html', {
        'vacancy': vacancy,
        'responsibilities_list': responsibilities_list,
        'qualifications_list': qualifications_list,
    })


# 3. Application View for a specific Vacancy
def apply_vacancy(request, slug=None):
    vacancy = None
    if slug:
        vacancy = get_object_or_404(Vacancy, slug=slug, is_active=True)

    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            if vacancy:
                application.vacancy = vacancy
            application.save()

            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'MalaTrade Careers <support@malatrade.com>')
            position_title = vacancy.title if vacancy else "MalaTrade Team Role"

            # Send Notification Email to HR
            try:
                send_mail(
                    subject=f"New Application: {application.full_name} - {position_title}",
                    message=(
                        f"Position: {position_title}\n"
                        f"Name: {application.full_name}\n"
                        f"Email: {application.email}\n"
                        f"Phone: {application.phone_number}\n"
                        f"Location: {application.location}\n\n"
                        f"Future Vacancy Opt-in: {'Yes' if application.opt_in_future_vacancies else 'No'}\n"
                        f"Products Opt-in: {'Yes' if application.opt_in_announcements_products else 'No'}\n"
                    ),
                    from_email=from_email,
                    recipient_list=['career@malatrade.com'], # From poster[cite: 2]
                    fail_silently=True,
                )
            except Exception:
                pass

            # Send Confirmation Email to Applicant
            try:
                send_mail(
                    subject=f"Application Received: {position_title} - MalaTrade",
                    message=(
                        f"Dear {application.full_name},\n\n"
                        f"Thank you for applying for the {position_title} role at MalaTrade!\n\n"
                        f"We have received your application and CV. Our recruitment team will review your qualifications and reach out soon.\n\n"
                        f"Best regards,\n"
                        f"MalaTrade Recruitment Team\n"
                        f"https://www.malatrade.com"
                    ),
                    from_email=from_email,
                    recipient_list=[application.email],
                    fail_silently=True,
                )
            except Exception:
                pass

            return redirect('careers:application_success')
    else:
        form = JobApplicationForm()

    return render(request, 'careers/apply.html', {'form': form, 'vacancy': vacancy})


# 4. Application Success View
def application_success(request):
    return render(request, 'careers/success.html')