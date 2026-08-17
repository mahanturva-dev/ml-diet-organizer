"""
Health metric calculations for BMI (including Indian ICMR standards),
calorie requirements, macro targets, and daily diet quality scoring.
"""

ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'active': 1.725,
    'very_active': 1.9,
}

GOAL_CALORIE_ADJUSTMENT = {
    'weight_gain': 500,
    'weight_loss': -500,
    'maintain': 0,
}


def calculate_bmi(weight_kg, height_cm, use_indian_standards=False):
    """
    Calculate BMI and return value with category label.
    Supports standard WHO and Indian ICMR consensus guidelines.
    """
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)

    if use_indian_standards:
        if bmi < 18.5:
            category = 'Underweight'
        elif bmi < 23.0:
            category = 'Normal weight (ICMR Ideal)'
        elif bmi < 25.0:
            category = 'Overweight (ICMR Cutoff)'
        else:
            category = 'Obese (High Metabolic Risk)'
    else:
        if bmi < 18.5:
            category = 'Underweight'
        elif bmi < 25.0:
            category = 'Normal weight'
        elif bmi < 30.0:
            category = 'Overweight'
        else:
            category = 'Obese'

    return round(bmi, 1), category


def calculate_bmr(weight_kg, height_cm, age):
    """Mifflin-St Jeor BMR estimate."""
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 78
    return round(bmr, 1)


def calculate_daily_calories(bmr, activity_level):
    """TDEE = BMR × activity multiplier."""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
    return round(bmr * multiplier, 0)


def calculate_calorie_target(daily_calories, fitness_goal):
    """Apply goal-based calorie adjustment (+/- 500 kcal)."""
    adjustment = GOAL_CALORIE_ADJUSTMENT.get(fitness_goal, 0)
    return round(daily_calories + adjustment, 0)


def compute_profile_metrics(profile):
    """Calculate and return all metrics for a UserProfile instance."""
    use_indian = getattr(profile, 'use_indian_bmi', True)
    bmi, bmi_category = calculate_bmi(profile.weight_kg, profile.height_cm, use_indian_standards=use_indian)
    bmr = calculate_bmr(profile.weight_kg, profile.height_cm, profile.age)
    daily_calories = calculate_daily_calories(bmr, profile.activity_level)
    calorie_target = calculate_calorie_target(daily_calories, profile.fitness_goal)

    return {
        'bmi': bmi,
        'bmi_category': bmi_category,
        'bmr': bmr,
        'daily_calories': daily_calories,
        'calorie_target': calorie_target,
    }


MACRO_PROTEIN_RATIO = 0.25
MACRO_CARBS_RATIO = 0.45
MACRO_FAT_RATIO = 0.30

MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack']


def calculate_macro_targets(calorie_target):
    """Derive macro targets (grams) from calorie target."""
    return {
        'protein': round((calorie_target * MACRO_PROTEIN_RATIO) / 4, 1),
        'carbohydrates': round((calorie_target * MACRO_CARBS_RATIO) / 4, 1),
        'fat': round((calorie_target * MACRO_FAT_RATIO) / 9, 1),
    }


def aggregate_food_logs(logs):
    """Sum nutrition totals from a queryset of FoodLog entries."""
    totals = {
        'calories': 0.0,
        'protein': 0.0,
        'carbohydrates': 0.0,
        'fat': 0.0,
        'fiber': 0.0,
        'sodium': 0.0,
        'sugar': 0.0,
    }
    for log in logs:
        totals['calories'] += log.total_calories
        totals['protein'] += log.total_protein
        totals['carbohydrates'] += log.total_carbohydrates
        totals['fat'] += log.total_fat
        totals['fiber'] += log.total_fiber
        totals['sodium'] += getattr(log, 'total_sodium', 0)
        totals['sugar'] += getattr(log, 'total_sugar', 0)

    for key in totals:
        totals[key] = round(totals[key], 1)
    return totals


def meal_breakdown(logs):
    """Return calorie totals grouped by meal type."""
    breakdown = {meal: 0.0 for meal in MEAL_TYPES}
    for log in logs:
        breakdown[log.meal_type] += log.total_calories
    for meal in breakdown:
        breakdown[meal] = round(breakdown[meal], 1)
    return breakdown


def calorie_progress(consumed, target):
    """Return consumed, target, remaining, percentage, and exceeded flag."""
    remaining = round(target - consumed, 1)
    percentage = round(min((consumed / target) * 100, 100), 1) if target > 0 else 0
    exceeded = consumed > target
    return {
        'consumed': consumed,
        'target': target,
        'remaining': remaining,
        'percentage': percentage,
        'exceeded': exceeded,
        'over_by': round(consumed - target, 1) if exceeded else 0,
    }


def calculate_health_score(totals, calorie_target, macro_targets, water_glasses=0):
    """
    Compute daily Diet Quality & Compliance Score (0 to 100).
    """
    if totals['calories'] == 0:
        return {'score': 0, 'label': 'No Meals Logged Yet', 'color': '#6c757d'}

    score = 0

    # 1. Calorie Accuracy (up to 35 pts)
    cal_diff_pct = abs(totals['calories'] - calorie_target) / max(calorie_target, 1)
    if cal_diff_pct <= 0.10:
        score += 35
    elif cal_diff_pct <= 0.20:
        score += 25
    elif cal_diff_pct <= 0.30:
        score += 15
    else:
        score += 5

    # 2. Protein Target (up to 25 pts)
    pro_target = macro_targets.get('protein', 50)
    pro_pct = totals['protein'] / max(pro_target, 1)
    if pro_pct >= 0.85:
        score += 25
    elif pro_pct >= 0.60:
        score += 18
    elif pro_pct >= 0.40:
        score += 10
    else:
        score += 5

    # 3. Water Hydration (up to 20 pts)
    if water_glasses >= 8:
        score += 20
    elif water_glasses >= 5:
        score += 14
    elif water_glasses >= 3:
        score += 8
    elif water_glasses >= 1:
        score += 4

    # 4. Dietary Fiber (up to 20 pts)
    if totals['fiber'] >= 20:
        score += 20
    elif totals['fiber'] >= 12:
        score += 14
    elif totals['fiber'] >= 6:
        score += 8
    else:
        score += 3

    score = min(100, max(0, score))

    if score >= 85:
        label = '🌟 Outstanding Balance'
        color = '#2d6a4f'
    elif score >= 70:
        label = '✨ Good Progress'
        color = '#40916c'
    elif score >= 50:
        label = '⚡ Moderate Compliance'
        color = '#f59e0b'
    else:
        label = '⚠️ Needs Attention'
        color = '#c1121f'

    return {'score': score, 'label': label, 'color': color}
