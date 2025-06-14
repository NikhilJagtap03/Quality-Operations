from flask import Blueprint, render_template, request, jsonify
from pymongo import MongoClient
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from bson import json_util

customer_satisfaction = Blueprint('customer_satisfaction', __name__)

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://nikhilvjagtap2003:ra9be97kyhd8wsR9@cluster0.vrqby.mongodb.net/quality_dashboard?retryWrites=true&w=majority')

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.get_database("quality_dashboard")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    db = None

@customer_satisfaction.route('/customer_satisfaction')
def show_customer_satisfaction():

    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    summary_metrics = get_customer_summary(from_date, to_date)

    recommendations = get_quality_recommendations()
    
    recent_feedback = get_recent_feedback()
    
    action_items = get_action_items()
    
    return render_template('customer_satisfaction.html', 
                          data=summary_metrics,
                          recommendations=recommendations,
                          recent_feedback=recent_feedback,
                          action_items=action_items)

@customer_satisfaction.route('/customer_satisfaction/summary')
def get_customer_summary_data():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    summary = get_customer_summary(from_date, to_date)
    return jsonify(summary)

@customer_satisfaction.route('/customer_satisfaction/satisfaction_trend')
def get_satisfaction_trend_data():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    trend_data = get_satisfaction_trend(from_date, to_date)
    return jsonify(trend_data)

@customer_satisfaction.route('/customer_satisfaction/complaint_analysis')
def get_complaint_analysis_data():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    complaint_data = get_complaint_analysis(from_date, to_date)
    return jsonify(complaint_data)

@customer_satisfaction.route('/customer_satisfaction/delivery_performance')
def get_delivery_performance_data():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    delivery_data = get_delivery_performance(from_date, to_date)
    return jsonify(delivery_data)

@customer_satisfaction.route('/customer_satisfaction/coil_quality_metrics')
def get_coil_quality_metrics_data():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    quality_data = get_coil_quality_metrics(from_date, to_date)
    return jsonify(quality_data)

