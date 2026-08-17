"""
ML-Based Food Recommendation & Daily Meal Plan Generator.
Uses K-Nearest Neighbors (KNN), dietary constraints, allergen filters, and Vrat mode.
"""

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


def get_dietary_filter(dietary_preference):
    """Return list of allowed food dietary types based on user preference."""
    if dietary_preference == 'vegetarian':
        return ['vegetarian', 'vegan']
    return ['vegetarian', 'vegan', 'eggetarian', 'non_vegetarian']


def filter_foods_by_profile(food_queryset, profile, is_vrat=False):
    """Filter queryset by dietary preference, Vrat status, and allergen restrictions."""
    allowed_types = get_dietary_filter(profile.dietary_preference)
    qs = food_queryset.filter(dietary_type__in=allowed_types)

    if is_vrat:
        qs = qs.filter(is_vrat_friendly=True)

    if profile.allergies:
        allergy_list = [a.strip().lower() for a in profile.allergies.split(',') if a.strip()]
        if 'gluten_free' in allergy_list:
            qs = qs.filter(is_gluten_free=True)
        if 'dairy_free' in allergy_list:
            qs = qs.filter(is_dairy_free=True)
        if 'nut_free' in allergy_list:
            qs = qs.filter(is_nut_free=True)

    if profile.health_condition == 'diabetes':
        # Prioritize low sugar, higher fiber
        qs = qs.filter(sugar_g__lte=12.0)
    elif profile.health_condition == 'hypertension':
        # Prioritize lower sodium
        qs = qs.filter(sodium_mg__lte=150.0)

    return qs


def get_recommendations(profile, remaining_calories, remaining_macros, food_queryset, is_vrat=False, top_k=4):
    """
    Generate top_k personalized food recommendations using KNN.
    """
    candidate_foods = list(filter_foods_by_profile(food_queryset, profile, is_vrat=is_vrat))

    if not candidate_foods:
        # Fallback to general foods if strict filter returned 0
        candidate_foods = list(food_queryset.filter(dietary_type__in=get_dietary_filter(profile.dietary_preference)))
        if not candidate_foods:
            return []

    data = []
    for f in candidate_foods:
        data.append({
            'id': f.id,
            'calories': f.calories,
            'protein': f.protein,
            'carbohydrates': f.carbohydrates,
            'fat': f.fat,
            'fiber': f.fiber,
        })
    df = pd.DataFrame(data)

    feature_cols = ['calories', 'protein', 'carbohydrates', 'fat', 'fiber']
    X = df[feature_cols].values

    if remaining_calories > 150:
        target_cal = min(remaining_calories * 0.5, 450)
        target_protein = max(remaining_macros.get('protein', 15) * 0.5, 5)
        target_carbs = max(remaining_macros.get('carbohydrates', 30) * 0.5, 10)
        target_fat = max(remaining_macros.get('fat', 10) * 0.5, 3)
        target_fiber = 4.0
    else:
        target_cal = 80.0
        target_protein = 5.0
        target_carbs = 10.0
        target_fat = 1.5
        target_fiber = 3.0

    target_vector = np.array([[target_cal, target_protein, target_carbs, target_fat, target_fiber]])

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    target_scaled = scaler.transform(target_vector)

    k = min(top_k, len(candidate_foods))
    knn = NearestNeighbors(n_neighbors=k, metric='euclidean')
    knn.fit(X_scaled)

    distances, indices = knn.kneighbors(target_scaled)

    recommendations = []
    for dist, idx in zip(distances[0], indices[0]):
        food_obj = candidate_foods[idx]

        if is_vrat:
            reason = '🕉️ Traditional Vrat / Fasting Approved Item'
        elif profile.health_condition == 'diabetes' and food_obj.fiber >= 3.5:
            reason = '🩸 Low GI & High Fiber for Blood Sugar'
        elif profile.health_condition == 'hypertension' and food_obj.sodium_mg <= 80:
            reason = '🫀 Low Sodium Heart-Healthy Pick'
        elif profile.fitness_goal == 'weight_gain' and food_obj.protein >= 12:
            reason = '💪 High Protein for Muscle & Weight Gain'
        elif profile.fitness_goal == 'weight_loss' and food_obj.calories <= 150:
            reason = '🔥 Low Calorie, High Satiety'
        elif food_obj.protein >= 15:
            reason = '⚡ Excellent Protein Source'
        elif food_obj.fiber >= 4:
            reason = '🌱 Rich in Dietary Fiber'
        else:
            reason = f'✨ Balanced {food_obj.get_dietary_type_display()} Choice'

        match_score = max(55, round(100 - (dist * 12), 1))
        match_score = min(99, match_score)

        recommendations.append({
            'food': food_obj,
            'reason': reason,
            'match_score': match_score,
        })

    return recommendations


