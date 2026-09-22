from django import forms
from .models import JobApplication

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = [
            'full_name',
            'email',
            'phone_number',
            'location',
            'cv_file',
            'cover_letter',
            'opt_in_future_vacancies',
            'opt_in_announcements_products',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white outline-none focus:ring-2 focus:ring-brand-orange-500', 'placeholder': 'John Doe'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white outline-none focus:ring-2 focus:ring-brand-orange-500', 'placeholder': 'applicant@email.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white outline-none focus:ring-2 focus:ring-brand-orange-500', 'placeholder': '+265 999 000 000'}),
            'location': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white outline-none focus:ring-2 focus:ring-brand-orange-500'}),
            'cv_file': forms.FileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:bg-brand-orange-50 file:text-brand-orange-700 hover:file:bg-brand-orange-100 dark:file:bg-gray-700 dark:file:text-gray-200'}),
            'cover_letter': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white outline-none focus:ring-2 focus:ring-brand-orange-500', 'placeholder': 'Brief summary of your experience...'}),
            'opt_in_future_vacancies': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-brand-orange-500 rounded border-gray-300 focus:ring-brand-orange-500'}),
            'opt_in_announcements_products': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-brand-orange-500 rounded border-gray-300 focus:ring-brand-orange-500'}),
        }