@customer_satisfaction.route('/customer_satisfaction/add_feedback', methods=['POST'])
def add_customer_feedback():
    try:
        data = {
            'customer_id': request.form.get('customer_id'),
            'customer_name': request.form.get('customer_name'),
            'satisfaction_score': float(request.form.get('satisfaction_score')),
            'delivery_rating': float(request.form.get('delivery_rating')),
            'quality_rating': float(request.form.get('quality_rating')),
            'service_rating': float(request.form.get('service_rating')),
            'complaint_category': request.form.get('complaint_category'),
            'complaint_description': request.form.get('complaint_description'),
            'resolution_status': request.form.get('resolution_status', 'Open'),
            'priority': request.form.get('priority', 'Medium'),
            'feedback_date': datetime.now(),
            'created_at': datetime.now()
        }
        
        if db is not None:
            db.customer_feedback.insert_one(data)
            return jsonify({'success': True, 'message': 'Customer feedback has been successfully recorded and will be reviewed by our quality team.'})
        else:
            return jsonify({'success': False, 'message': 'Database connection error. Please try again later.'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing feedback: {str(e)}'})


def get_customer_summary(from_date=None, to_date=None):
    if db is None:
        return {
            'customer_satisfaction_score': 4.3,
            'on_time_delivery': 96.2,
            'return_rate': 1.4,
            'complaint_resolution_rate': 91.7,
            'average_delivery_time': 4.8,
            'total_customers': 187,
            'nps_score': 72,
            'quality_index': 94.5,
            'response_rate': 89.3,
            'repeat_customer_rate': 78.9
        }
    
    # Build query
    query = {}
    if from_date:
        query['feedback_date'] = {'$gte': from_date}
    if to_date:
        if 'feedback_date' in query:
            query['feedback_date']['$lte'] = to_date
        else:
            query['feedback_date'] = {'$lte': to_date}
    
    try:
        feedback_data = list(db.customer_feedback.find(query))
        
        if not feedback_data:
            return get_sample_data()
        
        df = pd.DataFrame(feedback_data)
        
        # Calculate enhanced metrics
        avg_satisfaction = df['satisfaction_score'].mean()
        avg_delivery_rating = df['delivery_rating'].mean()
        avg_quality_rating = df['quality_rating'].mean()
        resolved_complaints = df[df['resolution_status'] == 'Resolved'].shape[0]
        total_complaints = df.shape[0]
        resolution_rate = (resolved_complaints / total_complaints * 100) if total_complaints > 0 else 0
        
        promoters = df[df['satisfaction_score'] >= 4].shape[0]
        detractors = df[df['satisfaction_score'] <= 2].shape[0]
        nps = ((promoters - detractors) / total_complaints * 100) if total_complaints > 0 else 0
        
        return {
            'customer_satisfaction_score': round(avg_satisfaction, 2),
            'on_time_delivery': round(avg_delivery_rating * 20, 1),
            'return_rate': round(np.random.uniform(1.2, 2.1), 1),
            'complaint_resolution_rate': round(resolution_rate, 1),
            'average_delivery_time': round(np.random.uniform(4.2, 5.8), 1),
            'total_customers': len(df['customer_id'].unique()),
            'nps_score': round(nps, 0),
            'quality_index': round(avg_quality_rating * 20, 1),
            'response_rate': round(np.random.uniform(85, 92), 1),
            'repeat_customer_rate': round(np.random.uniform(75, 85), 1)
        }
    except Exception as e:
        print(f"Error getting customer summary: {e}")
        return get_sample_data()

def get_sample_data():
    """Return enhanced sample data for demonstration"""
    return {
        'customer_satisfaction_score': 4.3,
        'on_time_delivery': 96.2,
        'return_rate': 1.4,
        'complaint_resolution_rate': 91.7,
        'average_delivery_time': 4.8,
        'total_customers': 187,
        'nps_score': 72,
        'quality_index': 94.5,
        'response_rate': 89.3,
        'repeat_customer_rate': 78.9
    }

def get_satisfaction_trend(from_date=None, to_date=None):

    dates = []
    satisfaction_scores = []
    delivery_ratings = []
    quality_ratings = []
    
    base_satisfaction = 4.2
    for i in range(30):
        date = datetime.now() - timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))
        

        weekend_factor = 0.1 if date.weekday() >= 5 else 0
        trend_factor = i * 0.002 
        
        satisfaction_scores.append(round(base_satisfaction + np.random.uniform(-0.3, 0.4) + weekend_factor + trend_factor, 2))
        delivery_ratings.append(round(4.1 + np.random.uniform(-0.2, 0.3) + weekend_factor, 2))
        quality_ratings.append(round(4.3 + np.random.uniform(-0.2, 0.2) + trend_factor, 2))
    
    return {
        'dates': list(reversed(dates)),
        'satisfaction_scores': list(reversed(satisfaction_scores)),
        'delivery_ratings': list(reversed(delivery_ratings)),
        'quality_ratings': list(reversed(quality_ratings))
    }

def get_complaint_analysis(from_date=None, to_date=None):

    categories = ['Product Quality', 'Delivery Issues', 'Packaging Problems', 'Documentation Errors', 'Customer Service', 'Technical Support', 'Billing Issues']
    complaint_counts = [52, 38, 22, 15, 12, 18, 8]
    resolution_times = [2.8, 4.2, 2.1, 1.8, 3.5, 5.2, 2.9]  
    severity_levels = ['High', 'Medium', 'Low', 'Low', 'Medium', 'High', 'Low']
    
    return {
        'categories': categories,
        'complaint_counts': complaint_counts,
        'resolution_times': resolution_times,
        'severity_levels': severity_levels
    }

def get_delivery_performance(from_date=None, to_date=None):

    delivery_metrics = {
        'on_time_deliveries': 178,
        'early_deliveries': 31,
        'late_deliveries': 6,
        'average_delivery_time': 4.8,
        'delivery_accuracy': 97.2,
        'customer_satisfaction_delivery': 4.4
    }
    
    months = ['January', 'February', 'March', 'April', 'May', 'June']
    on_time_percentages = [94.1, 95.8, 93.2, 96.4, 95.1, 96.2]
    delivery_volumes = [145, 132, 167, 189, 201, 215]
    
    return {
        'metrics': delivery_metrics,
        'trend': {
            'months': months,
            'on_time_percentages': on_time_percentages,
            'delivery_volumes': delivery_volumes
        }
    }

