import streamlit as st
import json
from datetime import date, timedelta
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd

# --- Google Sheets setup ---
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

# --- Modern CSS for UI Upgrades ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #7f53ac 0%, #657ced 100%) !important;
    }
    .main .block-container {
        background: #fff;
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 8px 24px rgba(58,58,158,0.14);
        margin-bottom: 2rem;
    }
    h1, h2, h3, .stRadio label { color: #3a3a9e; }
    .stButton>button {
        background-color: #5e4bff !important;
        color: #fff !important;
        border-radius: 12px;
        padding: 0.7em 2.2em;
        font-size: 1.1em;
        font-weight: bold;
        margin-top: 0.6em;
        transition: 0.2s;
        box-shadow: 0 2px 12px rgba(58,58,158,0.07);
    }
    .stButton>button:hover {
        background-color: #3a3a9e !important;
        transform: translateY(-2px) scale(1.03);
        box-shadow: 0 6px 22px rgba(58,58,158,0.18);
    }
    .stTextInput>div>input, .stTextArea>div>textarea {
        border-radius: 8px !important;
        border: 1.5px solid #b7b7e5 !important;
        padding: 0.5em;
        font-size: 1.06em;
        background: #f5f6fb !important;
    }
    .stSelectbox>div, .stDateInput>div>input, .stTimeInput>div>input {
        border-radius: 8px !important;
        background: #f5f6fb !important;
    }
    .st-bx { margin-bottom: 1em; }
    .stat-card {
        background: #f5f6fb;
        border-radius: 12px;
        padding: 1.2em;
        box-shadow: 0 1px 4px rgba(58,58,158,0.09);
        margin-bottom: 1em;
    }
    </style>
""", unsafe_allow_html=True)

# --- App Title ---
st.title("📊 Daily Activity Tracker")
st.caption("Track your daily activities and visualize your productivity")

# --- Columns ---
col1, col2 = st.columns([2, 3])

with col1:
    st.header("Add Activity")
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
    # Autocomplete-like suggestions (clickable)
    matches = [sc for sc in st.session_state.subcategories if subcat.lower() in sc.lower()] if subcat else []
    if matches and subcat:
        st.markdown("**Suggestions:** " + " | ".join([f"`{m}`" for m in matches]))
    comments = st.text_area("Comments", placeholder="Add additional details...")

    # --- Activity Add Button ---
    if st.button("Add Activity", use_container_width=True):
        try:
            worksheet.append_row([
                d.strftime("%Y-%m-%d"), start.strftime("%H:%M"), end.strftime("%H:%M"),
                cat, subcat, comments
            ])
            if subcat and subcat not in st.session_state.subcategories:
                st.session_state.subcategories.append(subcat)
            st.success("✅ Activity added successfully!")
        except Exception as e:
            st.error(f"❌ Error adding activity: {e}")

    # --- Download Data ---
    if st.button("Download All Activities as CSV", use_container_width=True):
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        st.download_button("Download CSV", data=df.to_csv(index=False), file_name="activities.csv", mime="text/csv")

with col2:
    st.header("Visualizations")
    period = st.radio("Select View", ["Daily", "Weekly", "Monthly"], horizontal=True)
    df = None
    try:
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading data: {e}")

    if df is not None and not df.empty:
        df["Date"] = pd.to_datetime(df["Date"])
        df["Duration"] = (
            pd.to_datetime(df["End Time"], format="%H:%M") -
            pd.to_datetime(df["Start Time"], format="%H:%M")
        ).dt.total_seconds() / 60

        # Filter by period
        if period == "Daily":
            view_date = st.date_input("Day", today, key="viz_day")
            filt = df["Date"].dt.date == view_date
            label = view_date.strftime('%b %d, %Y')
        elif period == "Weekly":
            view_week = st.date_input("Any day of week", today, key="viz_week")
            week_num = view_week.isocalendar()[1]
            filt = df["Date"].dt.isocalendar().week == week_num
            label = f"Week {week_num}"
        else:
            view_month = st.date_input("Any day of month", today, key="viz_month")
            filt = df["Date"].dt.month == view_month.month
            label = view_month.strftime('%B %Y')

        sub = df[filt]
        if not sub.empty:
            # --- Productivity Stats Card ---
            st.markdown(f"<div class='stat-card'><b>{label}:</b> Total Tracked: <span style='color:#5e4bff;'>{int(sub['Duration'].sum())} min</span> | <span style='color:#26a144;'>Productive</span>: <b>{int(sub[sub['Category']=='Productive']['Duration'].sum())}</b> min | <span style='color:#e64e2c;'>Not-Productive</span>: <b>{int(sub[sub['Category']=='Not-Productive']['Duration'].sum())}</b> min</div>", unsafe_allow_html=True)

            st.subheader("Category Breakdown")
            st.bar_chart(sub.groupby("Category")["Duration"].sum())

            st.subheader("Sub-Category Breakdown")
            st.bar_chart(sub.groupby("Sub Category")["Duration"].sum())

            # --- Optional Pie Chart ---
            st.subheader("Productive vs Not-Productive (Pie)")
            st.pyplot(sub.groupby("Category")["Duration"].sum().plot.pie(autopct='%1.0f%%', ylabel='').get_figure())
        else:
            st.info("No data for selected period.")
    else:
        st.info("No activity yet.")

# --- End of File ---

