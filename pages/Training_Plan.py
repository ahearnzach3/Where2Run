import streamlit as st
from datetime import date, timedelta
import training_plan_utils as tp

st.set_page_config(page_title="📆 Training Plans")

st.title("📆 Marathon Training Plan")
st.markdown("Build your training plan leading up to race day.")

# --- 1. Plan Type Selection ---
plan_type = st.selectbox("Choose your goal distance:", ["5K", "10K", "Half Marathon", "Marathon"])

# --- 2. Plan Options (Filtered) ---
available_plans = []

if plan_type == "Marathon":
    available_plans = [{
        "name": "Hal Higdon Novice 1",
        "description": "Ideal for first-time marathoners or runners getting back into training. Focuses on gradual mileage buildup with 4 weekly runs and a long run on weekends.",
        "filename": "plans/hal_higdon_novice1.json",
        "image_url": "https://www.halhigdon.com/wp-content/uploads/2019/12/NOVICE-1-768x994.png"
    }]
else:
    st.warning(f"🚧 No training plans yet for {plan_type}. Check back soon!")

# --- 3. Plan Selection ---
if available_plans:
    selected_plan = st.radio("Select a training plan:", [p["name"] for p in available_plans])
    plan_info = next(p for p in available_plans if p["name"] == selected_plan)

    st.image(plan_info["image_url"], width=300)
    st.markdown(f"**{plan_info['name']}**")
    st.caption(plan_info["description"])

    # --- 4. Plan Start Date ---
    start_date = st.date_input("Select your training start date:", value=date.today())
    race_day = start_date + timedelta(weeks=18)

    # --- 5. Save to session state ---
    if st.button("📌 Save Training Plan"):
        st.session_state.selected_plan_name = selected_plan
        st.session_state.selected_plan_path = plan_info["filename"].split("/")[-1]
        st.session_state.training_start_date = start_date
        st.success("✅ Training plan saved!")

# --- 6. Show Plan Status if Saved ---
if "selected_plan_name" in st.session_state:
    st.markdown("---")
    st.subheader("📅 Your Training Plan")
    st.markdown(f"**Plan:** {st.session_state.selected_plan_name}")
    st.markdown(f"**Start Date:** {st.session_state.training_start_date}")
    st.markdown(f"**Race Day:** {st.session_state.training_start_date + timedelta(weeks=18)}")

    days_left = (st.session_state.training_start_date + timedelta(weeks=18) - date.today()).days
    days_passed = (date.today() - st.session_state.training_start_date).days
    total_days = 18 * 7

    st.progress(min(days_passed / total_days, 1.0))
    st.info(f"⏳ {max(days_left, 0)} days left until race day!")

    # Optional: Show today's workout
    plan_data = tp.load_training_plan(st.session_state.selected_plan_path)
    today_summary, today_entry, week_number = tp.get_today_plan(plan_data, st.session_state.training_start_date)
    st.markdown(f"🏃 **Today’s Workout:** {today_summary}")
