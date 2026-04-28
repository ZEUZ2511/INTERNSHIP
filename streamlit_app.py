# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np

# ------------------------------------------------------------
# Cached data generation (prevents rerunning on every click)
# ------------------------------------------------------------
@st.cache_data
def generate_sample_users(n=500):
    """Create synthetic user data when no file is uploaded."""
    np.random.seed(42)
    ages = np.random.choice(
        [15, 20, 30, 42, 60], size=n,
        p=[0.2, 0.3, 0.25, 0.15, 0.1]
    )
    genders = np.random.choice(['Male', 'Female', 'Other'], size=n, p=[0.48, 0.48, 0.04])
    return pd.DataFrame({
        'UserID': [f'U{i:04d}' for i in range(1, n+1)],
        'Age': ages,
        'Gender': genders
    })

def get_age_group(age):
    if age <= 18:   return 'Teen (13-18)'
    elif age <= 25: return 'Young Adult (19-25)'
    elif age <= 35: return 'Adult (26-35)'
    elif age <= 50: return 'Professional (36-50)'
    else:           return 'Senior (50+)'

def generate_enrollment_data(users):
    """Create courses and enrollment records based on user age groups."""
    courses = pd.DataFrame([
        {'CourseID': 'PY101',  'CourseName': 'Python Programming',       'Category': 'Programming',    'Price': 49,  'Level': 'Beginner',     'Rating': 4.5},
        {'CourseID': 'PY201',  'CourseName': 'Advanced Python',          'Category': 'Programming',    'Price': 99,  'Level': 'Intermediate', 'Rating': 4.7},
        {'CourseID': 'DS101',  'CourseName': 'Data Science Fundamentals','Category': 'Data Science',   'Price': 79,  'Level': 'Beginner',     'Rating': 4.8},
        {'CourseID': 'ML201',  'CourseName': 'Machine Learning',         'Category': 'Data Science',   'Price': 149, 'Level': 'Advanced',     'Rating': 4.9},
        {'CourseID': 'WEB101', 'CourseName': 'Web Development',          'Category': 'Web Development','Price': 59,  'Level': 'Beginner',     'Rating': 4.6},
        {'CourseID': 'SQL101', 'CourseName': 'SQL Mastery',              'Category': 'Database',       'Price': 39,  'Level': 'Beginner',     'Rating': 4.5},
    ])

    # Age group preferences
    preferences = {
        'Teen (13-18)':         ['Programming', 'Web Development'],
        'Young Adult (19-25)':  ['Programming', 'Data Science', 'Web Development'],
        'Adult (26-35)':        ['Data Science', 'Programming', 'Database'],
        'Professional (36-50)': ['Data Science', 'Database', 'Programming'],
        'Senior (50+)':         ['Programming', 'Database'],
    }

    users['AgeGroup'] = users['Age'].apply(get_age_group)
    rows = []

    for _, course in courses.iterrows():
        base = 300
        if course['Price'] < 60:    base = int(base * 1.5)
        elif course['Price'] > 100: base = int(base * 0.7)
        if course['Level'] == 'Beginner':  base = int(base * 1.3)
        elif course['Level'] == 'Advanced': base = int(base * 0.6)

        for age_group, preferred in preferences.items():
            if course['Category'] not in preferred:
                continue
            age_users = users[users['AgeGroup'] == age_group]
            n = min(base, len(age_users))
            if n == 0:
                continue
            selected = age_users.sample(n=n, replace=False)
            for _, student in selected.iterrows():
                discount = np.random.uniform(0, 0.3)
                rows.append({
                    'UserID':       student['UserID'],
                    'UserAge':      student['Age'],
                    'UserGender':   student['Gender'],
                    'UserAgeGroup': student['AgeGroup'],
                    'CourseID':     course['CourseID'],
                    'CourseName':   course['CourseName'],
                    'Category':     course['Category'],
                    'Level':        course['Level'],
                    'OriginalPrice':course['Price'],
                    'Discount':     round(discount * 100, 1),
                    'PaidPrice':    round(course['Price'] * (1 - discount), 2),
                })

    enrollment = pd.DataFrame(rows)

    # Summary tables
    course_summary = enrollment.groupby('CourseID').agg(
        CourseName   = ('CourseName',    'first'),
        Category     = ('Category',      'first'),
        Level        = ('Level',         'first'),
        Price        = ('OriginalPrice', 'first'),
        Enrollments  = ('UserID',        'count'),
        Revenue      = ('PaidPrice',     'sum'),
        AvgDiscount  = ('Discount',      'mean'),
    ).reset_index()

    age_summary = enrollment.groupby('UserAgeGroup').agg(
        Enrollments  = ('UserID',    'count'),
        Revenue      = ('PaidPrice', 'sum'),
        AvgDiscount  = ('Discount',  'mean'),
    ).reset_index().rename(columns={'UserAgeGroup': 'AgeGroup'})

    category_summary = enrollment.groupby('Category').agg(
        Enrollments  = ('UserID',    'count'),
        Revenue      = ('PaidPrice', 'sum'),
    ).reset_index()

    return enrollment, course_summary, age_summary, category_summary

