from flask import Blueprint, render_template
from pymongo import MongoClient
import os

customer_satisfaction = Blueprint('customer_satisfaction', __name__)

# MongoDB Atlas connection string
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://<username>:<password>@cluster0.vrqby.mongodb.net/quality_dashboard?retryWrites=true&w=majority')

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.get_database()
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    db = None

@customer_satisfaction.route('/customer_satisfaction')
def show_customer_satisfaction():
    # Placeholder data - replace with actual data from MongoDB when available
    satisfaction_data = {
        'customer_satisfaction_score': 4.2,
        'on_time_delivery': 95,
        'return_rate': 1.5
    }

    return render_template('customer_satisfaction.html', data=satisfaction_data)

