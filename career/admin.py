from django.contrib import admin
from .models import Vacancy, JobApplication

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'locations', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 
        'get_vacancy_title', 
        'location', 
        'phone_number', 
        'opt_in_future_vacancies', 
        'opt_in_announcements_products', 
        'submitted_at'
    )
    list_filter = (
        'vacancy',
        'location', 
        'opt_in_future_vacancies', 
        'opt_in_announcements_products', 
        'submitted_at'
    )
    search_fields = ('full_name', 'email', 'phone_number')

    @admin.display(description='Vacancy')
    def get_vacancy_title(self, obj):
        return obj.vacancy.title if obj.vacancy else 'General'