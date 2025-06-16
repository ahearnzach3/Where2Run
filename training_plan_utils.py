import os
import json
from datetime import date, timedelta

def load_training_plan(filename):
    # Safely build the path to the 'plans' folder
    base_path = os.path.join(os.path.dirname(__file__), "plans")
    filepath = os.path.join(base_path, filename)
    with open(filepath, 'r') as f:
        return json.load(f)

def get_today_plan(plan_data, plan_start_date):
    today = date.today()
    days_since_start = (today - plan_start_date).days

    if days_since_start < 0:
        return "Plan hasn't started yet", None, None

    week_idx = days_since_start // 7
    day_idx = days_since_start % 7

    if week_idx >= len(plan_data):
        return "Plan completed", None, None

    today_entry = plan_data[week_idx]
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_name = day_names[day_idx]

    daily_plan = today_entry.get(day_name, "Rest")

    return f"Week {week_idx + 1}, {day_name}: {daily_plan}", daily_plan, (week_idx + 1, day_name)
