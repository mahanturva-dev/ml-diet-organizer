from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('planner/', views.planner, name='planner'),
    path('result/<int:profile_id>/', views.result, name='result'),
    path('food/', views.food_tracker, name='food_tracker'),
    path('food/delete/<int:log_id>/', views.delete_food_log, name='delete_food_log'),
    path('food/add-custom/', views.add_custom_food, name='add_custom_food'),
    path('food/quick-add/<int:food_id>/', views.quick_add_food, name='quick_add_food'),
    path('water/update/', views.update_water_log, name='update_water_log'),
    path('food/toggle-vrat/', views.toggle_vrat_mode, name='toggle_vrat_mode'),
    path('food/apply-plan/', views.apply_meal_plan, name='apply_meal_plan'),
    path('exercise/add/', views.add_exercise_log, name='add_exercise_log'),
    path('exercise/delete/<int:log_id>/', views.delete_exercise_log, name='delete_exercise_log'),
    path('weight/add/', views.add_weight_log, name='add_weight_log'),
    path('fasting/toggle/', views.toggle_fasting, name='toggle_fasting'),
]
