import pandas as pd
import matplotlib.pyplot as plt
# import plotly.express as px
import pydeck as pdk
import streamlit as st
import seaborn as sns

# CSV_PATH = r"D:\Assessment - SPTD Specialist AI_Data\SectionB_taxi trips_201501 to 201509\cleaned_taxi_data.csv"
current_dir = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(current_dir, 'cleaned_taxi_data.csv')
df = pd.read_csv(CSV_PATH)

st.set_page_config(page_title="Taxi Claims Dashboard", layout="wide")
st.title("Taxi Claims Dashboard, 2015 Jan-Sep")
st.markdown("Sample of Taxi Data (1084,16)")
st.dataframe(df.head(5))
st.write(list(df.columns))
st.write(df.shape)

# ----------------------------
# Styling
# ----------------------------
plt.style.use("dark_background")

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

# ----------------------------
# Handling Date Time
# ----------------------------
df["start_datetime"] = pd.to_datetime(df["start_datetime"])
df["month"] = df["start_datetime"].dt.to_period("M").dt.to_timestamp()
df["day_of_week"] = df["start_datetime"].dt.day_name()
df["hour"] = df["start_datetime"].dt.hour

day_order = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]

df["day_of_week"] = pd.Categorical(
    df["day_of_week"],
    categories=day_order,
    ordered=True
)
day_counts = df["day_of_week"].value_counts().sort_index()

# ----------------------------
# Problem Analysis
# ----------------------------
st.divider()
st.subheader("A. Is the total expense from taxi trips increasing? What is driving it?")

message_1 = """
<div class="content">
While total taxi expenditure shows noticeable fluctuations over time, there is no clear evidence of a sustained increase. 
Analysis indicates that these fluctuations are primarily driven by changes in the number of taxi trips taken by officers rather than changes in the average cost per trip. 
Although average cost per trip exhibits minor variation, these changes are insufficient to explain the magnitude of variation observed in total taxi expenditure. 
<br><br>
This suggests that taxi usage volume, rather than pricing, is the dominant factor influencing total costs.
</div>
"""
st.markdown(message_1, unsafe_allow_html=True)
st.write("\n\n\n")

# st.markdown("Distribution of Taxi Cost per Trip")
# st.write("Summary statistics for trip cost")
# st.write(df["total_fare"].describe())

# fig, ax = plt.subplots(figsize=(10, 8))

# sns.boxplot(
#     x=df["total_fare"],
#     ax=ax
# )

# ax.set_ylabel("Total Fare per Trip", color="white")
# ax.set_title("Box Plot of Taxi Cost per Trip", color="white")
# ax.tick_params(colors="white")

# st.pyplot(fig)

# ----- Total cost -----
monthly_cost = (
    df.groupby("month")["total_fare"]
    .sum()
    .reset_index()
)

st.line_chart(
    data=monthly_cost,
    x="month",
    y="total_fare"
)
st.markdown("<div class='caption'>Fig 1. Total Taxi Cost Over Time (Monthly)</div>", unsafe_allow_html=True)

# ----- Number of trips -----
trips_over_time = (
    df.groupby("month")
    .size()
    .reset_index(name="number_of_trips")
)

st.line_chart(
    data=trips_over_time,
    x="month",
    y="number_of_trips"
)
st.markdown("<div class='caption'>Fig 2. Number of Taxi Trips Over Time (Monthly)</div>", unsafe_allow_html=True)

# ----- Average cost -----
avg_cost_over_time = (
    df.groupby("month")["total_fare"]
    .mean()
    .reset_index(name="average_cost_per_trip")
)

st.line_chart(
    data=avg_cost_over_time,
    x="month",
    y="average_cost_per_trip"
)
st.markdown("<div class='caption'>Fig 3. Average Cost per Trip Over Time (Monthly)</div>", unsafe_allow_html=True)

