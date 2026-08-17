from django.contrib import admin

from .models import Food, FoodLog, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'age', 'weight_kg', 'height_cm',
        'fitness_goal', 'bmi', 'calorie_target', 'created_at',
    )
    list_filter = ('fitness_goal', 'dietary_preference', 'activity_level')
    readonly_fields = ('bmi', 'bmi_category', 'bmr', 'daily_calories', 'calorie_target')


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'serving_size', 'calories', 'protein',
        'carbohydrates', 'fat', 'dietary_type',
    )
    list_filter = ('dietary_type',)
    search_fields = ('name',)


@admin.register(FoodLog)
class FoodLogAdmin(admin.ModelAdmin):
    list_display = ('profile', 'food', 'meal_type', 'quantity', 'date', 'created_at')
    list_filter = ('meal_type', 'date')
    search_fields = ('food__name',)
