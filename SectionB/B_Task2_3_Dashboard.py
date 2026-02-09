import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk
import streamlit as st
import seaborn as sns
import os

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(
    page_title="Taxi Claims Dashboard",
    layout="wide"
)

st.title("Taxi Claims Dashboard (Jan–Sep 2015)")

# ----------------------------
# Load Data
# ----------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(current_dir, "cleaned_taxi_data.csv")
df = pd.read_csv(CSV_PATH)

# ----------------------------
# Styling
# ----------------------------
plt.style.use("default")

st.markdown(
    """
    <style>
    .content {
        font-size: 16px;
        text-align: justify;
    }

    .caption {
        font-size: 16px;
        text-align: center;
        margin-bottom: 50px;       
    }
    </style>
    """,
    unsafe_allow_html=True
)

FIG_FONTSIZE = 8
FIG_COLOUR = "black"

# ----------------------------
# Preprocessing
# ----------------------------
df["start_datetime"] = pd.to_datetime(df["start_datetime"])
df["month"] = df["start_datetime"].dt.to_period("M").dt.to_timestamp()
df["day_of_week"] = df["start_datetime"].dt.day_name()
df["hour"] = df["start_datetime"].dt.hour

min_dt = df["start_datetime"].min().to_pydatetime()
max_dt = df["start_datetime"].max().to_pydatetime()

day_order = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]
df["day_of_week"] = pd.Categorical(
    df["day_of_week"], categories=day_order, ordered=True
)

# ----------------------------
# Sidebar Filters
# ----------------------------
st.sidebar.title("Filters")

# --- Date ---
date_range = st.sidebar.date_input(
    "Date Range",
    value=(
        df["start_datetime"].dt.date.min(),
        df["start_datetime"].dt.date.max()
    )
)

# --- Hour of Day ---
hour_range = st.sidebar.slider(
    "Time of Day",
    min_value=0,
    max_value=23,
    value=(0, 23),
    format="%02d:00"
)

# --- Division Filter ---
top_10_divisions = (
    df["division_code"]
    .value_counts()
    .head(10)
    .index
    .tolist()
)

division_filter = st.sidebar.multiselect(
    "Division (Top 10)",
    top_10_divisions
)

# --- Day of Week Filter ---
weekday_filter = st.sidebar.multiselect(
    "Day of Week",
    day_order,
    default=day_order
)

# ----------------------------
# Apply Filters
# ----------------------------
filtered_df = df.copy()

# Date filter
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df["start_datetime"].dt.date >= start_date) &
        (filtered_df["start_datetime"].dt.date <= end_date)
    ]

# Time filter
filtered_df = filtered_df[
    filtered_df["hour"].between(hour_range[0], hour_range[1])
]

# Division filter
if division_filter:
    filtered_df = filtered_df[
        filtered_df["division_code"].isin(division_filter)
    ]

# Weekday filter
if weekday_filter:
    filtered_df = filtered_df[
        filtered_df["day_of_week"].isin(weekday_filter)
    ]

# ----------------------------
# Tabs
# ----------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Overview",
    "⏰ Ride Patterns",
    "🏢 Division Analysis",
    "🗺️ Geospatial Analysis"    
])

