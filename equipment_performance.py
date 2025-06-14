from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
import os
from datetime import datetime, timedelta
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from bson import json_util

equipment_performance = Blueprint('equipment_performance', __name__)

# MongoDB Atlas connection string
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://nikhilvjagtap2003:ra9be97kyhd8wsR9@cluster0.vrqby.mongodb.net/quality_dashboard?retryWrites=true&w=majority')

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.get_database("quality_dashboard")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    db = None

@equipment_performance.route('/equipment_performance')
def show_equipment_performance():
    # Get date range for filtering
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    equipment_id = request.args.get('equipment_id')
    
    # Get summary metrics
    summary_metrics = get_equipment_summary(from_date, to_date, equipment_id)
    
    # Get equipment list for dropdown
    equipment_list = get_equipment_list()
    
    return render_template('equipment_performance.html', 
                          summary=summary_metrics,
                          equipment_list=equipment_list)

@equipment_performance.route('/equipment_performance/summary')
def get_equipment_summary_data():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    equipment_id = request.args.get('equipment_id')
    
    summary = get_equipment_summary(from_date, to_date, equipment_id)
    return jsonify(summary)

@equipment_performance.route('/equipment_performance/oee_trend')
def get_oee_trend_data():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    equipment_id = request.args.get('equipment_id')
    
    # Get OEE trend data
    trend_data = get_oee_trend(from_date, to_date, equipment_id)
    return jsonify(trend_data)

@equipment_performance.route('/equipment_performance/component_trend')
def get_component_trend_data():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    equipment_id = request.args.get('equipment_id')
    
    # Get component trend data (availability, performance, quality)
    component_data = get_component_trend(from_date, to_date, equipment_id)
    return jsonify(component_data)

@equipment_performance.route('/equipment_performance/downtime_pareto')
def get_downtime_pareto_data():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    equipment_id = request.args.get('equipment_id')
    
    # Get downtime pareto data
    downtime_data = get_downtime_pareto(from_date, to_date, equipment_id)
    return jsonify(downtime_data)

@equipment_performance.route('/equipment_performance/add_data', methods=['GET', 'POST'])
def add_equipment_data():
    if request.method == 'POST':
        try:
            # Parse the form data
            data = {
                'equipment_id': request.form.get('equipment_id'),
                'equipment_name': request.form.get('equipment_name'),
                'date': request.form.get('date'),
                'shift': request.form.get('shift'),
                'planned_production_time': float(request.form.get('planned_production_time')),
                'actual_production_time': float(request.form.get('actual_production_time')),
                'ideal_cycle_time': float(request.form.get('ideal_cycle_time')),
                'total_pieces': int(request.form.get('total_pieces')),
                'good_pieces': int(request.form.get('good_pieces')),
                'downtime_reasons': json.loads(request.form.get('downtime_reasons', '[]')),
                'created_at': datetime.now()
            }
            
            # Calculate OEE components
            availability = data['actual_production_time'] / data['planned_production_time'] if data['planned_production_time'] > 0 else 0
            performance = (data['total_pieces'] * data['ideal_cycle_time']) / data['actual_production_time'] if data['actual_production_time'] > 0 else 0
            quality = data['good_pieces'] / data['total_pieces'] if data['total_pieces'] > 0 else 0
            
            # Calculate OEE
            oee = availability * performance * quality
            
            # Add calculated fields
            data['availability'] = round(availability * 100, 2)
            data['performance'] = round(performance * 100, 2)
            data['quality'] = round(quality * 100, 2)
            data['oee'] = round(oee * 100, 2)
            
            # Insert into database
            if db is not None:
                db.equipment_performance.insert_one(data)
                return jsonify({'success': True, 'message': 'Data added successfully'})
            else:
                return jsonify({'success': False, 'message': 'Database connection error'})
                
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    
    # If GET request, return the form template
    equipment_list = get_equipment_list()
    return render_template('equipment_data_form.html', equipment_list=equipment_list)

# Helper functions
def get_equipment_summary(from_date=None, to_date=None, equipment_id=None):
    if db is None:
        return {
            'overall_equipment_effectiveness': 0,
            'availability': 0,
            'performance': 0,
            'quality': 0,
            'total_records': 0
        }
    
    # Build query
    query = {}
    if from_date:
        query['date'] = {'$gte': from_date}
    if to_date:
        if 'date' in query:
            query['date']['$lte'] = to_date
        else:
            query['date'] = {'$lte': to_date}
    if equipment_id:
        query['equipment_id'] = equipment_id
    
    # Get data from MongoDB
    try:
        equipment_data = list(db.equipment_performance.find(query))
        
        if not equipment_data:
            # Return default values if no data
            return {
                'overall_equipment_effectiveness': 0,
                'availability': 0,
                'performance': 0,
                'quality': 0,
                'total_records': 0
            }
        
        # Calculate averages
        df = pd.DataFrame(equipment_data)
        avg_oee = df['oee'].mean()
        avg_availability = df['availability'].mean()
        avg_performance = df['performance'].mean()
        avg_quality = df['quality'].mean()
        
        return {
            'overall_equipment_effectiveness': round(avg_oee, 2),
            'availability': round(avg_availability, 2),
            'performance': round(avg_performance, 2),
            'quality': round(avg_quality, 2),
            'total_records': len(equipment_data)
        }
    except Exception as e:
        print(f"Error getting equipment summary: {e}")
        return {
            'overall_equipment_effectiveness': 0,
            'availability': 0,
            'performance': 0,
            'quality': 0,
            'total_records': 0,
            'error': str(e)
        }

