from flask import Flask, request, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

# MongoDB Configuration
MONGO_URI = "mongodb+srv://Firza:Firza293@cluster0.pnaf8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "Database"
COLLECTION_NAME = "Collection1"

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    print("MongoDB Connected Successfully!")
except Exception as e:
    print(f"MongoDB Connection Failed: {e}")

@app.route('/data', methods=['POST'])
def save_data():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON format"}), 400

        print(f"Received Data: {data}")  # Debugging

        temperature = data.get("temperature")
        humidity = data.get("humidity")
        motion = data.get("motion")

        if temperature is None or humidity is None:
            return jsonify({"error": "Temperature and humidity are required."}), 400

        record = {"temperature": temperature, "humidity": humidity, "motion": motion}
        collection.insert_one(record)

        return jsonify({"message": "Data saved successfully."}), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')  # Allow connections from all devices