# ----------------------------
# Insight 
# ----------------------------
st.divider()
st.subheader("B. Rides Analysis")

message_2 = """
<div class="content">
From the heatmap, it can be observed that rides are mostly concentrated during weekdays.

**Number of rides by day:**

| Day | Number of Rides |
|-----|----------------|
| Monday | 182 |
| Tuesday | 178 |
| Wednesday | 295 |
| Thursday | 249 |
| Friday | 176 |
| Saturday | 4 |
| Sunday | 0 |

Hence, further analysis will be performed on weekdays only.

**Peak timing identified:**
- Midnight: 00:00 – 04:00  
- Afternoon: 12:00 – 15:00  
- Evening: 18:00 – 20:00  

**Possible mitigation strategy:**  
Introduce shuttle services during late-night hours to reduce taxi usage.

</div>
"""

# st.dataframe(
#     day_counts,    
#     use_container_width=False
# )

st.markdown(message_2, unsafe_allow_html=True)
st.write("\n\n\n")

rides_by_day_hour = (
    df.groupby(["day_of_week", "hour"], observed=False)
    .size()
    .reset_index(name="number_of_rides")
)

pivot_table = rides_by_day_hour.pivot(
    index="day_of_week",
    columns="hour",
    values="number_of_rides"
)

fig, ax = plt.subplots(figsize=(10, 4.8), dpi=120)
sns.heatmap(
    pivot_table,
    cmap="GnBu",
    ax=ax
)

ax.set_xlabel("Hour of Day", fontsize=FIG_FONTSIZE)
ax.set_ylabel("Day of Week", fontsize=FIG_FONTSIZE)
ax.tick_params(axis="x", labelsize=FIG_FONTSIZE, colors="white")
ax.tick_params(axis="y", labelsize=FIG_FONTSIZE, colors="white")
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=FIG_FONTSIZE, colors="white")
cbar.set_label("Number of Rides", fontsize=FIG_FONTSIZE, color="white")

st.pyplot(fig, width='content')
st.markdown("<div class='caption'>Fig X. Number of Taxi Rides by Day and Hour</div>", unsafe_allow_html=True)

#--- Division ---
# st.markdown("Taxi Rides and Cost by Division")
message_3 = """
<div class='content'>
There are a total of 121 divisions in the dataset. However, only 10 divisions account for repeated taxi usage, while the remaining divisions have only a single recorded trip each. This indicates that taxi usage is highly concentrated within a small number of divisions.
<br><br>
Among these, Division Z002 records the highest number of taxi rides, making it the primary contributor to overall taxi usage. This concentration suggests that targeted interventions at the division level would be more effective than organisation-wide measures.
<br><br>
To reduce costs, shuttle bus services can be prioritised and expanded for high-usage divisions, particularly Division Z002.</div>
"""
st.markdown(message_3, unsafe_allow_html=True)

division_summary = (
    df.groupby("division_code")
    .agg(
        number_of_rides=("total_fare", "count"),
        total_cost=("total_fare", "sum")
    )
    .reset_index()
) # total 121 divisions

division_summary = division_summary[division_summary["number_of_rides"] > 1]

fig, ax1 = plt.subplots(figsize=(10, 4.8), dpi=120)

ax1.bar(
    division_summary["division_code"],
    division_summary["number_of_rides"],
    alpha=0.7,
    label="Number of Rides"
)
ax1.set_xlabel("Division", fontsize=FIG_FONTSIZE, color="white")
ax1.set_ylabel("Number of Rides", fontsize=FIG_FONTSIZE, color="white")
ax1.tick_params(axis="x", rotation=45, labelsize=FIG_FONTSIZE, colors="white")
ax1.tick_params(axis="y", labelsize=FIG_FONTSIZE, colors="white")

