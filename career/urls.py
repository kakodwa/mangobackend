from django.urls import path
from . import views

app_name = 'careers'

urlpatterns = [
    path('vacancy/', views.vacancy_list, name='vacancy_list'),
    path('vacancy/<slug:slug>/', views.vacancy_detail, name='vacancy_detail'),       # 👈 Shareable Detail Link
    path('apply/', views.apply_vacancy, name='apply_general'),
    path('apply/<slug:slug>/', views.apply_vacancy, name='apply_vacancy'),
    path('success/', views.application_success, name='application_success'),
]