from flask import Flask, render_template, request
import requests

app = Flask(__name__)


def get_coordinates(place):
    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": place,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "results" not in data:
        return None

    location = data["results"][0]

    return {
        "lat": location["latitude"],
        "lon": location["longitude"],
        "name": location["name"],
        "country": location.get("country", "")
    }


def get_route(start, destination):

    start_location = get_coordinates(start)
    destination_location = get_coordinates(destination)

    if not start_location or not destination_location:
        return None

    # OSRM routing API
    route_url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{start_location['lon']},{start_location['lat']};"
        f"{destination_location['lon']},{destination_location['lat']}"
    )

    params = {
        "overview": "false"
    }

    response = requests.get(route_url, params=params)
    data = response.json()

    if data.get("code") != "Ok":
        return None

    route = data["routes"][0]

    distance_km = round(route["distance"] / 1000, 2)
    time_hours = round(route["duration"] / 3600, 2)

    return {
        "start": start_location,
        "destination": destination_location,
        "distance": distance_km,
        "time": time_hours
    }


def get_weather(latitude, longitude):

    weather_url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "timezone": "auto"
    }

    response = requests.get(weather_url, params=params)
    data = response.json()

    current = data.get("current")

    if not current:
        return None

    return {
        "temperature": current["temperature_2m"],
        "wind_speed": current["wind_speed_10m"],
        "weather_code": current["weather_code"]
    }


def calculate_risk(weather):

    if not weather:
        return 50, "Moderate Risk"

    score = 20

    # High wind increases risk
    if weather["wind_speed"] > 30:
        score += 25
    elif weather["wind_speed"] > 20:
        score += 15

    # Weather code
    code = weather["weather_code"]

    # Rain / storm / bad weather
    if code >= 51:
        score += 20

    if code >= 80:
        score += 20

    if code >= 95:
        score += 15

    score = min(score, 100)

    if score < 35:
        level = "Low Risk"
    elif score < 65:
        level = "Moderate Risk"
    else:
        level = "High Risk"

    return score, level


@app.route("/", methods=["GET", "POST"])
def home():

    result = None
    error = None

    if request.method == "POST":

        start = request.form.get("start")
        destination = request.form.get("destination")

        route = get_route(start, destination)

        if route:

            weather = get_weather(
                route["destination"]["lat"],
                route["destination"]["lon"]
            )

            risk_score, risk_level = calculate_risk(weather)

            result = {
                "start": route["start"]["name"],
                "destination": route["destination"]["name"],
                "distance": route["distance"],
                "time": route["time"],
                "weather": weather,
                "risk_score": risk_score,
                "risk_level": risk_level
            }

        else:
            error = "Location not found. Please enter a valid city name."

    return render_template(
        "index.html",
        result=result,
        error=error
    )


if __name__ == "__main__":
    app.run()
