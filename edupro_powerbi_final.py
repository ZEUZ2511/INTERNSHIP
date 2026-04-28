# ============================================================
# EDUPRO – DATA SOURCE FOR POWER BI
# Paste into: Power BI → Get Data → Python script
#
# IMPORTANT: Update the file path on line 16 to where
# your EDU.xlsx file is saved on your computer.
# ============================================================

import pandas as pd
import numpy as np

np.random.seed(42)

# ── STEP 1: Load users ─────────────────────────────────────
users = pd.read_excel(r'D:\INTERNSHIP\EDU.xlsx', sheet_name=0)
users.columns = users.columns.str.strip()
users = users.dropna(subset=['UserID', 'Age'])
users['Age'] = pd.to_numeric(users['Age'], errors='coerce')
users = users.dropna(subset=['Age'])

# Assign age groups
def get_age_group(age):
    if age <= 18:   return 'Teen (13-18)'
    elif age <= 25: return 'Young Adult (19-25)'
    elif age <= 35: return 'Adult (26-35)'
    elif age <= 50: return 'Professional (36-50)'
    else:           return 'Senior (50+)'

users['AgeGroup'] = users['Age'].apply(get_age_group)


# ── STEP 2: Define courses ──────────────────────────────────
courses = pd.DataFrame([
    {'CourseID': 'PY101',  'CourseName': 'Python Programming',       'Category': 'Programming',    'Price': 49,  'Level': 'Beginner',     'Rating': 4.5},
    {'CourseID': 'PY201',  'CourseName': 'Advanced Python',          'Category': 'Programming',    'Price': 99,  'Level': 'Intermediate', 'Rating': 4.7},
    {'CourseID': 'DS101',  'CourseName': 'Data Science Fundamentals','Category': 'Data Science',   'Price': 79,  'Level': 'Beginner',     'Rating': 4.8},
    {'CourseID': 'ML201',  'CourseName': 'Machine Learning',         'Category': 'Data Science',   'Price': 149, 'Level': 'Advanced',     'Rating': 4.9},
    {'CourseID': 'WEB101', 'CourseName': 'Web Development',          'Category': 'Web Development','Price': 59,  'Level': 'Beginner',     'Rating': 4.6},
    {'CourseID': 'SQL101', 'CourseName': 'SQL Mastery',              'Category': 'Database',       'Price': 39,  'Level': 'Beginner',     'Rating': 4.5},
])


# ── STEP 3: Generate enrollments ───────────────────────────

preferences = {
    'Teen (13-18)':         ['Programming', 'Web Development'],
    'Young Adult (19-25)':  ['Programming', 'Data Science', 'Web Development'],
    'Adult (26-35)':        ['Data Science', 'Programming', 'Database'],
    'Professional (36-50)': ['Data Science', 'Database', 'Programming'],
    'Senior (50+)':         ['Programming', 'Database'],
}

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

# Power BI picks this up as the "Enrollment_Details" table
Enrollment_Details = pd.DataFrame(rows)


# ── STEP 4: Summary tables ─────────────────────────────────
# Power BI picks each of these up as a separate table

Course_Summary = Enrollment_Details.groupby('CourseID').agg(
    CourseName   = ('CourseName',    'first'),
    Category     = ('Category',      'first'),
    Level        = ('Level',         'first'),
    Price        = ('OriginalPrice', 'first'),
    Enrollments  = ('UserID',        'count'),
    Revenue      = ('PaidPrice',     'sum'),
    AvgDiscount  = ('Discount',      'mean'),
).reset_index()

Age_Summary = Enrollment_Details.groupby('UserAgeGroup').agg(
    Enrollments  = ('UserID',    'count'),
    Revenue      = ('PaidPrice', 'sum'),
    AvgDiscount  = ('Discount',  'mean'),
).reset_index().rename(columns={'UserAgeGroup': 'AgeGroup'})

Category_Summary = Enrollment_Details.groupby('Category').agg(
    Enrollments  = ('UserID',    'count'),
    Revenue      = ('PaidPrice', 'sum'),
).reset_index()

