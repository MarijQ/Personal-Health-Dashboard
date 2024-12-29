# FILE: stats/dash_apps.py

import sqlite3
from django.conf import settings
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import html, dcc
from django_plotly_dash import DjangoDash


# Create a Dash app for all charts
app = DjangoDash('health_charts_app_combined')


def get_df_from_sql(table_name):
    """
    Utility function to read an entire table from the SQLite DB into a pandas DataFrame.
    Returns an empty DataFrame if the table doesn't exist.
    """
    try:
        conn = sqlite3.connect(settings.DATABASES['default']['NAME'])
        df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Warning: Could not read table {table_name}. Error: {e}")
        return pd.DataFrame()


def clean_numeric_column(df, column_name):
    """
    Ensure a column is numeric, replacing invalid values with NaN.
    Returns the cleaned DataFrame.
    """
    if column_name in df.columns:
        df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
    return df


# ---- LOAD DATA FROM DB ----
df_steps = get_df_from_sql("step_db")
df_sleep = get_df_from_sql("sleep_db")
df_hr = get_df_from_sql("hr_db")
df_cal = get_df_from_sql("calorie_db")
df_blood = get_df_from_sql("blood_test_db")
df_cigs = get_df_from_sql("cigarette_db")
df_sym = get_df_from_sql("symptoms_db")


# Ensure date columns are recognized as dates when possible
for df in [df_steps, df_sleep, df_hr, df_cal, df_blood, df_cigs, df_sym]:
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')


# Placeholder function for empty charts
def empty_chart(title):
    fig = go.Figure()
    fig.update_layout(
        title=title,
        xaxis=dict(title='Date'),
        yaxis=dict(title='Value'),
        annotations=[
            dict(
                text="No data available",
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=20)
            )
        ]
    )
    return fig


# ------------------------------------------------------------------------
# CHART 1: Steps vs. Sleep
# ------------------------------------------------------------------------
if not df_steps.empty and not df_sleep.empty:
    # Clean data
    df_steps = clean_numeric_column(df_steps, 'Step_Counts')
    df_sleep = clean_numeric_column(df_sleep, 'Total_Sleep_Hours')

    # Merge and aggregate
    df_1 = pd.merge(df_steps, df_sleep, on='Date', how='inner', suffixes=("_steps", "_sleep"))
    df_1 = df_1.dropna(subset=['Step_Counts', 'Total_Sleep_Hours'])
    df_1_agg = df_1.groupby('Date', as_index=False).agg({
        'Step_Counts': 'sum',
        'Total_Sleep_Hours': 'mean'
    }).rename(columns={'Step_Counts': 'Daily_Steps', 'Total_Sleep_Hours': 'Avg_Sleep_Hours'})

    # Create chart
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=df_1_agg['Date'], y=df_1_agg['Daily_Steps'], name='Daily Steps', marker_color='blue'))
    fig1.add_trace(go.Scatter(
        x=df_1_agg['Date'], y=df_1_agg['Avg_Sleep_Hours'],
        name='Avg Sleep Hours', mode='lines+markers', yaxis='y2', marker_color='green'
    ))
    fig1.update_layout(
        title='Steps vs. Sleep (Daily)',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Steps'),
        yaxis2=dict(
            title='Sleep (hours)',
            overlaying='y',
            side='right'
        )
    )
else:
    fig1 = empty_chart("Steps vs. Sleep")


# ------------------------------------------------------------------------
# CHART 2: HR vs. Sleep
# ------------------------------------------------------------------------
if not df_hr.empty and not df_sleep.empty:
    # Clean data
    df_hr = clean_numeric_column(df_hr, 'Heart_Rate')
    df_sleep = clean_numeric_column(df_sleep, 'Total_Sleep_Hours')

    # Merge and aggregate
    df_2 = pd.merge(df_hr, df_sleep, on='Date', how='inner')
    df_2 = df_2.dropna(subset=['Heart_Rate', 'Total_Sleep_Hours'])
    df_2_agg = df_2.groupby('Date', as_index=False).agg({
        'Heart_Rate': 'mean',
        'Total_Sleep_Hours': 'mean'
    }).rename(columns={'Heart_Rate': 'Avg_Heart_Rate', 'Total_Sleep_Hours': 'Avg_Sleep_Hours'})

    # Create chart
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_2_agg['Date'], y=df_2_agg['Avg_Heart_Rate'], name='Avg HR', mode='lines+markers'))
    fig2.add_trace(go.Scatter(
        x=df_2_agg['Date'], y=df_2_agg['Avg_Sleep_Hours'], name='Avg Sleep Hours', mode='lines+markers', yaxis='y2'
    ))
    fig2.update_layout(
        title="HR vs. Sleep",
        xaxis=dict(title='Date'),
        yaxis=dict(title='Heart Rate (bpm)'),
        yaxis2=dict(
            title='Sleep (hours)',
            overlaying='y',
            side='right'
        )
    )
