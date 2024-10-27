from flask import Flask, render_template, request, jsonify
from FlightRadar24 import FlightRadar24API
import airportsdata
airports = airportsdata.load('IATA')
import math

def find_closest_point(coordinates, target_lat, target_lon):
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    closest_point = None
    min_distance = float('inf')

    for lat, lon in coordinates:
        distance = haversine(target_lat, target_lon, lat, lon)
        if distance < min_distance:
            min_distance = distance
            closest_point = (lat, lon)

    return closest_point, min_distance
fr_api = FlightRadar24API()

app = Flask(__name__)
def get_city(id):
    try:
        return airports[id]['city']
    except:
        return "N/A"
@app.route("/")
def index():
    return render_template("index.html")
@app.post("/api/getflights")
def getflights():
    data = request.get_json()
    latitude=data["lat"]
    longitude=data["long"]
    lis =[]
    nearby = fr_api.get_flights(bounds=fr_api.get_bounds_by_point(latitude, longitude, 8047))
    for i in nearby:
        try:
            lis.append((i.latitude, i.longitude))
        except:
            data.append("not much data known")
    print(data)
    closest = find_closest_point(lis, latitude, longitude)
    i=nearby[lis.index(closest[0])]
    flight_details = fr_api.get_flight_details(i)
    i.set_flight_details(flight_details)
    images = []
    for j in i.aircraft_images["large"]:
        images.append(j['src'])
    depart = i.time_details["real"]['departure'] if i.time_details["real"]['departure'] is not None else i.time_details["scheduled"]['departure']
    arrive = i.time_details["real"]['arrival'] if i.time_details["real"]['arrival'] is not None else (depart-i.time_details["scheduled"]['departure'])+i.time_details["scheduled"]['arrival']
    data={"images":images, "destination":get_city(i.destination_airport_iata), "orgin":get_city(i.origin_airport_iata), "destination code":i.destination_airport_iata, "orgin code":i.origin_airport_iata, "model":i.aircraft_model, "airline":i.airline_name, "depart gate":i.origin_airport_gate, "arrival gate":i.destination_airport_gate, "age": i.aircraft_age, "call sign":i.callsign, "depart":depart, "arrive":arrive}
    print(data)
    return jsonify(data)
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
