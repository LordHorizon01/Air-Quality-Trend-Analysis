import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error


# Page Setup


st.set_page_config(page_title="Air Quality Dashboard", layout="wide")

st.title("🌍 Air Quality Trend Analysis - Professional Dashboard")
st.markdown("Interactive Analysis and Forecasting of Air Pollutants")

# Load Data


df = pd.read_csv("data/processed_air_quality.csv")

df["Datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"])
# pollutant columns
numeric_cols = [
    'CO(GT)', 'PT08.S1(CO)', 'C6H6(GT)', 'PT08.S2(NMHC)',
    'NOx(GT)', 'PT08.S3(NOx)', 'NO2(GT)',
    'PT08.S4(NO2)', 'PT08.S5(O3)', 'T', 'RH', 'AH'
]


# Sidebar Controls


st.sidebar.header("Dashboard Controls")

selected_pollutant = st.sidebar.selectbox(
    "Select Pollutant",
    numeric_cols
)

rolling_window = st.sidebar.slider(
    "Rolling Window (hours)",
    6,
    72,
    48
)

st.sidebar.subheader("Date Filter")

start_date = st.sidebar.date_input(
    "Start Date",
    df["Datetime"].min().date()
)

end_date = st.sidebar.date_input(
    "End Date",
    df["Datetime"].max().date()
)

st.sidebar.subheader("Hour Filter")

hour_range = st.sidebar.slider(
    "Select Hour Range",
    0,
    23,
    (0, 23)
)

filtered_df = df[
    (df["Datetime"].dt.date >= start_date) &
    (df["Datetime"].dt.date <= end_date)
]

filtered_df = filtered_df[
    (filtered_df["Datetime"].dt.hour >= hour_range[0]) &
    (filtered_df["Datetime"].dt.hour <= hour_range[1])
]

model_option = st.sidebar.selectbox(
    "Models Used",
    ["Naive", "Moving Average"]
)


# Create Lag Features


df[selected_pollutant + "_lag1"] = df[selected_pollutant].shift(1)
df[selected_pollutant + "_lag2"] = df[selected_pollutant].shift(2)
df[selected_pollutant + "_lag3"] = df[selected_pollutant].shift(3)

df[selected_pollutant + "_ma_forecast"] = df[selected_pollutant].rolling(3).mean()

df = df.dropna()
filtered_df = df[
    (df["Datetime"].dt.date >= start_date) &
    (df["Datetime"].dt.date <= end_date)
]

filtered_df = filtered_df[
    (filtered_df["Datetime"].dt.hour >= hour_range[0]) &
    (filtered_df["Datetime"].dt.hour <= hour_range[1])
]


# Train Test Split


train_size = int(len(df) * 0.8)

train = df.iloc[:train_size].copy()
test = df.iloc[train_size:].copy()


# Dashboard Tabs


tabs = st.tabs([
    "📈 Time Series",
    "📊 Distribution",
    "🔄 Rolling Stats",
    "🔥 Heatmap",
    "📅 Seasonality",
    "🔗Autocorrelation",
    "🎯 Forecast vs Actual",
    "📋 Summary Stats"
])


# Time Series


with tabs[0]:

    st.subheader("Time Series")

    fig = px.line(
        filtered_df,
        x="Datetime",
        y=selected_pollutant,
        title=f"{selected_pollutant} Over Time"
    )

    st.plotly_chart(fig, use_container_width=True)


# Distribution


with tabs[1]:

    st.subheader(f"Distribution Analysis: {selected_pollutant}")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("Histogram")

        fig = px.histogram(
            filtered_df,
            x=selected_pollutant,
            nbins=50,
            title="Distribution Histogram"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:

        st.markdown("Box Plot")

        fig = px.box(
            filtered_df,
            y=selected_pollutant,
            title="Outlier Detection"
        )

        st.plotly_chart(fig, use_container_width=True)

# Rolling Statistics

with tabs[2]:

    st.subheader(f"Rolling Statistics ({rolling_window}h window)")

    rolling_mean = filtered_df[selected_pollutant].rolling(rolling_window).mean()
    rolling_min = filtered_df[selected_pollutant].rolling(rolling_window).min()
    rolling_max = filtered_df[selected_pollutant].rolling(rolling_window).max()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=filtered_df["Datetime"],
        y=filtered_df[selected_pollutant],
        mode="lines",
        name="Actual",
        line=dict(color="white")
    ))

    fig.add_trace(go.Scatter(
        x=filtered_df["Datetime"],
        y=rolling_mean,
        mode="lines",
        name=f"Mean ({rolling_window}h)"
    ))

    fig.add_trace(go.Scatter(
        x=filtered_df["Datetime"],
        y=rolling_min,
        mode="lines",
        name=f"Min ({rolling_window}h)",
        line=dict(dash="dash")
    ))

    fig.add_trace(go.Scatter(
        x=filtered_df["Datetime"],
        y=rolling_max,
        mode="lines",
        name=f"Max ({rolling_window}h)",
        line=dict(dash="dash")
    ))

    st.plotly_chart(fig, use_container_width=True)


