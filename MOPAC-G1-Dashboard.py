import streamlit as st
import pandas as pd
import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Consultancy POAP",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS Styling for "Aesthetic" Look ---
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        h1 { color: #0f172a; font-family: 'Helvetica Neue', sans-serif; }
        .stDataFrame { border: 1px solid #e2e8f0; border-radius: 0.5rem; overflow: hidden; }
        /* Highlight Total Rows/Cols */
        div[data-testid="stMetricValue"] { font-size: 1.5rem; color: #3b82f6; }
    </style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def get_month_columns(start_year=2025, start_month=7, months_count=25):
    """Generates a list of month keys (e.g., 'Jul 25')"""
    cols = []
    current_date = datetime.date(start_year, start_month, 1)
    for _ in range(months_count):
        cols.append(current_date.strftime("%b '%y"))
        # Move to next month
        if current_date.month == 12:
            current_date = datetime.date(current_date.year + 1, 1, 1)
        else:
            current_date = datetime.date(current_date.year, current_date.month + 1, 1)
    return cols

# --- Initialization ---
# Define columns
all_months = get_month_columns()
phase1_cols = all_months[:12]   # Jul '25 - Jun '26
phase2_cols = all_months[12:]   # Jul '26 - Jul '27

# Initialize Session State for Data Persistence
if 'resource_df' not in st.session_state:
    data = {
        "Resource": ["Sarah Jenkins", "David Chen", "Priya Patel", "Marcus Johnson", "Analyst Pool"],
        "Role": ["Partner", "Engagement Mgr", "Senior Associate", "Associate", "Analyst Support"],
        "Grade": ["L1", "L3", "L4", "L5", "L6"],
    }
    # Initialize all months with 0
    for month in all_months:
        data[month] = [0, 0, 0, 0, 0]
    
    st.session_state.resource_df = pd.DataFrame(data)

if 'deliverables_df' not in st.session_state:
    # Initialize deliverables with empty strings
    st.session_state.deliverables_df = pd.DataFrame(
        [[""] * len(all_months)], 
        columns=all_months, 
        index=["Key Deliverables"]
    )

# --- Header Section ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("Project Phoenix: Resource & Delivery Plan")
    st.caption("Global Transformation Office • July 2025 – July 2027")
with c2:
    st.download_button(
        label="📥 Download Plan as CSV",
        data=st.session_state.resource_df.to_csv(index=False),
        file_name="consultancy_poap.csv",
        mime="text/csv",
        use_container_width=True
    )

# --- Tabs for Phases ---
tab1, tab2 = st.tabs(["Phase 1: Jul '25 - Jun '26", "Phase 2: Jul '26 - Jul '27"])

def render_phase_view(cols, phase_name):
    """Renders the grid and stats for a specific phase"""
    
    # 1. Prepare Data for Display
    # We filter the main DF to just show current phase columns + Metadata
    display_cols = ["Resource", "Role"] + cols
    df_view = st.session_state.resource_df[display_cols].copy()
    
    # Calculate Row Totals (Total Days for this Phase)
    df_view["Phase Total"] = df_view[cols].sum(axis=1)

    # 2. Styling (The Heatmap Effect)
    # We apply a gradient only to the month columns
    styled_df = (df_view.style
                 .background_gradient(cmap="Blues", subset=cols, vmin=0, vmax=22)
                 .format(precision=0)
                 .set_properties(**{'text-align': 'center'}, subset=cols)
                 .set_properties(**{'font-weight': 'bold'}, subset=["Phase Total"]))

    # 3. Render Editor
    st.subheader(f"Resource Allocation - {phase_name}")
    
    # st.data_editor allows the user to change values. 
    # We capture the edits and update the main session_state.
    edited_df = st.data_editor(
        styled_df,
        column_config={
            "Resource": st.column_config.TextColumn(disabled=True),
            "Role": st.column_config.TextColumn(disabled=True),
            "Phase Total": st.column_config.NumberColumn(disabled=True, help="Total days in this phase"),
        },
        use_container_width=True,
        height=250,
        key=f"editor_{phase_name}" # Unique key for each tab
    )

    # 4. Update State Logic
    # If the user edits the grid, we need to sync those changes back to the main 'resource_df'
    # Note: Streamlit data_editor returns the *entire* edited dataframe.
    if not edited_df.equals(df_view):
        # Update only the numeric columns for this phase in the main state
        st.session_state.resource_df.update(edited_df[cols])
        st.rerun() # Rerun to update totals immediately

    # 5. Monthly Totals Calculation
    st.divider()
    
    # Calculate Sums per month
    totals = st.session_state.resource_df[cols].sum()
    
    # Display Deliverables
    st.subheader("Key Deliverables & Milestones")
    
    # Transpose Deliverables for better editing experience (Rows = Months)
    del_view = st.session_state.deliverables_df[cols].T
    del_view.columns = ["Deliverable Description"]
    
    edited_deliverables = st.data_editor(
        del_view,
        use_container_width=True,
        num_rows="fixed",
        key=f"del_editor_{phase_name}"
    )
    
    # Sync Deliverables back to state
    if not edited_deliverables.equals(del_view):
        # Transpose back to save
        updated_del = edited_deliverables.T
        st.session_state.deliverables_df.update(updated_del)

    # 6. Quick Stats for this Phase
    st.markdown("### Phase Summary")
    sc1, sc2, sc3 = st.columns(3)
    
    total_days_phase = totals.sum()
    busy_month = totals.idxmax()
    busy_count = totals.max()
    
    sc1.metric("Total Days (This Phase)", f"{total_days_phase}")
    sc2.metric("Peak Activity Month", f"{busy_month}", f"{busy_count} days")
    sc3.metric("Avg. Burn Rate", f"{total_days_phase / len(cols):.1f} days/mo")


# --- Render Content based on active tab ---
with tab1:
    render_phase_view(phase1_cols, "Year 1")

with tab2:
    render_phase_view(phase2_cols, "Year 2")

# --- Global Stats Footer ---
st.markdown("---")
grand_total = st.session_state.resource_df[all_months].sum().sum()
st.info(f"**Grand Total Project Effort (2025-2027):** {grand_total} Days")