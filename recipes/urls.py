from django.urls import path
from . import views

app_name = 'recipes'

urlpatterns = [
    path('', views.generate_safe_recipe, name='generate_safe_recipe'),
]
