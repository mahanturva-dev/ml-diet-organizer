import datetime
import json

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from ml.recommender import generate_daily_meal_plan, get_recommendations
from .calculations import (
    aggregate_food_logs,
    calculate_health_score,
    calculate_macro_targets,
    calorie_progress,
    compute_profile_metrics,
    meal_breakdown,
)
from .forms import (
    CustomFoodForm,
    ExerciseLogForm,
    FoodLogForm,
    UserProfileForm,
    WeightLogForm,
)
from .models import (
    ExerciseLog,
    FastingLog,
    Food,
    FoodLog,
    UserProfile,
    WaterLog,
    WeightLog,
)
from .session_utils import get_session_profile, profile_owns_resource, require_session_profile


def home(request):
    """Landing page with project overview."""
    return render(request, 'home.html')


def planner(request):
    """User profile input form with health conditions, fasting protocols, and allergies."""
    profile = get_session_profile(request)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            metrics = compute_profile_metrics(profile)
            profile.bmi = metrics['bmi']
            profile.bmi_category = metrics['bmi_category']
            profile.bmr = metrics['bmr']
            profile.daily_calories = metrics['daily_calories']
            profile.calorie_target = metrics['calorie_target']
            profile.save()

            request.session['profile_id'] = profile.pk
            messages.success(request, 'Your nutritional profile has been generated!')
            return redirect('result', profile_id=profile.pk)
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'planner.html', {'form': form})


def result(request, profile_id):
    """Display BMI, calorie calculation results, and smart goal projection."""
    profile = get_object_or_404(UserProfile, pk=profile_id)
    if not profile_owns_resource(request, profile):
        messages.error(request, 'You can only view your own profile results.')
        return redirect('planner')

    # Goal weight projection
    weeks_to_goal = None
    projected_date = None
    if profile.target_weight_kg and profile.weight_kg != profile.target_weight_kg:
        weight_diff = abs(profile.weight_kg - profile.target_weight_kg)
        weekly_change = 0.5  # ~500 kcal deficit/surplus per day
        weeks_to_goal = round(weight_diff / weekly_change, 1)
        projected_date = timezone.localdate() + datetime.timedelta(weeks=weeks_to_goal)

    context = {
        'profile': profile,
        'weeks_to_goal': weeks_to_goal,
        'projected_date': projected_date,
    }
    return render(request, 'result.html', context)