# ============================
# TAB 1 — OVERVIEW
# ============================
with tab1:
    st.subheader("Total Cost, Trips & Average Fare")
    message_1 = """
    <div class="content">
    While total taxi expenditure shows noticeable fluctuations over time, there is no clear evidence of a sustained increase. 
    Analysis indicates that these fluctuations are primarily driven by changes in the number of taxi trips taken by officers rather than changes in the average cost per trip. 
    Although average cost per trip exhibits minor variation, these changes are insufficient to explain the magnitude of variation observed in total taxi expenditure. 
    <br><br>
    This suggests that taxi usage volume, rather than pricing, is the dominant factor influencing total costs.
    <br><br><br>
    </div>
    """
    st.markdown(message_1, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Trips", len(filtered_df))    
    col2.metric("Total Cost", f"${filtered_df['total_fare'].sum():,.2f}")
    col3.metric("Avg Cost / Trip", f"${filtered_df['total_fare'].mean():.2f}")

    monthly_cost = filtered_df.groupby("month")["total_fare"].sum().reset_index(name="Total Fare ($)")
    monthly_trips = filtered_df.groupby("month").size().reset_index(name="Num of Trips")
    avg_cost = filtered_df.groupby("month")["total_fare"].mean().reset_index(name="Average Fare ($)")

    st.line_chart(monthly_cost, x="month", y="Total Fare ($)")
    st.line_chart(monthly_trips, x="month", y="Num of Trips")
    st.line_chart(avg_cost, x="month", y="Average Fare ($)")

# ============================
# TAB 2 — RIDE PATTERNS
# ============================
with tab2:
    st.subheader("Taxi Rides by Day & Hour")
    message_2 = """
    <div class="content">
    From the table and heatmap, it can be observed that rides are mostly concentrated during weekdays.
    <br><br>

    **Peak timing identified:**
    - Midnight: 00:00 – 04:00  
    - Afternoon: 12:00 – 15:00  
    - Evening: 18:00 – 20:00

    <br>

    **🔎Possible cost reduction strategy:**  
    Introduce shuttle services during late-night hours to reduce taxi usage.
    <br>
    </div>
    """

    st.markdown(message_2, unsafe_allow_html=True)
    st.write("\n\n\n")

    rides = (
        filtered_df
        .groupby(["day_of_week", "hour"])
        .size()
        .reset_index(name="rides")
    )

    rides_by_day = (
        filtered_df
        .groupby("day_of_week")
        .size()
        .reset_index(name="Number of Rides")
    )

    pivot = rides.pivot(
        index="day_of_week",
        columns="hour",
        values="rides"
    )

    st.dataframe(
        rides_by_day,        
        hide_index=True
    )

    fig, ax = plt.subplots(figsize=(10, 4), dpi=120)
    sns.heatmap(
        pivot,
        cmap="GnBu",
        ax=ax,
        linewidths=1,
        linecolor="#e6e6e6"
    )
    ax.set_xlabel("Hour", fontsize=FIG_FONTSIZE, color=FIG_COLOUR)
    ax.set_ylabel("Day", fontsize=FIG_FONTSIZE, color=FIG_COLOUR)
    ax.tick_params(axis="both", labelsize=FIG_FONTSIZE, color=FIG_COLOUR, length=0)
    ax.set_title(
        "Number of Taxi Rides by Day and Hour",
        fontsize=FIG_FONTSIZE,
        color=FIG_COLOUR
    )
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(labelsize=FIG_FONTSIZE, colors=FIG_COLOUR)
    # cbar.set_label("Number of Rides", fontsize=FIG_FONTSIZE, color=FIG_COLOUR)
    st.pyplot(fig)

# ============================
# TAB 3 — DIVISION ANALYSIS
# ============================
with tab3:
    st.subheader("Taxi Usage by Division")
    message_3 = """
    <div class='content'>
    There are 121 divisions in the dataset. However, only 10 divisions exhibit repeated taxi usage, while the remaining divisions each record only a single taxi trip. 
    This demonstrates that taxi usage is highly concentrated within a small subset of divisions. Such concentration suggests that targeted, division-level interventions 
    would be more effective and cost-efficient than broad, organisation-wide measures.
    <br><br>

    **🔎Possible cost reduction strategy:**  
    Shuttle bus services can be prioritised and arranged for high-usage divisions.
    <br><br>
    </div>
    """
    st.markdown(message_3, unsafe_allow_html=True)

    division_summary = (
        filtered_df
        .groupby("division_code")
        .agg(
            trips=("total_fare", "count"),
            total_cost=("total_fare", "sum")
        )
        .sort_values("trips", ascending=False)
    )

    st.dataframe(division_summary)

    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax1.bar(
        division_summary.index[:10],
        division_summary["trips"][:10],
        label="Number of Trips"
    )
    ax1.set_ylabel("Trips", fontsize=FIG_FONTSIZE, color=FIG_COLOUR)
    ax1.set_xlabel("Division", fontsize=FIG_FONTSIZE, color=FIG_COLOUR)
    ax1.tick_params(axis="both", labelsize=FIG_FONTSIZE, color=FIG_COLOUR, length=0)  

    # Line chart: total cost
    ax2 = ax1.twinx()
    ax2.plot(
        division_summary.index[:10],
        division_summary["total_cost"][:10],
        marker="o",
        label="Total Cost"
    )
    ax2.set_ylabel("Total Cost", fontsize=FIG_FONTSIZE, color=FIG_COLOUR)
    ax2.set_title(
        "Comparison of Taxi Usage and Cost by Division",
        fontsize=FIG_FONTSIZE,
        color=FIG_COLOUR
    )    
    ax2.tick_params(axis="both", labelsize=FIG_FONTSIZE, color=FIG_COLOUR, length=0)    

    # Legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(
        lines_1 + lines_2,
        labels_1 + labels_2,
        loc="upper right",
        fontsize=FIG_FONTSIZE
    )    

    # Styling
    # Remove border for bar axis
    for spine in ax1.spines.values():
        spine.set_visible(False)

    # Remove border for line axis
    for spine in ax2.spines.values():
        spine.set_visible(False)
    
    ax1.grid(
        True,
        which="major",
        axis="y",
        color="#e6e6e6",
        linewidth=0.8
    )
    ax1.set_axisbelow(True)
    ax2.set_axisbelow(True)

    st.pyplot(fig)

    #--- Taxi Usage By Weekday Across Division ---
    df_top = df[df["division_code"].isin(top_10_divisions)]

    weekday_division = (
        df_top
        .groupby(["day_of_week", "division_code"])
        .size()
        .reset_index(name="number_of_rides")
    )

    pivot_df = weekday_division.pivot(
        index="day_of_week",
        columns="division_code",
        values="number_of_rides"
    ).fillna(0)

    fig, ax3 = plt.subplots(figsize=(10, 5), dpi=120)

    pivot_df.plot(
        kind="bar",
        stacked=True,
        ax=ax3
    )

    ax3.set_xlabel("Day of Week", fontsize=FIG_FONTSIZE, color=FIG_COLOUR)
    ax3.set_ylabel("Number of Rides", fontsize=FIG_FONTSIZE, color=FIG_COLOUR)
    ax3.set_title(
        "Taxi Usage by Weekday (Stacked by Top 10 Divisions)",
        fontsize=FIG_FONTSIZE,
        color=FIG_COLOUR
    )

    ax3.tick_params(axis="x", labelsize=FIG_FONTSIZE, rotation=30, colors=FIG_COLOUR)
    ax3.tick_params(axis="y", labelsize=FIG_FONTSIZE, colors=FIG_COLOUR)

    ax3.legend(
        title="Division",
        fontsize=9,
        title_fontsize=FIG_FONTSIZE,
        bbox_to_anchor=(1.05, 1),
        loc="upper left"
    )

    plt.tight_layout()

    for spine in ax3.spines.values():
        spine.set_visible(False)
    
    ax3.grid(
        True,
        which="major",
        axis="y",
        color="#e6e6e6",
        linewidth=0.8
    )
    ax3.set_axisbelow(True)

    st.pyplot(fig)    

