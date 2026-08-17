from django.core.management.base import BaseCommand

from dietapp.data.sample_foods import SAMPLE_FOODS
from dietapp.models import Food


class Command(BaseCommand):
    help = 'Seed the database with Indian staples, desi superfoods, and Vrat items.'

    def handle(self, *args, **options):
        updated_count = 0

        for row in SAMPLE_FOODS:
            (name, serving_size, calories, protein, carbs, fat, fiber, dietary_type,
             is_vrat, is_gf, is_df, sodium, sugar) = row

            Food.objects.update_or_create(
                name=name,
                defaults={
                    'serving_size': serving_size,
                    'calories': calories,
                    'protein': protein,
                    'carbohydrates': carbs,
                    'fat': fat,
                    'fiber': fiber,
                    'dietary_type': dietary_type,
                    'is_vrat_friendly': is_vrat,
                    'is_gluten_free': is_gf,
                    'is_dairy_free': is_df,
                    'sodium_mg': sodium,
                    'sugar_g': sugar,
                },
            )
            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Seed complete: {updated_count} Indian foods synchronized.')
        )