# ------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------
st.set_page_config(page_title="EduPro Dashboard", layout="wide")
st.title("📊 EduPro – Course Enrollment Analytics")
st.markdown("Interactive dashboard built from synthetic enrollment data.")

# Sidebar – data source selection
st.sidebar.header("Data Source")
uploaded_file = st.sidebar.file_uploader("Upload your own Excel file (must contain UserID, Age, Gender)", type=["xlsx"])

if uploaded_file is not None:
    try:
        users_raw = pd.read_excel(uploaded_file, sheet_name=0)
        # Required columns
        required = ['UserID', 'Age']
        missing = [col for col in required if col not in users_raw.columns]
        if missing:
            st.sidebar.error(f"Missing columns: {missing}. Using sample data instead.")
            users = generate_sample_users()
        else:
            # Clean and validate
            users_raw.columns = users_raw.columns.str.strip()
            users_raw['Age'] = pd.to_numeric(users_raw['Age'], errors='coerce')
            users_raw = users_raw.dropna(subset=['UserID', 'Age'])
            if 'Gender' not in users_raw.columns:
                users_raw['Gender'] = np.random.choice(['Male','Female','Other'], size=len(users_raw))
            users = users_raw[['UserID', 'Age', 'Gender']].copy()
            st.sidebar.success(f"Loaded {len(users)} users from your file.")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")
        users = generate_sample_users()
else:
    users = generate_sample_users()
    st.sidebar.info("Using synthetic user data. Upload an Excel file to use your own.")

# Generate enrollment data
with st.spinner("Generating enrollments..."):
    enrollment, course_summary, age_summary, category_summary = generate_enrollment_data(users)

# ------------------------------------------------------------
# Dashboard Layout
# ------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Enrollments", f"{len(enrollment):,}")
col2.metric("Unique Courses", course_summary['CourseID'].nunique())
col3.metric("Total Revenue", f"${enrollment['PaidPrice'].sum():,.2f}")
col4.metric("Avg Discount", f"{enrollment['Discount'].mean():.1f}%")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📈 Revenue by Category", "👥 Age Group Analysis", "🏆 Course Performance", "📋 Raw Data"])

with tab1:
    st.subheader("Revenue & Enrollments by Category")
    col_a, col_b = st.columns(2)
    with col_a:
        st.bar_chart(category_summary.set_index('Category')['Revenue'])
    with col_b:
        st.bar_chart(category_summary.set_index('Category')['Enrollments'])

with tab2:
    st.subheader("Age Group Breakdown")
    col_c, col_d = st.columns(2)
    with col_c:
        st.bar_chart(age_summary.set_index('AgeGroup')['Enrollments'])
    with col_d:
        st.bar_chart(age_summary.set_index('AgeGroup')['Revenue'])
    st.dataframe(age_summary, use_container_width=True)

with tab3:
    st.subheader("Course Enrollment & Revenue")
    # Sortable dataframe
    st.dataframe(
        course_summary.sort_values('Revenue', ascending=False),
        column_config={
            "Revenue": st.column_config.NumberColumn(format="$%.2f"),
            "Price": st.column_config.NumberColumn(format="$%.2f"),
            "AvgDiscount": st.column_config.NumberColumn(format="%.1f%%"),
        },
        use_container_width=True
    )
    # Highlight top courses
    top_courses = course_summary.nlargest(3, 'Enrollments')['CourseName'].tolist()
    st.success(f"🏅 Top 3 courses by enrollments: {', '.join(top_courses)}")

with tab4:
    st.subheader("Enrollment Details (sample)")
    st.dataframe(enrollment.head(100), use_container_width=True)
    st.download_button(
        label="Download full enrollment data (CSV)",
        data=enrollment.to_csv(index=False).encode('utf-8'),
        file_name='enrollment_details.csv',
        mime='text/csv'
    )