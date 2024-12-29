import dash
from dash import html, dcc
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
from django_plotly_dash import DjangoDash

# Example dataframe (placeholder)
df = px.data.gapminder().query("country=='Canada'")

# Create a single Dash app for all charts
app = DjangoDash('health_charts_app_combined')

# Create a 2x2 grid of subplots
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Life Expectancy (Line Chart)",
        "Population (Bar Chart)",
        "GDP vs Life Expectancy (Scatter Chart)",
        "GDP Per Capita (Line Chart)"
    )
)

# Add the first chart (Line)
fig.add_trace(
    go.Scatter(x=df['year'], y=df['lifeExp'], mode='lines', name='Life Expectancy'),
    row=1, col=1
)

# Add the second chart (Bar)
fig.add_trace(
    go.Bar(x=df['year'], y=df['pop'], name='Population'),
    row=1, col=2
)

# Add the third chart (Scatter)
fig.add_trace(
    go.Scatter(x=df['gdpPercap'], y=df['lifeExp'], mode='markers', name='GDP vs Life'),
    row=2, col=1
)

# Add the fourth chart (Line)
fig.add_trace(
    go.Scatter(x=df['year'], y=df['gdpPercap'], mode='lines', name='GDP Per Capita'),
    row=2, col=2
)

fig.update_layout(autosize=True)

app.layout = html.Div([
    dcc.Graph(figure=fig, style={'width': '100%', 'height': '100%'})
])
