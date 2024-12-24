import dash
from dash import html, dcc
import plotly.express as px
from django_plotly_dash import DjangoDash

# Example dataframe (placeholder)
df = px.data.gapminder().query("country=='Canada'")

# 1st chart app
app = DjangoDash('health_charts_app')
fig = px.line(df, x='year', y='lifeExp', title='Life Expectancy (Placeholder Chart)')
app.layout = html.Div([dcc.Graph(figure=fig)])

# 2nd chart app
app2 = DjangoDash('health_charts_app_2')
fig2 = px.bar(df, x='year', y='pop', title='Population (Placeholder Chart)')
app2.layout = html.Div([dcc.Graph(figure=fig2)])

# 3rd chart app
app3 = DjangoDash('health_charts_app_3')
fig3 = px.scatter(df, x='gdpPercap', y='lifeExp', title='GDP vs Life Expectancy')
app3.layout = html.Div([dcc.Graph(figure=fig3)])

# 4th chart app
app4 = DjangoDash('health_charts_app_4')
fig4 = px.line(df, x='year', y='gdpPercap', title='GDP Per Capita (Placeholder Chart)')
app4.layout = html.Div([dcc.Graph(figure=fig4)])
