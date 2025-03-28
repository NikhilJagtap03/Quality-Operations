from flask import Blueprint, render_template
from pymongo import MongoClient
import os

equipment_performance = Blueprint('equipment_performance', __name__)

# MongoDB Atlas connection string
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://<username>:<password>@cluster0.vrqby.mongodb.net/quality_dashboard?retryWrites=true&w=majority')

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.get_database()
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    db = None

@equipment_performance.route('/equipment_performance')
def show_equipment_performance():
    # Placeholder data - replace with actual data from MongoDB when available
    performance_data = {
        'overall_equipment_effectiveness': 75,
        'availability': 90,
        'performance': 85,
        'quality': 95
    }

    return render_template('equipment_performance.html', data=performance_data)