else:
    fig2 = empty_chart("HR vs. Sleep")


# ------------------------------------------------------------------------
# CHART 3: Calories Consumed vs. Burned
# ------------------------------------------------------------------------
if not df_cal.empty:
    # Clean data
    df_cal = clean_numeric_column(df_cal, 'Calories Consumed')
    df_cal = clean_numeric_column(df_cal, 'Calories Burned')

    # Aggregate
    df_3_agg = df_cal.groupby('Date', as_index=False).agg({
        'Calories Consumed': 'sum',
        'Calories Burned': 'sum'
    }).rename(columns={'Calories Consumed': 'Total_Consumed', 'Calories Burned': 'Total_Burned'})

    # Create chart
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=df_3_agg['Date'], y=df_3_agg['Total_Consumed'], name='Consumed', marker_color='indigo'))
    fig3.add_trace(go.Bar(x=df_3_agg['Date'], y=df_3_agg['Total_Burned'], name='Burned', marker_color='orange'))
    fig3.update_layout(
        barmode='group',
        title='Calories Consumed vs. Burned',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Calories')
    )
else:
    fig3 = empty_chart("Calories Consumed vs. Burned")


# ------------------------------------------------------------------------
# CHART 4: RBC vs. Cigarettes
# ------------------------------------------------------------------------
if not df_blood.empty and not df_cigs.empty:
    # Clean data
    df_blood = clean_numeric_column(df_blood, 'RBC')
    df_cigs = clean_numeric_column(df_cigs, 'Number of Cigarettes')

    # Merge and aggregate
    df_4 = pd.merge(df_blood, df_cigs, on='Date', how='inner')
    df_4 = df_4.dropna(subset=['RBC', 'Number of Cigarettes'])
    df_4_agg = df_4.groupby('Date', as_index=False).agg({
        'RBC': 'mean',
        'Number of Cigarettes': 'sum'
    }).rename(columns={'RBC': 'Avg_RBC', 'Number of Cigarettes': 'Cigs_per_day'})

    # Create chart
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=df_4_agg['Date'], y=df_4_agg['Avg_RBC'], name='Avg RBC', mode='lines+markers'))
    fig4.add_trace(go.Bar(x=df_4_agg['Date'], y=df_4_agg['Cigs_per_day'], name='Cigs per Day', yaxis='y2'))
    fig4.update_layout(
        title='RBC vs. Cigarettes',
        xaxis=dict(title='Date'),
        yaxis=dict(title='RBC'),
        yaxis2=dict(
            title='Cigarettes',
            overlaying='y',
            side='right'
        )
    )
else:
    fig4 = empty_chart("RBC vs. Cigarettes")


# ------------------------------------------------------------------------
# COMBINE INTO 2x2 GRID
# ------------------------------------------------------------------------
final_fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=[
        "Steps vs. Sleep",
        "HR vs. Sleep",
        "Calories Consumed vs. Burned",
        "RBC vs. Cigarettes"
    ],
    specs=[[{"secondary_y": True}, {"secondary_y": True}],
           [{"secondary_y": False}, {"secondary_y": True}]]
)

# Add traces from individual charts to the corresponding subplot
for trace in fig1.data:
    final_fig.add_trace(trace, row=1, col=1, secondary_y='yaxis2' in trace.to_plotly_json())
for trace in fig2.data:
    final_fig.add_trace(trace, row=1, col=2, secondary_y='yaxis2' in trace.to_plotly_json())
for trace in fig3.data:
    final_fig.add_trace(trace, row=2, col=1, secondary_y=False)
for trace in fig4.data:
    final_fig.add_trace(trace, row=2, col=2, secondary_y='yaxis2' in trace.to_plotly_json())

# Update layout and axes
final_fig.update_layout(
    height=900,
    title="Health Dashboard Overview",
    xaxis_title="Date"
)

# Ensure each subplot has its own axis titles
final_fig.update_xaxes(title_text="Date", row=1, col=1)
final_fig.update_yaxes(title_text="Steps", row=1, col=1)
final_fig.update_yaxes(title_text="Sleep (hours)", row=1, col=1, secondary_y=True)

final_fig.update_xaxes(title_text="Date", row=1, col=2)
final_fig.update_yaxes(title_text="HR (bpm)", row=1, col=2)
final_fig.update_yaxes(title_text="Sleep (hours)", row=1, col=2, secondary_y=True)

final_fig.update_xaxes(title_text="Date", row=2, col=1)
final_fig.update_yaxes(title_text="Calories", row=2, col=1)

final_fig.update_xaxes(title_text="Date", row=2, col=2)
final_fig.update_yaxes(title_text="RBC", row=2, col=2)
final_fig.update_yaxes(title_text="Cigarettes", row=2, col=2, secondary_y=True)

# Apply the layout to the Dash app
app.layout = html.Div([
    dcc.Graph(figure=final_fig)
])
