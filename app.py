import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -----------------------------
# Load Data
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("Palo Alto Networks1.csv")
    return df

df = load_data()

st.title("📊 Employee Engagement & Burnout Analytics")

# -----------------------------
# Sidebar Filters (User Capabilities)
# -----------------------------
st.sidebar.header("Filters")

department = st.sidebar.multiselect(
    "Select Department",
    options=df['Department'].unique(),
    default=df['Department'].unique()
)

job_role = st.sidebar.multiselect(
    "Select Job Role",
    options=df['JobRole'].unique(),
    default=df['JobRole'].unique()
)

overtime_filter = st.sidebar.selectbox(
    "Overtime",
    ["All", "Yes", "No"]
)

engagement_threshold = st.sidebar.slider(
    "Engagement Threshold",
    min_value=0.0, max_value=1.0, value=0.5
)

tenure_range = st.sidebar.slider(
    "Years at Company",
    int(df['YearsAtCompany'].min()),
    int(df['YearsAtCompany'].max()),
    (0, int(df['YearsAtCompany'].max()))
)

# -----------------------------
# Apply Filters
# -----------------------------
filtered_df = df[
    (df['Department'].isin(department)) &
    (df['JobRole'].isin(job_role)) &
    (df['YearsAtCompany'].between(tenure_range[0], tenure_range[1]))
]

if overtime_filter != "All":
    filtered_df = filtered_df[filtered_df['OverTime'] == overtime_filter]

# -----------------------------
# 1. Engagement Health Overview
# -----------------------------
st.header("📈 Engagement Health Overview")

avg_engagement = filtered_df['EngagementScore'].mean()

col1, col2 = st.columns(2)

with col1:
    st.metric("Organization Engagement Score", round(avg_engagement, 3))

with col2:
    fig = px.histogram(
        filtered_df,
        x="EngagementScore",
        nbins=20,
        title="Engagement Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

# Satisfaction Distribution
st.subheader("Satisfaction Breakdown")

sat_cols = [
    'JobSatisfaction',
    'EnvironmentSatisfaction',
    'RelationshipSatisfaction'
]

sat_df = filtered_df[sat_cols].mean().reset_index()
sat_df.columns = ['Metric', 'Score']

fig_sat = px.bar(sat_df, x='Metric', y='Score', title="Average Satisfaction Scores")
st.plotly_chart(fig_sat, use_container_width=True)

# -----------------------------
# 2. Burnout Risk Dashboard
# -----------------------------
st.header("🔥 Burnout Risk Dashboard")

burnout_counts = filtered_df['BurnoutRisk'].value_counts().reset_index()
burnout_counts.columns = ['Risk Level', 'Count']

fig_burnout = px.pie(
    burnout_counts,
    names='Risk Level',
    values='Count',
    title="Burnout Risk Distribution"
)
st.plotly_chart(fig_burnout, use_container_width=True)

# Overtime vs WorkLifeBalance
fig_ot = px.box(
    filtered_df,
    x="OverTime",
    y="WorkLifeBalance",
    title="Overtime vs Work-Life Balance"
)
st.plotly_chart(fig_ot, use_container_width=True)

# -----------------------------
# 3. Role & Career Stage Analysis
# -----------------------------
st.header("📊 Role & Career Stage Analysis")

# Job Role vs Engagement
role_engagement = filtered_df.groupby('JobRole', as_index=False)['EngagementScore'].mean()

fig_role = px.bar(
    role_engagement,
    x="JobRole",
    y="EngagementScore",
    title="Engagement by Job Role"
)
st.plotly_chart(fig_role, use_container_width=True)

# Job Level
level_engagement = filtered_df.groupby('JobLevel', as_index=False)['EngagementScore'].mean()

fig_level = px.line(
    level_engagement,
    x="JobLevel",
    y="EngagementScore",
    markers=True,
    title="Engagement by Job Level"
)
st.plotly_chart(fig_level, use_container_width=True)

# Tenure vs Engagement
tenure_engagement = filtered_df.groupby('YearsAtCompany', as_index=False)['EngagementScore'].mean()

fig_tenure = px.line(
    tenure_engagement,
    x="YearsAtCompany",
    y="EngagementScore",
    title="Tenure vs Engagement"
)
st.plotly_chart(fig_tenure, use_container_width=True)

# -----------------------------
# 4. Manager Action Panel
# -----------------------------
st.header("⚠️ Manager Action Panel")

# ------------------
# Color Function
# ------------------
def color_scale(val, q1, q3):
    if val >= q3:
        return 'background-color: red; color: white'
    elif val >= q1:
        return 'background-color: orange'
    else:
        return 'background-color: green; color: white'

# -----------------------------
# Low Engagement Alerts
# -----------------------------
st.subheader("🔴 Low Engagement Alerts")

low_engagement_df = filtered_df[
    filtered_df['EngagementScore'] < engagement_threshold
]

low_summary = low_engagement_df.groupby(
    ['Department', 'JobRole'],
    as_index=False
).agg(
    Low_Engagement_Count=('EngagementScore', 'count'),
    Avg_Engagement=('EngagementScore', 'mean')
)

# Sort ASCENDING
low_summary = low_summary.sort_values(by='Low_Engagement_Count', ascending=True)

# Quantiles for coloring
q1_low = low_summary['Low_Engagement_Count'].quantile(0.5)
q3_low = low_summary['Low_Engagement_Count'].quantile(0.75)

# Apply styling
styled_low = low_summary.style.applymap(
    lambda x: color_scale(x, q1_low, q3_low),
    subset=['Low_Engagement_Count']
)

st.dataframe(styled_low, hide_index=True)

# -----------------------------
# Priority Intervention Areas
# -----------------------------
st.subheader("🟠 Priority Intervention Areas")

priority_df = filtered_df.groupby('Department', as_index=False).agg(
    Avg_Engagement=('EngagementScore', 'mean'),
    High_Risk_Count=('BurnoutRisk', lambda x: (x == 'High').sum())
)

# Priority Score Calculation
priority_df['PriorityScore'] = (
    (1 - priority_df['Avg_Engagement']) * 0.6 +
    (priority_df['High_Risk_Count'] / priority_df['High_Risk_Count'].max()) * 0.4
)

# Sort ASCENDING
priority_df = priority_df.sort_values(by='PriorityScore', ascending=True)

# Quantiles for coloring
q1_pr = priority_df['PriorityScore'].quantile(0.5)
q3_pr = priority_df['PriorityScore'].quantile(0.75)

# Apply styling
styled_priority = priority_df.style.applymap(
    lambda x: color_scale(x, q1_pr, q3_pr),
    subset=['PriorityScore']
)

st.dataframe(styled_priority, hide_index=True)

# -----------------------------
# Visualization (Optional)
# -----------------------------
import plotly.express as px

fig_priority = px.bar(
    priority_df,
    x='Department',
    y='PriorityScore',
    color='PriorityScore',
    title="Priority Intervention Ranking"
)

st.plotly_chart(fig_priority, use_container_width=True)