def food_tracker(request):
    """Comprehensive daily food logging, fasting, workouts, health score, and ML planner."""
    profile = require_session_profile(request)
    if profile is None:
        return redirect('planner')

    today = timezone.localdate()
    date_param = request.GET.get('date')
    if date_param:
        try:
            selected_date = datetime.date.fromisoformat(date_param)
        except (ValueError, TypeError):
            selected_date = today
    else:
        selected_date = today

    prev_date = selected_date - datetime.timedelta(days=1)
    next_date = selected_date + datetime.timedelta(days=1)
    is_today = (selected_date == today)

    # Vrat / Upvas Mode status
    is_vrat_mode = request.session.get('is_vrat_mode', False)

    # Food logs
    logs = FoodLog.objects.filter(profile=profile, date=selected_date).select_related('food')

    if request.method == 'POST':
        form = FoodLogForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.profile = profile
            entry.save()
            messages.success(request, f'Added {entry.food.name} to your log.')
            return redirect(f"{reverse('food_tracker')}?date={entry.date.isoformat()}")
    else:
        form = FoodLogForm(initial={'date': selected_date})

    totals = aggregate_food_logs(logs)
    meals = meal_breakdown(logs)
    macro_targets = calculate_macro_targets(profile.calorie_target)
    progress = calorie_progress(totals['calories'], profile.calorie_target)

    # Exercise and Net Calories
    exercise_logs = ExerciseLog.objects.filter(profile=profile, date=selected_date)
    total_burned = sum(e.calories_burned for e in exercise_logs)
    net_calories = round(max(0, totals['calories'] - total_burned), 1)

    def macro_pct(consumed, target):
        if target <= 0:
            return 0
        return min(round((consumed / target) * 100, 1), 100)

    macro_progress = {
        'protein': macro_pct(totals['protein'], macro_targets['protein']),
        'carbohydrates': macro_pct(totals['carbohydrates'], macro_targets['carbohydrates']),
        'fat': macro_pct(totals['fat'], macro_targets['fat']),
    }

    # Water tracking
    water_log, _ = WaterLog.objects.get_or_create(profile=profile, date=selected_date)

    # Health score
    health_score = calculate_health_score(totals, profile.calorie_target, macro_targets, water_log.glasses)

    # Log streak
    streak = 0
    check_day = selected_date
    while True:
        if FoodLog.objects.filter(profile=profile, date=check_day).exists():
            streak += 1
            check_day -= datetime.timedelta(days=1)
        else:
            break

    # ML recommendations
    remaining_cals = max(0, profile.calorie_target - totals['calories'])
    remaining_macros = {
        'protein': max(0, macro_targets['protein'] - totals['protein']),
        'carbohydrates': max(0, macro_targets['carbohydrates'] - totals['carbohydrates']),
        'fat': max(0, macro_targets['fat'] - totals['fat']),
    }
    recommendations = get_recommendations(
        profile,
        remaining_cals,
        remaining_macros,
        Food.objects.all(),
        is_vrat=is_vrat_mode,
        top_k=4,
    )

    # Automated 1-Day Meal Plan Generator
    generated_plan = generate_daily_meal_plan(
        profile,
        profile.calorie_target,
        Food.objects.all(),
        is_vrat=is_vrat_mode,
    )

    # Active Fasting Timer
    active_fast = FastingLog.objects.filter(profile=profile, is_active=True).first()
    fast_hours_elapsed = 0
    if active_fast:
        elapsed = timezone.now() - active_fast.start_time
        fast_hours_elapsed = round(elapsed.total_seconds() / 3600, 1)

    # Weight logs for trend
    weight_logs = WeightLog.objects.filter(profile=profile)[:10]

    # 7-day calorie trend
    history_labels = []
    history_calories = []
    history_targets = []
    for i in range(6, -1, -1):
        d = selected_date - datetime.timedelta(days=i)
        day_logs = FoodLog.objects.filter(profile=profile, date=d)
        day_cals = sum(l.total_calories for l in day_logs)
        history_labels.append(d.strftime('%a (%b %d)'))
        history_calories.append(round(day_cals, 1))
        history_targets.append(round(profile.calorie_target, 1))

    history_data_json = json.dumps({
        'labels': history_labels,
        'calories': history_calories,
        'targets': history_targets,
    })

    # All foods for comparison dropdown
    all_foods = list(Food.objects.values('id', 'name', 'serving_size', 'calories', 'protein', 'carbohydrates', 'fat', 'fiber', 'sodium_mg', 'sugar_g', 'dietary_type', 'is_vrat_friendly'))
    all_foods_json = json.dumps(all_foods)

    context = {
        'profile': profile,
        'form': form,
        'custom_food_form': CustomFoodForm(),
        'exercise_form': ExerciseLogForm(initial={'date': selected_date}),
        'weight_form': WeightLogForm(initial={'date': selected_date}),
        'logs': logs,
        'exercise_logs': exercise_logs,
        'total_burned': total_burned,
        'net_calories': net_calories,
        'totals': totals,
        'meals': meals,
        'macro_targets': macro_targets,
        'macro_progress': macro_progress,
        'progress': progress,
        'today': today,
        'selected_date': selected_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'is_today': is_today,
        'water_log': water_log,
        'recommendations': recommendations,
        'generated_plan': generated_plan,
        'health_score': health_score,
        'streak': streak,
        'is_vrat_mode': is_vrat_mode,
        'active_fast': active_fast,
        'fast_hours_elapsed': fast_hours_elapsed,
        'weight_logs': weight_logs,
        'history_data_json': history_data_json,
        'all_foods_json': all_foods_json,
    }
    return render(request, 'food_tracker.html', context)


