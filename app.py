import streamlit as st
import json
from datetime import date, timedelta
from google.oauth2.service_account import Credentials
import gspread

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

creds_dict = json.loads(st.secrets["gcp_service_account"])
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

sheet_url = st.secrets["sheet_url"]
sh = client.open_by_url(sheet_url)
worksheet = sh.sheet1


# --- CSS for Modern Look ---
st.markdown("""
    <style>
    /* Card style */
    .stApp {background: linear-gradient(135deg, #7f53ac 0%, #657ced 100%);}
    .main .block-container {background: #fff;border-radius: 12px;padding: 2rem;box-shadow: 0 8px 24px rgba(58,58,158,0.1);}
    .stButton>button {background-color: #5e4bff;color: white;border-radius: 6px;padding: 0.5em 2em;}
    .stTextInput>div>input, .stTextArea>div>textarea {border-radius: 6px;}
    .stSelectbox>div {border-radius: 6px;}
    </style>
""", unsafe_allow_html=True)

st.title("📊 Daily Activity Tracker")
st.caption("Track your daily activities and visualize your productivity")

col1, col2 = st.columns([2, 3])
with col1:
    st.header("Add Activity")
    # Input fields
    today = date.today()
    d = st.date_input("Date", today)
    start = st.time_input("Start Time", step=timedelta(minutes=1))
    end = st.time_input("End Time", step=timedelta(minutes=1))
    cat = st.selectbox("Category", ["Productive", "Not-Productive"])
    default_subcategories = [
        "Academic Study", "Read Book", "Smoke", "Household Chores", "Daily Essentials",
        "Sleep", "Relationship - Family", "Relationship - Friends", "Priyanka", "Workout",
        "Cooking", "Meditation", "Journaling", "Productivity Hacks", "Resting", "Random Work"
    ]
    if "subcategories" not in st.session_state:
        st.session_state.subcategories = default_subcategories
    subcat = st.text_input("Sub Category", placeholder="Type or add new sub-category...")
    # Show autocomplete as suggestions
    matches = [sc for sc in st.session_state.subcategories if subcat.lower() in sc.lower()] if subcat else []
    if matches and subcat:
        st.write("Suggestions:", ", ".join(matches))
    comments = st.text_area("Comments", placeholder="Add additional details...")

    if st.button("Add Activity"):
        if worksheet is not None:
            worksheet.append_row([
                d.strftime("%Y-%m-%d"), start.strftime("%H:%M"), end.strftime("%H:%M"),
                cat, subcat, comments
            ])
            if subcat and subcat not in st.session_state.subcategories:
                st.session_state.subcategories.append(subcat)
            st.success("Activity added successfully!")
        else:
            st.error("Please provide a valid Google Sheet URL and credentials.")

with col2:
    st.header("Visualizations")
    period = st.radio("Select View", ["Daily", "Weekly", "Monthly"], horizontal=True)
    df = None
    if worksheet is not None:
        import pandas as pd
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
    if df is not None and not df.empty:
        df["Date"] = pd.to_datetime(df["Date"])
        df["Duration"] = (
            pd.to_datetime(df["End Time"], format="%H:%M") -
            pd.to_datetime(df["Start Time"], format="%H:%M")
        ).dt.total_seconds() / 60
        if period == "Daily":
            view_date = st.date_input("Day", today, key="viz_day")
            filt = df["Date"].dt.date == view_date
        elif period == "Weekly":
            view_week = st.date_input("Any day of week", today, key="viz_week")
            week_num = view_week.isocalendar()[1]
            filt = df["Date"].dt.isocalendar().week == week_num
        else:
            view_month = st.date_input("Any day of month", today, key="viz_month")
            filt = df["Date"].dt.month == view_month.month
        sub = df[filt]
        if not sub.empty:
            st.subheader("Category Breakdown")
            st.bar_chart(sub.groupby("Category")["Duration"].sum())
            st.subheader("Sub-Category Breakdown")
            st.bar_chart(sub.groupby("Sub-Category")["Duration"].sum())
        else:
            st.info("No data for selected period.")
    else:
        st.info("No activity yet.")