# Heatmap

with tabs[3]:

    st.subheader("Hourly vs Daily Heatmap")

    filtered_df = filtered_df.copy()

    filtered_df["hour"] = filtered_df["Datetime"].dt.hour
    filtered_df["day"] = filtered_df["Datetime"].dt.day_name()

    heatmap_data = filtered_df.pivot_table(
        values=selected_pollutant,
        index="day",
        columns="hour",
        aggfunc="mean"
    )

    fig = px.imshow(
        heatmap_data,
        aspect="auto",
        color_continuous_scale="viridis"
    )

    st.plotly_chart(fig, use_container_width=True)

# Seasonality

with tabs[4]:

    st.subheader("Monthly & Seasonal Trends")

    filtered_df = filtered_df.copy()

    filtered_df["month"] = filtered_df["Datetime"].dt.month_name()
    filtered_df["day"] = filtered_df["Datetime"].dt.day_name()

    monthly_avg = filtered_df.groupby("month")[selected_pollutant].mean()
    daily_avg = filtered_df.groupby("day")[selected_pollutant].mean()

    col1, col2 = st.columns(2)

    with col1:

        fig = px.bar(
            monthly_avg,
            title="Monthly Average",
            labels={"value": "Avg Concentration", "month": "Month"}
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:

        fig = px.bar(
            daily_avg,
            title="Daily Average",
            labels={"value": "Avg Concentration", "day": "Day"}
        )

        st.plotly_chart(fig, use_container_width=True)


# Autocorrelation


with tabs[5]:

    st.subheader("Autocorrelation Analysis")

    max_lag = st.slider("Select Max Lag", 10, 200, 50)

    autocorr_values = [
        filtered_df[selected_pollutant].autocorr(lag=i)
        for i in range(1, max_lag)
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=list(range(1, max_lag)),
        y=autocorr_values,
        name="Autocorrelation"
    ))

    fig.update_layout(
        title="Autocorrelation vs Lag",
        xaxis_title="Lag",
        yaxis_title="Correlation"
    )

    st.plotly_chart(fig, use_container_width=True)

# Forecast vs Actual

with tabs[6]:

    st.subheader("Forecast vs Actual")

    if model_option == "Naive":

        y_true = test[selected_pollutant]
        y_pred = test[selected_pollutant + "_lag1"]

    elif model_option == "Moving Average":

        y_true = test[selected_pollutant]
        y_pred = test[selected_pollutant + "_ma_forecast"]

    else:

        X_train = train[[selected_pollutant + "_lag1",
                         selected_pollutant + "_lag2",
                         selected_pollutant + "_lag3"]]

        y_train = train[selected_pollutant]

        X_test = test[[selected_pollutant + "_lag1",
                       selected_pollutant + "_lag2",
                       selected_pollutant + "_lag3"]]

        y_true = test[selected_pollutant]

        model = LinearRegression()
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        y=y_true.values,
        mode='lines',
        name='Actual'
    ))

    fig.add_trace(go.Scatter(
        y=y_pred,
        mode='lines',
        name='Forecast'
    ))

    st.plotly_chart(fig, use_container_width=True)

    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)

    st.metric("RMSE", round(rmse, 4))

# Summary Statistics

with tabs[7]:

    st.subheader("Summary Statistics")

    data = filtered_df[selected_pollutant]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Count", len(data))
    col2.metric("Mean", round(data.mean(),4))
    col3.metric("Median", round(data.median(),4))
    col4.metric("Std Dev", round(data.std(),4))

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Min", round(data.min(),4))
    col6.metric("Q1 (25%)", round(data.quantile(0.25),4))
    col7.metric("Q3 (75%)", round(data.quantile(0.75),4))
    col8.metric("Max", round(data.max(),4))

    st.markdown("### Data Quality")

    missing = filtered_df[selected_pollutant].isna().sum()
    completeness = (1 - missing/len(filtered_df))*100

    st.write(f"• Missing values: {missing}")
    st.write(f"• Data completeness: {round(completeness,2)}%")