def generate_daily_meal_plan(profile, target_calories, food_queryset, is_vrat=False):
    """
    Generate a cohesive 4-meal daily diet plan (Breakfast, Lunch, Dinner, Snack)
    using KNN targeting standard meal caloric distributions.
    """
    candidate_foods = list(filter_foods_by_profile(food_queryset, profile, is_vrat=is_vrat))
    if len(candidate_foods) < 4:
        candidate_foods = list(food_queryset.all())

    df = pd.DataFrame([{
        'id': f.id,
        'calories': f.calories,
        'protein': f.protein,
        'carbohydrates': f.carbohydrates,
        'fat': f.fat,
        'fiber': f.fiber,
    } for f in candidate_foods])

    feature_cols = ['calories', 'protein', 'carbohydrates', 'fat', 'fiber']
    X = df[feature_cols].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Standard daily calorie split
    meal_splits = {
        'breakfast': {'cal_pct': 0.25, 'pro_pct': 0.25, 'name': 'Breakfast'},
        'lunch': {'cal_pct': 0.35, 'pro_pct': 0.35, 'name': 'Lunch'},
        'dinner': {'cal_pct': 0.25, 'pro_pct': 0.25, 'name': 'Dinner'},
        'snack': {'cal_pct': 0.15, 'pro_pct': 0.15, 'name': 'Evening Snack'},
    }

    knn = NearestNeighbors(n_neighbors=len(candidate_foods), metric='euclidean')
    knn.fit(X_scaled)

    used_food_ids = set()
    meal_plan = {}
    tot_cal = 0
    tot_pro = 0
    tot_carb = 0
    tot_fat = 0

    for meal_key, split in meal_splits.items():
        slot_cal = target_calories * split['cal_pct']
        slot_pro = (slot_cal * 0.25) / 4
        slot_carb = (slot_cal * 0.45) / 4
        slot_fat = (slot_cal * 0.30) / 9

        target_vec = scaler.transform([[slot_cal, slot_pro, slot_carb, slot_fat, 3.0]])
        _, indices = knn.kneighbors(target_vec)

        chosen_food = None
        for idx in indices[0]:
            f_obj = candidate_foods[idx]
            if f_obj.id not in used_food_ids:
                chosen_food = f_obj
                used_food_ids.add(f_obj.id)
                break

        if not chosen_food:
            chosen_food = candidate_foods[indices[0][0]]

        # Portion multiplier (round to 1 or 1.5 or 2)
        portion = round(max(1.0, slot_cal / max(50, chosen_food.calories)), 1)
        if portion > 2.5:
            portion = 2.0

        meal_plan[meal_key] = {
            'food': chosen_food,
            'slot_name': split['name'],
            'portion': portion,
            'calories': round(chosen_food.calories * portion, 1),
            'protein': round(chosen_food.protein * portion, 1),
            'carbohydrates': round(chosen_food.carbohydrates * portion, 1),
            'fat': round(chosen_food.fat * portion, 1),
        }

        tot_cal += meal_plan[meal_key]['calories']
        tot_pro += meal_plan[meal_key]['protein']
        tot_carb += meal_plan[meal_key]['carbohydrates']
        tot_fat += meal_plan[meal_key]['fat']

    return {
        'meals': meal_plan,
        'totals': {
            'calories': round(tot_cal, 1),
            'protein': round(tot_pro, 1),
            'carbohydrates': round(tot_carb, 1),
            'fat': round(tot_fat, 1),
        },
        'target_calories': target_calories,
        'calorie_diff': round(tot_cal - target_calories, 1),
    }