def get_oee_trend(from_date=None, to_date=None, equipment_id=None):
    if db is None:
        return {'dates': [], 'oee_values': []}
    
    # Build query
    query = {}
    if from_date:
        query['date'] = {'$gte': from_date}
    if to_date:
        if 'date' in query:
            query['date']['$lte'] = to_date
        else:
            query['date'] = {'$lte': to_date}
    if equipment_id:
        query['equipment_id'] = equipment_id
    
    # Get data from MongoDB
    try:
        equipment_data = list(db.equipment_performance.find(query).sort('date', 1))
        
        if not equipment_data:
            return {'dates': [], 'oee_values': []}
        
        # Convert to DataFrame and group by date
        df = pd.DataFrame(equipment_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Group by date and calculate average OEE
        daily_oee = df.groupby(df['date'].dt.date)['oee'].mean().reset_index()
        
        return {
            'dates': [d.strftime('%Y-%m-%d') for d in daily_oee['date']],
            'oee_values': daily_oee['oee'].tolist()
        }
    except Exception as e:
        print(f"Error getting OEE trend: {e}")
        return {'dates': [], 'oee_values': [], 'error': str(e)}

def get_component_trend(from_date=None, to_date=None, equipment_id=None):
    if db is None:
        return {
            'dates': [],
            'availability_values': [],
            'performance_values': [],
            'quality_values': []
        }
    
    # Build query
    query = {}
    if from_date:
        query['date'] = {'$gte': from_date}
    if to_date:
        if 'date' in query:
            query['date']['$lte'] = to_date
        else:
            query['date'] = {'$lte': to_date}
    if equipment_id:
        query['equipment_id'] = equipment_id
    
    # Get data from MongoDB
    try:
        equipment_data = list(db.equipment_performance.find(query).sort('date', 1))
        
        if not equipment_data:
            return {
                'dates': [],
                'availability_values': [],
                'performance_values': [],
                'quality_values': []
            }
        
        # Convert to DataFrame and group by date
        df = pd.DataFrame(equipment_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Group by date and calculate average components
        daily_data = df.groupby(df['date'].dt.date).agg({
            'availability': 'mean',
            'performance': 'mean',
            'quality': 'mean'
        }).reset_index()
        
        return {
            'dates': [d.strftime('%Y-%m-%d') for d in daily_data['date']],
            'availability_values': daily_data['availability'].tolist(),
            'performance_values': daily_data['performance'].tolist(),
            'quality_values': daily_data['quality'].tolist()
        }
    except Exception as e:
        print(f"Error getting component trend: {e}")
        return {
            'dates': [],
            'availability_values': [],
            'performance_values': [],
            'quality_values': [],
            'error': str(e)
        }

def get_downtime_pareto(from_date=None, to_date=None, equipment_id=None):
    if db is None:
        return {'reasons': [], 'durations': []}
    
    # Build query
    query = {}
    if from_date:
        query['date'] = {'$gte': from_date}
    if to_date:
        if 'date' in query:
            query['date']['$lte'] = to_date
        else:
            query['date'] = {'$lte': to_date}
    if equipment_id:
        query['equipment_id'] = equipment_id
    
    # Get data from MongoDB
    try:
        equipment_data = list(db.equipment_performance.find(query))
        
        if not equipment_data:
            return {'reasons': [], 'durations': []}
        
        # Extract downtime reasons and aggregate
        downtime_reasons = {}
        for record in equipment_data:
            if 'downtime_reasons' in record:
                for reason in record['downtime_reasons']:
                    if reason['reason'] in downtime_reasons:
                        downtime_reasons[reason['reason']] += reason['duration']
                    else:
                        downtime_reasons[reason['reason']] = reason['duration']
        
        # Sort by duration (descending)
        sorted_reasons = sorted(downtime_reasons.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'reasons': [item[0] for item in sorted_reasons],
            'durations': [item[1] for item in sorted_reasons]
        }
    except Exception as e:
        print(f"Error getting downtime pareto: {e}")
        return {'reasons': [], 'durations': [], 'error': str(e)}

def get_equipment_list():
    if db is None:
        return []
    
    try:
        # Get distinct equipment IDs and names
        equipment_data = list(db.equipment_performance.find({}, {'equipment_id': 1, 'equipment_name': 1, '_id': 0}).distinct('equipment_id'))
        
        # If no data, return empty list
        if not equipment_data:
            return []
        
        # Get equipment names for each ID
        equipment_list = []
        for eq_id in equipment_data:
            eq_record = db.equipment_performance.find_one({'equipment_id': eq_id}, {'equipment_id': 1, 'equipment_name': 1, '_id': 0})
            if eq_record:
                equipment_list.append({
                    'id': eq_record['equipment_id'],
                    'name': eq_record['equipment_name']
                })
        
        return equipment_list
    except Exception as e:
        print(f"Error getting equipment list: {e}")
        return []
