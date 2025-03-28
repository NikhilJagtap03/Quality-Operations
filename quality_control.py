from flask import Blueprint, render_template, jsonify
from pymongo import MongoClient
import os
import plotly.express as px
import pandas as pd

quality_control = Blueprint('quality_control', __name__)

# MongoDB Connection
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://nikhilvjagtap2003:ra9be97kyhd8wsR9@cluster0.vrqby.mongodb.net/quality_dashboard?retryWrites=true&w=majority')

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.get_database("quality_dashboard")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    db = None

@quality_control.route('/quality_control')
def show_quality_control():
    if db is None:
        return jsonify({'error': 'Database connection error'}), 500
    
    try:
        # Fetch quality data
        quality_data = list(db.quality_control.find({}, {'_id': 0}))
        if not quality_data:
            return render_template('quality_control.html', data=None, chart=None)
        
        # Convert to DataFrame for visualization
        df = pd.DataFrame(quality_data)
        
        # Ensure defect_rate is numeric
        df['defect_rate'] = pd.to_numeric(df['defect_rate'], errors='coerce')
        
        # Sort data by defect_rate in ascending order
        df = df.sort_values(by='defect_rate')
        
        # Generate interactive chart
        chart_html = generate_interactive_chart(df)
        
        return render_template('quality_control.html', data=quality_data, chart=chart_html)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_interactive_chart(df):
    fig = px.bar(
        df,
        x='category',
        y='defect_rate',
        text='defect_rate',
        title='Defect Rate by Category',
        labels={'defect_rate': 'Defect Rate (%)', 'category': 'Category'},
        color='defect_rate',
        color_continuous_scale='Reds',
        hover_data=['quality_score', 'compliance']
    )
    
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor='rgba(242, 244, 247, 1)',
        height=500,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')