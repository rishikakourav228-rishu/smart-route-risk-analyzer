from flask import Flask, render_template, request
import requests

app = Flask(__name__)


# -----------------------------
# GET LOCATION COORDINATES
# -----------------------------
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
        "name": location["name"]
    }


# -----------------------------
# GET REAL ROUTE
# -----------------------------
def get_route(start, destination):

    start_location = get_coordinates(start)
    destination_location = get_coordinates(destination)

    if not start_location or not destination_location:
        return None

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


# -----------------------------
# WEATHER DESCRIPTION
# -----------------------------
def weather_description(code):

    weather_codes = {

        0: "Clear Sky",

        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Overcast",

        45: "Fog",
        48: "Fog",

        51: "Light Drizzle",
        53: "Moderate Drizzle",
        55: "Heavy Drizzle",

        61: "Light Rain",
        63: "Moderate Rain",
        65: "Heavy Rain",

        71: "Light Snow",
        73: "Moderate Snow",
        75: "Heavy Snow",

        80: "Rain Showers",
        81: "Moderate Rain Showers",
        82: "Heavy Rain Showers",

        95: "Thunderstorm",
        96: "Thunderstorm with Hail",
        99: "Heavy Thunderstorm"
    }

    return weather_codes.get(code, "Unknown Weather")


# -----------------------------
# GET REAL WEATHER
# -----------------------------
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

    code = current["weather_code"]

    return {
        "temperature": current["temperature_2m"],
        "wind_speed": current["wind_speed_10m"],
        "condition": weather_description(code),
        "weather_code": code
    }


# -----------------------------
# RISK CALCULATION
# -----------------------------
# -----------------------------
# RISK CALCULATION
# -----------------------------
def calculate_risk(weather, distance):

    score = 10
    reasons = []

    if weather:

        temperature = weather["temperature"]
        wind = weather["wind_speed"]
        code = weather["weather_code"]

        # Temperature risk
        if temperature >= 40:
            score += 20
            reasons.append("Very high temperature")
        elif temperature >= 35:
            score += 10
            reasons.append("High temperature")

        elif temperature <= 5:
            score += 15
            reasons.append("Very low temperature")

        # Wind risk
        if wind >= 40:
            score += 25
            reasons.append("Very strong wind")
        elif wind >= 25:
            score += 15
            reasons.append("Strong wind")
        elif wind >= 15:
            score += 5
            reasons.append("Moderate wind")

        # Weather condition risk
        if code in [95, 96, 99]:
            score += 35
            reasons.append("Thunderstorm")

        elif code in [65, 82]:
            score += 25
            reasons.append("Heavy rain")

        elif code in [61, 63, 80, 81]:
            score += 15
            reasons.append("Rain")

        elif code in [45, 48]:
            score += 20
            reasons.append("Fog")

        elif code in [71, 73, 75]:
            score += 20
            reasons.append("Snow")

    # Distance risk
    if distance >= 500:
        score += 20
        reasons.append("Very long route")

    elif distance >= 300:
        score += 15
        reasons.append("Long route")

    elif distance >= 150:
        score += 5
        reasons.append("Moderately long route")

    score = min(score, 100)

    if score < 30:
        level = "Low Risk"

    elif score < 60:
        level = "Moderate Risk"

    else:
        level = "High Risk"

    if not reasons:
        reasons.append("No major risk indicator detected")

    return score, level, reasons
# -----------------------------
# HOME PAGE
# -----------------------------
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

            risk_score, risk_level = calculate_risk(
                weather,
                route["distance"]
            )

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


# -----------------------------
# START APPLICATION
# -----------------------------
if __name__ == "__main__":
    app.run()
