# 🥗 ML-Based Diet & Health Organizer

An intelligent, full-stack nutrition and wellness application built with **Django**, **Scikit-learn**, and **Vanilla CSS/JS**. Calibrated for both global dietary standards (WHO / Mifflin-St Jeor) and authentic Indian nutritional needs (ICMR BMI standards, Vrat/Upvas fasting protocols, and Desi superfoods).

---

## ✨ Key Features

### 1. 🤖 AI-Powered Nutrition & ML Recommendations
* **K-Nearest Neighbors (KNN) Recommender**: Analyzes dynamic remaining calorie and macronutrient deficits to suggest optimal foods.
* **1-Click AI Daily Meal Plan Generator**: Automatically constructs a balanced 4-meal daily schedule (Breakfast, Lunch, Dinner, Snack) calibrated to the user's exact caloric target.
* **1-Click Log Application**: Instantly logs the generated 4-meal plan to the user's daily food journal.

### 2. 🇮🇳 Indian ICMR Standards & Vrat Fasting Intelligence
* **ICMR South Asian BMI Classification**: Supports revised South Asian body composition thresholds (Overweight ≥23, Obese ≥25).
* **🕉️ Vrat / Upvas Fasting Mode**: 1-click toggle filtering ML recommendations exclusively to fasting-compliant foods (*Sabudana, Makhana, Kuttu, Samak Rice, Singhara, Sendha Namak fruits*).
* **Desi Quick-Add Bar**: 1-click logging for daily household staples (*Ghee on Roti, Chaas / Buttermilk, Green Salad, Roasted Makhana*).

### 3. 📊 Daily Health & Habit Tracking
* **Daily Diet Quality Score (0–100)**: Real-time score factoring calorie accuracy, protein compliance, hydration, and dietary fiber.
* **💧 Daily Water Hydration Tracker**: Visual 8-glass counter and volume tracker (250ml per glass).
* **⏳ Intermittent Fasting (IF) Timer**: Live countdown timer for 16:8, 14:10, or 12:12 schedules.
* **🏃 Physical Activity & Net Calories**: Workout logging calculating $$\text{Net Calories} = \text{Food Consumed} - \text{Exercise Burned}$$.
* **⚖️ Side-by-Side Food Comparison Tool**: Interactive comparator for comparing calories, protein, carbs, fat, fiber, and sodium between any two foods.
* **📈 Visual Analytics**: Interactive Chart.js Macronutrient Donut and 7-Day Calorie Trend charts.

### 4. 🎨 Modern & Balanced UI
* **Clean, Humanized Interface**: Focused workflow without visual clutter.
* **🌙 Dark Mode Support**: Theme switcher with persistent `localStorage` memory.
* **🖨️ PDF Summary Export**: Built-in `@media print` stylesheet for clean print and PDF report downloads.

---

## 🛠️ Tech Stack

* **Backend**: Python 3.10+, Django 4.2+
* **Machine Learning**: Scikit-learn (NearestNeighbors, StandardScaler), NumPy, Pandas
* **Frontend**: HTML5, Vanilla CSS3 (Custom Design System with CSS Variables), JavaScript (ES6)
* **Visualizations**: Chart.js
* **Database**: SQLite (Development) / PostgreSQL-ready

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ml-diet-organizer.git
cd ml-diet-organizer
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Database Migrations
```bash
python manage.py migrate
```

### 5. Seed the Indian & Global Foods Database
```bash
python manage.py seed_foods
```

### 6. Run the Development Server
```bash
python manage.py runserver
```

Open your browser and visit: **`http://127.0.0.1:8000/`**

---

## 📁 Project Architecture

```
├── diet_organizer/         # Master Django Project Configuration
│   ├── settings.py         # App configuration & middleware
│   ├── urls.py             # Root URL routing
│   └── wsgi.py             # Web server entrypoint
│
├── dietapp/                # Main Application Package
│   ├── models.py           # Database schema (UserProfile, Food, FoodLog, WaterLog, etc.)
│   ├── views.py            # Business logic and request handlers
│   ├── forms.py            # ModelForms and validation
│   ├── calculations.py     # BMI, BMR, TDEE, ICMR, and Health Score math
│   ├── session_utils.py    # Session profile helpers
│   ├── urls.py             # App-level route definitions
│   └── management/commands/# Custom terminal commands (seed_foods.py)
│
├── ml/
│   └── recommender.py      # KNN ML algorithm & 1-day meal plan generator
│
├── templates/              # HTML templates (base.html, food_tracker.html, planner.html, result.html)
└── static/                 # CSS (style.css) and JavaScript (food_tracker.js)
```

---

## ⚠️ Academic Disclaimer
This project is developed for educational, academic, and portfolio demonstration purposes. Caloric estimates and algorithm suggestions are based on scientific formulas (Mifflin-St Jeor, ICMR guidelines) but do not replace certified clinical dietitian or medical consultations.
## it is largely scalable project the basic structure of project can be expand beyond any college projects limitations by URVAMAHANT 17/08/2026 12:08
---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
