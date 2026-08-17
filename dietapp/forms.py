from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import ExerciseLog, Food, FoodLog, UserProfile, WeightLog


class UserProfileForm(forms.ModelForm):
    """Form for collecting user health, preferences, allergies, and fasting habits."""

    ALLERGY_CHOICES = [
        ('gluten_free', 'Gluten-Free'),
        ('dairy_free', 'Dairy/Lactose-Free'),
        ('nut_free', 'Nut-Free'),
    ]

    allergy_options = forms.MultipleChoiceField(
        choices=ALLERGY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox-inline'}),
        label='Food Sensitivities / Allergies',
    )

    class Meta:
        model = UserProfile
        fields = [
            'age',
            'height_cm',
            'weight_kg',
            'target_weight_kg',
            'activity_level',
            'fitness_goal',
            'dietary_preference',
            'health_condition',
            'fasting_protocol',
            'use_indian_bmi',
        ]
        widgets = {
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 25',
                'min': 10,
                'max': 100,
            }),
            'height_cm': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 172',
                'min': 100,
                'max': 250,
                'step': '0.1',
            }),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 68',
                'min': 30,
                'max': 200,
                'step': '0.1',
            }),
            'target_weight_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 62 (optional)',
                'min': 30,
                'max': 200,
                'step': '0.1',
            }),
            'activity_level': forms.Select(attrs={'class': 'form-control'}),
            'fitness_goal': forms.Select(attrs={'class': 'form-control'}),
            'dietary_preference': forms.Select(attrs={'class': 'form-control'}),
            'health_condition': forms.Select(attrs={'class': 'form-control'}),
            'fasting_protocol': forms.Select(attrs={'class': 'form-control'}),
            'use_indian_bmi': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'height_cm': 'Height (cm)',
            'weight_kg': 'Current Weight (kg)',
            'target_weight_kg': 'Goal Target Weight (kg)',
            'activity_level': 'Daily Activity Level',
            'fitness_goal': 'Primary Fitness Goal',
            'dietary_preference': 'Dietary Preference',
            'health_condition': 'Health Condition / Focus',
            'fasting_protocol': 'Intermittent Fasting Schedule',
            'use_indian_bmi': 'Use Indian ICMR Standards (Overweight ≥23, Obese ≥25)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_weight_kg'].required = False
        self.fields['health_condition'].required = False
        self.fields['fasting_protocol'].required = False
        self.fields['use_indian_bmi'].required = False
        if not self.initial.get('health_condition'):
            self.initial['health_condition'] = 'none'
        if not self.initial.get('fasting_protocol'):
            self.initial['fasting_protocol'] = 'none'
        if self.instance and self.instance.pk and self.instance.allergies:
            self.fields['allergy_options'].initial = [
                a.strip() for a in self.instance.allergies.split(',') if a.strip()
            ]

    def save(self, commit=True):
        instance = super().save(commit=False)
        selected_allergies = self.cleaned_data.get('allergy_options', [])
        instance.allergies = ','.join(selected_allergies)
        if commit:
            instance.save()
        return instance


class FoodLogForm(forms.ModelForm):
    """Form for logging a food entry."""

    food_search = forms.CharField(
        required=False,
        label='Search Food Database',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'food-search',
            'placeholder': 'Type to filter foods (e.g. paneer, makhana, roti)…',
            'autocomplete': 'off',
        }),
    )

    class Meta:
        model = FoodLog
        fields = ['food', 'meal_type', 'quantity', 'date']
        widgets = {
            'food': forms.Select(attrs={
                'class': 'form-control',
                'id': 'food-select',
                'size': '8',
            }),
            'meal_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.1',
                'step': '0.1',
                'value': '1',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['food'].queryset = Food.objects.all()
        self.fields['food'].label_from_instance = (
            lambda obj: f'{"🕉️ [Vrat] " if obj.is_vrat_friendly else ""}{obj.name} ({obj.serving_size}) — {obj.calories} kcal | {obj.protein}g P'
        )
        if not self.initial.get('date') and not self.data.get('date'):
            self.initial['date'] = timezone.localdate()

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity is None or quantity <= 0:
            raise ValidationError('Quantity must be greater than zero.')
        return quantity

    def clean_date(self):
        log_date = self.cleaned_data['date']
        return log_date

    def clean_food(self):
        food = self.cleaned_data.get('food')
        if food is None:
            raise ValidationError('Please select a valid food item.')
        return food


class CustomFoodForm(forms.ModelForm):
    """Form for adding custom food items into the database."""

    class Meta:
        model = Food
        fields = [
            'name',
            'serving_size',
            'calories',
            'protein',
            'carbohydrates',
            'fat',
            'fiber',
            'dietary_type',
            'is_vrat_friendly',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Homemade Sattu Drink',
            }),
            'serving_size': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 1 bowl (200g)',
            }),
            'calories': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 150',
                'min': '0',
                'step': '0.1',
            }),
            'protein': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 12.0',
                'min': '0',
                'step': '0.1',
            }),
            'carbohydrates': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 18.0',
                'min': '0',
                'step': '0.1',
            }),
            'fat': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 4.0',
                'min': '0',
                'step': '0.1',
            }),
            'fiber': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 2.5',
                'min': '0',
                'step': '0.1',
            }),
            'dietary_type': forms.Select(attrs={'class': 'form-control'}),
            'is_vrat_friendly': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ExerciseLogForm(forms.ModelForm):
    """Form for logging workouts and calorie burn."""

    ACTIVITY_PRESETS = [
        ('Brisk Walking (5 km/h)', 150),
        ('Running / Jogging', 300),
        ('Gym / Strength Training', 220),
        ('Cycling', 240),
        ('Yoga / Surya Namaskar', 120),
        ('Swimming', 280),
        ('HIIT / Cardio Workout', 320),
    ]

    class Meta:
        model = ExerciseLog
        fields = ['activity_name', 'duration_mins', 'calories_burned', 'date']
        widgets = {
            'activity_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Morning Brisk Walk',
            }),
            'duration_mins': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '5',
                'step': '5',
                'value': '30',
            }),
            'calories_burned': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'step': '5',
                'value': '150',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }


class WeightLogForm(forms.ModelForm):
    """Form for logging weigh-in progress."""

    class Meta:
        model = WeightLog
        fields = ['weight_kg', 'notes', 'date']
        widgets = {
            'weight_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 67.5',
                'min': '30',
                'max': '200',
                'step': '0.1',
            }),
            'notes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Morning post-workout check-in',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }
