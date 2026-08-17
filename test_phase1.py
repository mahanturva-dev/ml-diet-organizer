"""Quick unit tests for Phase 1 calculations."""

from dietapp.calculations import (
    calculate_bmi,
    calculate_bmr,
    calculate_calorie_target,
    calculate_daily_calories,
)


def test_bmi_normal():
    bmi, category = calculate_bmi(70, 175)
    assert 22 <= bmi <= 23
    assert category == 'Normal weight'


def test_bmr_and_calories():
    bmr = calculate_bmr(70, 175, 25)
    daily = calculate_daily_calories(bmr, 'moderate')
    target_gain = calculate_calorie_target(daily, 'weight_gain')
    target_loss = calculate_calorie_target(daily, 'weight_loss')

    assert bmr > 1400
    assert daily > bmr
    assert target_gain == daily + 500
    assert target_loss == daily - 500


if __name__ == '__main__':
    test_bmi_normal()
    test_bmr_and_calories()
    print('All Phase 1 calculation tests passed.')