# ============================
# TAB 4 — GEO ANALYSIS
# ============================
with tab4:
    st.subheader("Pickup & Drop-off Hotspots")
    message_4 = """
    <div class='content'>
    A geospatial analysis of taxi pickup and drop-off locations was conducted to identify frequently travelled routes and demand hotspots.
    <br><br>

    **🔎Potential cost reduction strategy:**
    <br>Optimise shuttle bus routes and operating schedules based on observed travel patterns.

    For instance, during the late-night period (00:00–04:00), taxi pickups are highly concentrated within a specific location. 
    This indicates a consistent demand corridor, suggesting that a dedicated shuttle bus service could be introduced during these hours to reduce reliance on taxis and lower overall transport costs.
    <br><br>
    </div>
    """
    st.markdown(message_4, unsafe_allow_html=True)

    pickup = (
        filtered_df
        .groupby(["pickup_latitude", "pickup_longtitude"])
        .size()
        .reset_index(name="count")
    )

    dropoff = (
        filtered_df
        .groupby(["destination_latitude", "destination_longtitude"])
        .size()
        .reset_index(name="count")
    )

    pickup_layer = pdk.Layer(
        "ScatterplotLayer",
        pickup,
        get_position="[pickup_longtitude, pickup_latitude]",
        get_radius="200 + count * 5",
        get_fill_color="[255, 0, 0, 140]",
        pickable=True
    )

    drop_layer = pdk.Layer(
        "ScatterplotLayer",
        dropoff,
        get_position="[destination_longtitude, destination_latitude]",
        get_radius="200 + count * 5",
        get_fill_color="[0, 200, 0, 140]",
        pickable=True
    )

    view = pdk.ViewState(
        latitude=1.3521,
        longitude=103.8198,
        zoom=11
    )

    st.markdown(
        """
        <div style="display: flex; justify-content: left; gap: 30px; margin-top: 10px;">
            <div>
                <span style="display:inline-block; width:12px; height:12px;
                            background-color: rgba(255,0,0,0.8); border-radius:50%;"></span>
                <span style="margin-left:6px;">Pickup Locations</span>
            </div>
            <div>
                <span style="display:inline-block; width:12px; height:12px;
                            background-color: rgba(0,200,0,0.8); border-radius:50%;"></span>
                <span style="margin-left:6px;">Destination Locations</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[pickup_layer, drop_layer],
            initial_view_state=view,
            tooltip={"text": "Trips: {count}"}
        )
    )
