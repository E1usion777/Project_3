import requests
from flask import Flask, render_template
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go

API_KEY = "7ec80289916b7564f7581d20da27f604"
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"

def get_weather_data(city):
    url = BASE_URL
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "ru"
    }
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None

server = Flask(__name__)

@server.route('/')
def index():
    return render_template('index.html')

@server.route('/weather')
def weather():
    return render_template('weather.html')

app = dash.Dash(__name__, server=server, url_base_pathname='/dash/')

app.layout = html.Div([
    dcc.Input(id="start-city", type="text", placeholder="Начальная точка", style={"width": "100%"}),
    dcc.Textarea(id="mid-cities", placeholder="Промежуточные точки (по одной в строке)",
                 style={"width": "100%", "height": "100px"}),
    dcc.Input(id="end-city", type="text", placeholder="Конечная точка", style={"width": "100%"}),
    html.Button("Отправить", id="submit-button", n_clicks=0, style={"marginTop": "10px"}),

    dcc.Dropdown(
        id='parameter-dropdown',
        options=[
            {'label': 'Температура', 'value': 'temperature'},
            {'label': 'Скорость ветра', 'value': 'wind_speed'},
            {'label': 'Вероятность осадков', 'value': 'precipitation'}
        ],
        value='temperature',
        clearable=False,
        style={'width': '100%', 'margin': '0 auto'}
    ),

    dcc.Graph(id="weather-graph"),
])

@app.callback(
    Output("weather-graph", "figure"),
    [Input("submit-button", "n_clicks"), Input("parameter-dropdown", "value")],
    [State("start-city", "value"), State("mid-cities", "value"), State("end-city", "value")]
)
def update_graph(n_clicks, selected_parameter, start_city, mid_cities, end_city):
    if n_clicks == 0:
        return go.Figure()

    city_list = [start_city] + (
        [city.strip() for city in mid_cities.split("\n") if city.strip()] if mid_cities else []) + [end_city]

    all_data = {}

    for city in city_list:
        data = get_weather_data(city)

        if data:
            processed_data = [
                {
                    'time': entry["dt_txt"],
                    'temperature': entry["main"]["temp"],
                    'wind_speed': entry["wind"]["speed"],
                    'precipitation': entry.get("pop", 0) * 100,
                }
                for entry in data["list"]
            ]
            all_data[city] = processed_data

    fig = go.Figure()

    parameter_labels = {
        'temperature': 'Температура',
        'wind_speed': 'Скорость ветра',
        'precipitation': 'Вероятность осадков'
    }

    for city in all_data.keys():
        if selected_parameter == 'temperature':
            fig.add_trace(go.Scatter(
                x=[entry["time"] for entry in all_data[city]],
                y=[entry["temperature"] for entry in all_data[city]],
                mode='lines+markers',
                name=city
            ))
        elif selected_parameter == 'wind_speed':
            fig.add_trace(go.Scatter(
                x=[entry["time"] for entry in all_data[city]],
                y=[entry["wind_speed"] for entry in all_data[city]],
                mode='lines+markers',
                name=city
            ))
        elif selected_parameter == 'precipitation':
            fig.add_trace(go.Bar(
                x=[entry["time"] for entry in all_data[city]],
                y=[entry["precipitation"] for entry in all_data[city]],
                name=city
            ))

    fig.update_layout(title=f'{parameter_labels[selected_parameter]} по маршруту',
                      xaxis_title='Время',
                      yaxis_title=parameter_labels[selected_parameter],
                      hovermode="x unified")

    return fig

if __name__ == "__main__":
    app.run(debug=True)