@require_POST
def toggle_vrat_mode(request):
    """Toggle Vrat / Fasting mode in session."""
    current = request.session.get('is_vrat_mode', False)
    request.session['is_vrat_mode'] = not current
    date_str = request.POST.get('date', '')
    if not current:
        messages.success(request, '🕉️ Vrat / Upvas Fasting Mode Activated! Food suggestions are now fasting-compliant.')
    else:
        messages.info(request, 'Regular Diet Mode Restored.')
    return redirect(f"{reverse('food_tracker')}?date={date_str}" if date_str else reverse('food_tracker'))


@require_POST
def apply_meal_plan(request):
    """Apply the generated 4-meal plan to the active day's log."""
    profile = require_session_profile(request)
    if profile is None:
        return redirect('planner')

    date_str = request.POST.get('date', '')
    try:
        log_date = datetime.date.fromisoformat(date_str) if date_str else timezone.localdate()
    except (ValueError, TypeError):
        log_date = timezone.localdate()

    is_vrat_mode = request.session.get('is_vrat_mode', False)
    plan = generate_daily_meal_plan(profile, profile.calorie_target, Food.objects.all(), is_vrat=is_vrat_mode)

    added_count = 0
    for meal_key, item in plan['meals'].items():
        FoodLog.objects.create(
            profile=profile,
            food=item['food'],
            meal_type=meal_key,
            quantity=item['portion'],
            date=log_date,
        )
        added_count += 1

    messages.success(request, f'🎉 Successfully logged {added_count} meals from your AI Daily Meal Plan ({plan["totals"]["calories"]} kcal)!')
    return redirect(f"{reverse('food_tracker')}?date={log_date.isoformat()}")


@require_POST
def delete_food_log(request, log_id):
    """Remove a food log entry."""
    profile = require_session_profile(request)
    if profile is None:
        return redirect('planner')

    log = get_object_or_404(FoodLog, pk=log_id, profile=profile)
    food_name = log.food.name
    log_date = log.date
    log.delete()
    messages.success(request, f'Removed {food_name} from your log.')
    return redirect(f"{reverse('food_tracker')}?date={log_date.isoformat()}")


@require_POST
def add_custom_food(request):
    """Add custom food item."""
    profile = require_session_profile(request)
    if profile is None:
        return redirect('planner')

    form = CustomFoodForm(request.POST)
    date_str = request.POST.get('redirect_date', '')
    if form.is_valid():
        food = form.save()
        messages.success(request, f'Added custom food "{food.name}" to the database!')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field.replace("_", " ").title()}: {error}')

    return redirect(f"{reverse('food_tracker')}?date={date_str}" if date_str else reverse('food_tracker'))


@require_POST
def quick_add_food(request, food_id):
    """Quick-add a food to the active log date."""
    profile = require_session_profile(request)
    if profile is None:
        return redirect('planner')

    food = get_object_or_404(Food, pk=food_id)
    meal_type = request.POST.get('meal_type', 'snack')
    date_str = request.POST.get('date', '')
    quantity = float(request.POST.get('quantity', 1.0))
    try:
        log_date = datetime.date.fromisoformat(date_str) if date_str else timezone.localdate()
    except (ValueError, TypeError):
        log_date = timezone.localdate()

    FoodLog.objects.create(
        profile=profile,
        food=food,
        meal_type=meal_type,
        quantity=quantity,
        date=log_date,
    )
    messages.success(request, f'Quick-added {quantity}x {food.name} ({meal_type.title()}) to your log.')
    return redirect(f"{reverse('food_tracker')}?date={log_date.isoformat()}")


