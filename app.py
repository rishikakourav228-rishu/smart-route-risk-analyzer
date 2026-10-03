from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():

    result = None

    if request.method == "POST":

        start = request.form.get("start")
        destination = request.form.get("destination")

        # Demo route analysis
        distance = "190 km"
        time = "4 hours"
        traffic = "Moderate"
        weather = "Clear"
        risk_score = 35
        risk_level = "Low Risk"

        result = {
            "start": start,
            "destination": destination,
            "distance": distance,
            "time": time,
            "traffic": traffic,
            "weather": weather,
            "risk_score": risk_score,
            "risk_level": risk_level
        }

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)