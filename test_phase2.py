"""Phase 2 integration tests for food tracking."""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diet_organizer.settings')

import django

django.setup()

from django.test import Client
from django.utils import timezone

from dietapp.calculations import aggregate_food_logs, meal_breakdown
from dietapp.models import Food, FoodLog, UserProfile


def test_food_log_nutrition():
    profile = UserProfile.objects.create(
        age=22, height_cm=170, weight_kg=65,
        activity_level='moderate', fitness_goal='maintain',
        dietary_preference='vegetarian',
        bmi=22.5, bmi_category='Normal weight',
        bmr=1500, daily_calories=2300, calorie_target=2300,
    )
    food = Food.objects.get(name='Roti (Whole Wheat)')
    log = FoodLog.objects.create(
        profile=profile, food=food,
        meal_type='breakfast', quantity=2, date=timezone.localdate(),
    )
    assert log.total_calories == 140.0
    assert log.total_protein == 5.0

    logs = FoodLog.objects.filter(profile=profile, date=timezone.localdate())
    totals = aggregate_food_logs(logs)
    assert totals['calories'] == 140.0
    meals = meal_breakdown(logs)
    assert meals['breakfast'] == 140.0
    log.delete()
    profile.delete()
    print('Nutrition calculation test passed.')


def test_session_isolation():
    p1 = UserProfile.objects.create(
        age=20, height_cm=165, weight_kg=60,
        activity_level='light', fitness_goal='weight_loss',
        dietary_preference='vegetarian',
        bmi=22.0, bmi_category='Normal weight',
        bmr=1400, daily_calories=1900, calorie_target=1400,
    )
    p2 = UserProfile.objects.create(
        age=25, height_cm=175, weight_kg=75,
        activity_level='active', fitness_goal='weight_gain',
        dietary_preference='non_vegetarian',
        bmi=24.5, bmi_category='Normal weight',
        bmr=1600, daily_calories=2800, calorie_target=3300,
    )
    food = Food.objects.first()
    log = FoodLog.objects.create(
        profile=p1, food=food,
        meal_type='lunch', quantity=1, date=timezone.localdate(),
    )

    client = Client()
    session = client.session
    session['profile_id'] = p2.pk
    session.save()

    response = client.post(f'/food/delete/{log.pk}/')
    assert response.status_code == 404

    session = client.session
    session['profile_id'] = p1.pk
    session.save()

    response = client.post(f'/food/delete/{log.pk}/')
    assert response.status_code == 302
    assert not FoodLog.objects.filter(pk=log.pk).exists()

    p1.delete()
    p2.delete()
    print('Session isolation test passed.')


def test_food_tracker_flow():
    client = Client()
    response = client.post('/planner/', {
        'age': 21, 'height_cm': 170, 'weight_kg': 65,
        'activity_level': 'moderate', 'fitness_goal': 'weight_loss',
        'dietary_preference': 'vegetarian',
    })
    assert response.status_code == 302
    profile_id = client.session.get('profile_id')
    assert profile_id is not None

    response = client.get('/food/')
    assert response.status_code == 200

    rice = Food.objects.get(name='Rice (Cooked)')
    response = client.post('/food/', {
        'food': rice.pk,
        'meal_type': 'lunch',
        'quantity': 2,
        'date': timezone.localdate().isoformat(),
    })
    assert response.status_code == 302

    logs = FoodLog.objects.filter(profile_id=profile_id)
    assert logs.count() == 1
    assert logs.first().total_calories == 400.0

    response = client.get('/result/9999/')
    assert response.status_code == 302

    FoodLog.objects.filter(profile_id=profile_id).delete()
    UserProfile.objects.filter(pk=profile_id).delete()
    print('Food tracker flow test passed.')


if __name__ == '__main__':
    test_food_log_nutrition()
    test_session_isolation()
    test_food_tracker_flow()
    print('All Phase 2 tests passed.')