# Line chart: total cost
ax2 = ax1.twinx()
ax2.plot(
    division_summary["division_code"],
    division_summary["total_cost"],
    marker="o",
    label="Total Cost"
)
ax2.set_ylabel("Total Taxi Cost", fontsize=FIG_FONTSIZE, color="white")
ax2.tick_params(axis="y", labelsize=FIG_FONTSIZE, colors="white")

# Legends
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(
    lines_1 + lines_2,
    labels_1 + labels_2,
    loc="upper right",
    fontsize=8
)

st.pyplot(fig, width='content')
st.markdown("<div class='caption'>Fig 1. Comparison of Taxi Usage and Cost by Division</div>", unsafe_allow_html=True)

#--- Taxi Usage by weekday across division ---
top_divisions = (
    division_summary
    .sort_values("number_of_rides", ascending=False)
    .head(10)["division_code"]
)

df_top = df[df["division_code"].isin(top_divisions)]

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

fig, ax = plt.subplots(figsize=(10, 5), dpi=120)

bottom = None

for division in pivot_df.columns:
    ax.bar(
        pivot_df.index,
        pivot_df[division],
        bottom=bottom,
        label=division
    )
    bottom = (
        pivot_df[division]
        if bottom is None
        else bottom + pivot_df[division]
    )

ax.set_xlabel("Day of Week", fontsize=FIG_FONTSIZE, color="white")
ax.set_ylabel("Number of Rides", fontsize=FIG_FONTSIZE, color="white")

ax.tick_params(axis="x", labelsize=FIG_FONTSIZE, rotation=30, colors="white")
ax.tick_params(axis="y", labelsize=FIG_FONTSIZE, colors="white")

ax.legend(
    title="Division",
    fontsize=9,
    title_fontsize=FIG_FONTSIZE
)

plt.tight_layout()
st.pyplot(fig, width='content')
st.markdown("<div class='caption'>Fig 1. Number of Taxi Rides by Weekday (Stacked by Division)</div>", unsafe_allow_html=True)

#--- Location ---
# st.markdown("Taxi Rides by Location===============================================")
message_4 = """
<div class='content'>
In addition, a geospatial analysis of pickup and drop-off locations has been conducted to identify commonly travelled routes. These insights can be used to optimise shuttle bus routes and schedules, ensuring that alternative transport options are aligned with actual travel patterns and peak demand.

</div>
"""
st.markdown(message_4, unsafe_allow_html=True)
# ----- Pickup aggregation -----
pickup_df = (
    df.groupby(["pickup_latitude", "pickup_longtitude"])
    .size()
    .reset_index(name="trip_count")
)

# ----- Destination aggregation -----
dest_df = (
    df.groupby(["destination_latitude", "destination_longtitude"])
    .size()
    .reset_index(name="trip_count")
)

# ----- Pickup layer (RED) -----
pickup_layer = pdk.Layer(
    "ScatterplotLayer",
    data=pickup_df,
    get_position="[pickup_longtitude, pickup_latitude]",
    get_radius="200 + trip_count * 5",
    get_fill_color="[255, 0, 0, 140]",   # red
    pickable=True,
)

# ----- Destination layer (GREEN) -----
dest_layer = pdk.Layer(
    "ScatterplotLayer",
    data=dest_df,
    get_position="[destination_longtitude, destination_latitude]",
    get_radius="200 + trip_count * 5",
    get_fill_color="[0, 200, 0, 140]",   # green
    pickable=True,
)

# ----- View state (Singapore) -----
view_state = pdk.ViewState(
    latitude=1.3521,
    longitude=103.8198,
    zoom=11,
    pitch=0,
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

# ----- Render map -----
st.pydeck_chart(
    pdk.Deck(
        layers=[pickup_layer, dest_layer],
        initial_view_state=view_state,
        tooltip={
            "text": "Trips: {trip_count}"
        }
    )
)
st.markdown("<div class='caption'>Fig 1. Geospatial Analysis of Pickup and Drop-off Locations</div>", unsafe_allow_html=True)


