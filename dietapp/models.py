from django.db import models


class UserProfile(models.Model):
    """Stores user health profile, calculated metrics, health goals, and fasting preferences."""

    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentary (little or no exercise)'),
        ('light', 'Lightly Active (1–3 days/week)'),
        ('moderate', 'Moderately Active (3–5 days/week)'),
        ('active', 'Very Active (6–7 days/week)'),
        ('very_active', 'Extra Active (hard exercise / physical job)'),
    ]

    GOAL_CHOICES = [
        ('weight_gain', 'Weight Gain'),
        ('weight_loss', 'Weight Loss'),
        ('maintain', 'Maintain Weight'),
    ]

    DIET_CHOICES = [
        ('vegetarian', 'Vegetarian'),
        ('non_vegetarian', 'Non-Vegetarian'),
    ]

    CONDITION_CHOICES = [
        ('none', 'General / Healthy Maintenance'),
        ('diabetes', 'Diabetes / Blood Sugar Control (Low GI, High Fiber)'),
        ('hypertension', 'Hypertension / Heart Health (Low Sodium, High Potassium)'),
        ('pcos', 'PCOS / Thyroid Support (Anti-inflammatory, High Protein)'),
        ('gerd', 'GERD / Digestive Sensitivity (Mild, Low Acid)'),
    ]

    FASTING_CHOICES = [
        ('none', 'No Fasting Schedule'),
        ('16_8', '16:8 Protocol (16h Fast / 8h Eating Window)'),
        ('14_10', '14:10 Protocol (14h Fast / 10h Eating Window)'),
        ('12_12', '12:12 Circadian Fasting'),
    ]

    age = models.PositiveIntegerField()
    height_cm = models.FloatField(help_text='Height in centimeters')
    weight_kg = models.FloatField(help_text='Weight in kilograms')
    target_weight_kg = models.FloatField(null=True, blank=True, help_text='Target goal weight in kg')
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)
    fitness_goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    dietary_preference = models.CharField(max_length=20, choices=DIET_CHOICES)
    health_condition = models.CharField(max_length=30, choices=CONDITION_CHOICES, default='none')
    allergies = models.CharField(max_length=150, blank=True, help_text='e.g. gluten_free, dairy_free, nut_free')
    fasting_protocol = models.CharField(max_length=20, choices=FASTING_CHOICES, default='none')
    use_indian_bmi = models.BooleanField(default=True, help_text='Use Indian ICMR standards (overweight >= 23, obese >= 25)')

    # Calculated fields
    bmi = models.FloatField(null=True, blank=True)
    bmi_category = models.CharField(max_length=30, blank=True)
    bmr = models.FloatField(null=True, blank=True)
    daily_calories = models.FloatField(null=True, blank=True)
    calorie_target = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Profile #{self.pk} — {self.get_fitness_goal_display()}'


class Food(models.Model):
    """Sample food database (demo/educational data per serving)."""

    DIETARY_TYPE_CHOICES = [
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('non_vegetarian', 'Non-Vegetarian'),
        ('eggetarian', 'Eggetarian'),
    ]

    name = models.CharField(max_length=120, unique=True)
    serving_size = models.CharField(max_length=80)
    calories = models.FloatField(help_text='Calories per serving')
    protein = models.FloatField(help_text='Protein (g) per serving')
    carbohydrates = models.FloatField(help_text='Carbohydrates (g) per serving')
    fat = models.FloatField(help_text='Fat (g) per serving')
    fiber = models.FloatField(help_text='Fiber (g) per serving')
    dietary_type = models.CharField(max_length=20, choices=DIETARY_TYPE_CHOICES)

    # Health & Fasting Flags
    is_vrat_friendly = models.BooleanField(default=False, help_text='Allowed during Upvas/Vrat')
    is_gluten_free = models.BooleanField(default=True)
    is_dairy_free = models.BooleanField(default=True)
    is_nut_free = models.BooleanField(default=True)
    sodium_mg = models.FloatField(default=50.0, help_text='Sodium (mg)')
    sugar_g = models.FloatField(default=2.0, help_text='Sugar (g)')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class FoodLog(models.Model):
    """Daily food intake log linked to a user profile."""

    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='food_logs',
    )
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='logs')
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    quantity = models.FloatField(help_text='Number of servings')
    date = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.food.name} × {self.quantity} ({self.get_meal_type_display()})'

    @property
    def total_calories(self):
        return round(self.food.calories * self.quantity, 1)

    @property
    def total_protein(self):
        return round(self.food.protein * self.quantity, 1)

    @property
    def total_carbohydrates(self):
        return round(self.food.carbohydrates * self.quantity, 1)

    @property
    def total_fat(self):
        return round(self.food.fat * self.quantity, 1)

    @property
    def total_fiber(self):
        return round(self.food.fiber * self.quantity, 1)

    @property
    def total_sodium(self):
        return round(self.food.sodium_mg * self.quantity, 1)

    @property
    def total_sugar(self):
        return round(self.food.sugar_g * self.quantity, 1)


class WaterLog(models.Model):
    """Daily water intake log for a user profile."""

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='water_logs',
    )
    date = models.DateField()
    glasses = models.PositiveIntegerField(default=0, help_text='Number of 250ml glasses')
    target_glasses = models.PositiveIntegerField(default=8, help_text='Target glasses per day')

    class Meta:
        ordering = ['-date']
        unique_together = ('profile', 'date')

    def __str__(self):
        return f'Profile #{self.profile_id} — {self.glasses}/{self.target_glasses} glasses on {self.date}'

    @property
    def total_ml(self):
        return self.glasses * 250

    @property
    def target_ml(self):
        return self.target_glasses * 250

    @property
    def progress_pct(self):
        if self.target_glasses <= 0:
            return 0
        return min(round((self.glasses / self.target_glasses) * 100, 1), 100)


class ExerciseLog(models.Model):
    """Physical activity and workout log."""

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='exercise_logs',
    )
    date = models.DateField()
    activity_name = models.CharField(max_length=80)
    duration_mins = models.PositiveIntegerField(default=30)
    calories_burned = models.FloatField(default=150.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.activity_name} ({self.duration_mins}m) — {self.calories_burned} kcal'


class WeightLog(models.Model):
    """Periodic weight check-in log."""

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='weight_logs',
    )
    date = models.DateField()
    weight_kg = models.FloatField()
    notes = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ['date']
        unique_together = ('profile', 'date')

    def __str__(self):
        return f'{self.weight_kg} kg on {self.date}'


class FastingLog(models.Model):
    """Intermittent fasting tracker log."""

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='fasting_logs',
    )
    start_time = models.DateTimeField()
    target_hours = models.PositiveIntegerField(default=16)
    is_active = models.BooleanField(default=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f'Fast #{self.id} — {self.target_hours}h protocol'