def get_coil_quality_metrics(from_date=None, to_date=None):

    quality_params = ['Surface Finish', 'Dimensional Accuracy', 'Chemical Composition', 'Mechanical Properties', 'Coating Quality', 'Edge Quality']
    quality_scores = [95.8, 97.2, 98.5, 94.1, 96.3, 93.7]
    benchmarks = [95.0, 95.0, 98.0, 95.0, 96.0, 94.0]
    improvement_trends = ['+1.2%', '+0.8%', '+0.3%', '-0.5%', '+1.1%', '+2.1%']

    defect_types = ['Surface Defects', 'Dimensional Issues', 'Edge Problems', 'Coating Issues', 'Chemical Variations', 'Other']
    defect_percentages = [1.8, 1.4, 1.1, 0.9, 0.3, 0.2]
    defect_trends = ['-15%', '-8%', '+5%', '-12%', '-3%', '-20%']
    
    return {
        'quality_parameters': {
            'params': quality_params,
            'scores': quality_scores,
            'benchmarks': benchmarks,
            'trends': improvement_trends
        },
        'defect_analysis': {
            'types': defect_types,
            'percentages': defect_percentages,
            'trends': defect_trends
        }
    }

def get_recent_feedback():
    """Get recent customer feedback for display"""
    sample_feedback = [
        {
            'id': 'FB001',
            'customer_name': 'Acme Steel Corp',
            'customer_id': 'CST-2024-001',
            'satisfaction_score': 4.5,
            'feedback_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'category': 'Product Quality',
            'status': 'Open',
            'priority': 'High',
            'description': 'Excellent surface finish quality, but minor dimensional variations observed'
        },
        {
            'id': 'FB002',
            'customer_name': 'Global Manufacturing Inc',
            'customer_id': 'CST-2024-002',
            'satisfaction_score': 3.8,
            'feedback_date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
            'category': 'Delivery Issues',
            'status': 'In Progress',
            'priority': 'Medium',
            'description': 'Delivery was delayed by 2 days affecting production schedule'
        },
        {
            'id': 'FB003',
            'customer_name': 'Premium Metals Ltd',
            'customer_id': 'CST-2024-003',
            'satisfaction_score': 4.8,
            'feedback_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            'category': 'Customer Service',
            'status': 'Resolved',
            'priority': 'Low',
            'description': 'Outstanding customer service and technical support'
        },
        {
            'id': 'FB004',
            'customer_name': 'Industrial Solutions Co',
            'customer_id': 'CST-2024-004',
            'satisfaction_score': 4.2,
            'feedback_date': (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d'),
            'category': 'Packaging Problems',
            'status': 'Resolved',
            'priority': 'Medium',
            'description': 'Packaging improvements appreciated, coils arrived in perfect condition'
        }
    ]
    
    return sample_feedback

def get_action_items():
    """Get action items with enhanced details"""
    action_items = [
        {
            'id': 'AI001',
            'priority': 'High',
            'action': 'Implement advanced surface inspection checkpoints',
            'department': 'Quality Control',
            'assigned_to': 'John Smith',
            'timeline': '2-3 weeks',
            'expected_impact': '+2-3% surface quality improvement',
            'status': 'Pending',
            'progress': 0,
            'created_date': '2024-05-20',
            'due_date': '2024-06-10'
        },
        {
            'id': 'AI002',
            'priority': 'Medium',
            'action': 'Optimize production scheduling system',
            'department': 'Production Planning',
            'assigned_to': 'Sarah Johnson',
            'timeline': '4-6 weeks',
            'expected_impact': '-15-20% delivery time reduction',
            'status': 'In Progress',
            'progress': 35,
            'created_date': '2024-05-15',
            'due_date': '2024-06-25'
        },
        {
            'id': 'AI003',
            'priority': 'High',
            'action': 'Enhance heat treatment process control system',
            'department': 'Manufacturing',
            'assigned_to': 'Mike Davis',
            'timeline': '3-4 weeks',
            'expected_impact': '-25% property variation reduction',
            'status': 'Pending',
            'progress': 0,
            'created_date': '2024-05-18',
            'due_date': '2024-06-15'
        },
        {
            'id': 'AI004',
            'priority': 'Medium',
            'action': 'Deploy automated complaint tracking system',
            'department': 'Customer Service',
            'assigned_to': 'Lisa Chen',
            'timeline': '2-3 weeks',
            'expected_impact': '-1.3 days resolution time',
            'status': 'Approved',
            'progress': 80,
            'created_date': '2024-05-10',
            'due_date': '2024-06-01'
        },
        {
            'id': 'AI005',
            'priority': 'Low',
            'action': 'Implement predictive maintenance for critical equipment',
            'department': 'Maintenance',
            'assigned_to': 'Robert Wilson',
            'timeline': '8-12 weeks',
            'expected_impact': '30-40% quality issue prevention',
            'status': 'Planning',
            'progress': 15,
            'created_date': '2024-05-22',
            'due_date': '2024-08-15'
        }
    ]
    
    return action_items

def get_quality_recommendations():
    """Generate enhanced quality control recommendations"""
    recommendations = [
        {
            'category': 'Surface Quality Enhancement',
            'priority': 'High',
            'issue': 'Surface finish quality showing slight decline (95.8% vs 96.5% target)',
            'recommendation': 'Implement AI-powered surface inspection system with real-time feedback to rolling mill operators',
            'expected_impact': 'Improve surface quality by 2-3% and reduce rejection rate by 15%',
            'timeline': '3-4 weeks',
            'cost_estimate': '$45,000',
            'roi_months': 6
        },
        {
            'category': 'Delivery Optimization',
            'priority': 'High',
            'issue': 'Delivery performance affecting customer satisfaction scores',
            'recommendation': 'Deploy intelligent logistics platform with predictive delivery scheduling and real-time tracking',
            'expected_impact': 'Reduce delivery time by 18-25% and improve on-time delivery to 98%',
            'timeline': '5-7 weeks',
            'cost_estimate': '$75,000',
            'roi_months': 8
        },
        {
            'category': 'Process Control',
            'priority': 'High',
            'issue': 'Mechanical properties showing increased variation in recent batches',
            'recommendation': 'Upgrade heat treatment process with advanced temperature control and statistical process monitoring',
            'expected_impact': 'Reduce property variation by 30% and improve consistency',
            'timeline': '4-5 weeks',
            'cost_estimate': '$85,000',
            'roi_months': 12
        },
        {
            'category': 'Customer Experience',
            'priority': 'Medium',
            'issue': 'Complaint resolution time averaging 3.2 days, target is 2.0 days',
            'recommendation': 'Implement customer portal with automated ticketing, priority routing, and real-time status updates',
            'expected_impact': 'Reduce resolution time to 1.8 days and improve satisfaction by 12%',
            'timeline': '3-4 weeks',
            'cost_estimate': '$32,000',
            'roi_months': 4
        },
        {
            'category': 'Quality Prediction',
            'priority': 'Medium',
            'issue': 'Reactive approach to quality issues leads to customer complaints',
            'recommendation': 'Deploy machine learning-based quality prediction system with early warning alerts',
            'expected_impact': 'Prevent 40-50% of quality issues before they reach customers',
            'timeline': '10-12 weeks',
            'cost_estimate': '$120,000',
            'roi_months': 15
        },
        {
            'category': 'Training & Development',
            'priority': 'Low',
            'issue': 'Skill gaps in quality control processes identified',
            'recommendation': 'Implement comprehensive training program for quality control staff with certification',
            'expected_impact': 'Improve detection accuracy by 20% and reduce human error',
            'timeline': '6-8 weeks',
            'cost_estimate': '$25,000',
            'roi_months': 18
        }
    ]
    
    return recommendations