@require_POST
def update_water_log(request):
    """Increment or decrement water intake glasses."""
    profile = require_session_profile(request)
    if profile is None:
        return redirect('planner')

    action = request.POST.get('action')
    date_str = request.POST.get('date', '')
    try:
        log_date = datetime.date.fromisoformat(date_str) if date_str else timezone.localdate()
    except (ValueError, TypeError):
        log_date = timezone.localdate()

    water_log, _ = WaterLog.objects.get_or_create(profile=profile, date=log_date)
    if action == 'add':
        water_log.glasses += 1
        water_log.save()
        messages.success(request, f'Logged 1 glass (+250ml) of water. Total: {water_log.total_ml}ml / {water_log.target_ml}ml')
    elif action == 'remove' and water_log.glasses > 0:
        water_log.glasses -= 1
        water_log.save()
        messages.info(request, f'Removed 1 glass of water. Total: {water_log.total_ml}ml')

    return redirect(f"{reverse('food_tracker')}?date={log_date.isoformat()}")


@require_POST
def add_exercise_log(request):
    """Log an exercise workout."""
    profile = require_session_profile(request)
    if profile is None:
        return redirect('planner')

    form = ExerciseLogForm(request.POST)
    date_str = request.POST.get('date', '')
    if form.is_valid():
        ex = form.save(commit=False)
        ex.profile = profile
        ex.save()
        messages.success(request, f'Logged workout: {ex.activity_name} ({ex.calories_burned} kcal burned)!')
    else:
        messages.error(request, 'Please enter valid workout details.')

    return redirect(f"{reverse('food_tracker')}?date={date_str}" if date_str else reverse('food_tracker'))


@require_POST
def delete_exercise_log(request, log_id):
    """Remove workout entry."""
    profile = require_session_profile(request)
    if profile is None:
        return redirect('planner')

    ex = get_object_or_404(ExerciseLog, pk=log_id, profile=profile)
    log_date = ex.date
    ex.delete()
    messages.success(request, 'Removed workout entry.')
    return redirect(f"{reverse('food_tracker')}?date={log_date.isoformat()}")


@require_POST
def add_weight_log(request):
    """Log periodic weigh-in check-in."""
    profile = require_session_profile(request)
    if profile is None:
        return redirect('planner')

    form = WeightLogForm(request.POST)
    date_str = request.POST.get('date', '')
    if form.is_valid():
        w = form.save(commit=False)
        w.profile = profile
        w.save()
        # Update current weight on profile
        profile.weight_kg = w.weight_kg
        profile.save()
        messages.success(request, f'Recorded weight check-in: {w.weight_kg} kg.')
    else:
        messages.error(request, 'Please enter a valid weight.')

    return redirect(f"{reverse('food_tracker')}?date={date_str}" if date_str else reverse('food_tracker'))


@require_POST
def toggle_fasting(request):
    """Start or stop active intermittent fasting timer."""
    profile = require_session_profile(request)
    if profile is None:
        return redirect('planner')

    action = request.POST.get('action')
    date_str = request.POST.get('date', '')

    if action == 'start':
        FastingLog.objects.filter(profile=profile, is_active=True).update(is_active=False)
        hours = 16
        if profile.fasting_protocol == '14_10':
            hours = 14
        elif profile.fasting_protocol == '12_12':
            hours = 12

        FastingLog.objects.create(
            profile=profile,
            start_time=timezone.now(),
            target_hours=hours,
            is_active=True,
        )
        messages.success(request, f'⏳ Started {hours}-hour Fasting Window!')
    elif action == 'stop':
        active = FastingLog.objects.filter(profile=profile, is_active=True).first()
        if active:
            active.is_active = False
            active.completed_at = timezone.now()
            active.save()
            elapsed_h = round((active.completed_at - active.start_time).total_seconds() / 3600, 1)
            messages.success(request, f'🎉 Completed fast of {elapsed_h} hours! Eating window is now open.')

    return redirect(f"{reverse('food_tracker')}?date={date_str}" if date_str else reverse('food_tracker'))
