from io import BytesIO
from flask import Blueprint, json, render_template, jsonify, request, send_file
from pymongo import MongoClient
import os
from datetime import datetime
import plotly.express as px
import pandas as pd
from bson import json_util
import plotly.graph_objects as go
import openpyxl

production_overview = Blueprint('production_overview', __name__)

# MongoDB Atlas connection string
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://nikhilvjagtap2003:ra9be97kyhd8wsR9@cluster0.vrqby.mongodb.net/quality_dashboard?retryWrites=true&w=majority')

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.get_database("quality_dashboard")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    db = None

@production_overview.route('/production_overview')
def show_production_overview():
    if db is None:
        return jsonify({'error': 'Database connection error'}), 500
        
    try:
        # Fetch all coil data from MongoDB, sorted by serial number
        coil_data = list(db.coil_production.find({}, {'_id': 0}).sort('slNo', 1))

        # Fetch daily production data
        daily_output = list(db.daily_production.find({}, {
            '_id': 0,
            'date': 1,
            'output': 1
        }).sort('date', 1))

        # Fetch production distribution data
        distribution_data = list(db.production_distribution.find({}, {
            '_id': 0,
            'product': 1,
            'number_of_products': 1
        }))

        # Generate charts
        daily_output_chart = generate_daily_output_chart(daily_output)
        distribution_chart = generate_distribution_chart(distribution_data)
        coil_chart = generate_coil_chart(coil_data)
        daily_production_chart = generate_daily_production_chart(coil_data)
            
        return render_template(
            'production_overview.html', 
            coil_data=coil_data,
            coil_chart=coil_chart,
            daily_output_chart=daily_output_chart,
            distribution_chart=distribution_chart,
            monthly_production_chart=daily_production_chart  # Keep variable name for template compatibility
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update the get_chart_data function to handle different chart types
@production_overview.route('/production_overview/chart_data')
def get_chart_data():
    if db is None:
        return jsonify({'error': 'Database connection error'}), 500
        
    try:
        # Get filter parameters
        chart_type = request.args.get('chart_type', 'all')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        # Build query for coil data
        query = {}
        if from_date and to_date:
            query['clearanceDate'] = {
                '$gte': from_date,
                '$lte': to_date
            }

        # Fetch filtered data
        coil_data = list(db.coil_production.find(query, {'_id': 0}))
        daily_output = list(db.daily_production.find({}, {'_id': 0}))
        distribution_data = list(db.production_distribution.find({}, {'_id': 0}))

        # Generate charts based on chart_type
        charts = {}
        
        if chart_type == 'all' or chart_type == 'coil':
            charts['coil_chart'] = generate_coil_chart(coil_data)
            charts['daily_output_chart'] = generate_daily_output_chart(daily_output)
            charts['distribution_chart'] = generate_distribution_chart(distribution_data)
        
        return jsonify(charts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add a new endpoint for daily production chart with its own filters
@production_overview.route('/production_overview/daily_chart_data')
def get_daily_chart_data():
    if db is None:
        return jsonify({'error': 'Database connection error'}), 500
        
    try:
        # Get filter parameters specific to daily production chart
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        # Build query for coil data
        query = {}
        if from_date and to_date:
            query['clearanceDate'] = {
                '$gte': from_date,
                '$lte': to_date
            }

        # Fetch filtered data
        coil_data = list(db.coil_production.find(query, {'_id': 0}))

        # Generate only the daily production chart
        daily_production_chart = generate_daily_production_chart(coil_data)
        
        return jsonify({'daily_production_chart': daily_production_chart})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@production_overview.route('/production_overview/table_data')
def get_table_data():
    if db is None:
        return jsonify({'error': 'Database connection error'}), 500
        
    try:
        # Get filter parameters
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        serial_no = request.args.get('serial_no')

        # Build query
        query = {}
        if from_date and to_date:
            query['clearanceDate'] = {
                '$gte': from_date,
                '$lte': to_date
            }
        if serial_no:
            query['serialNo'] = {'$regex': serial_no, '$options': 'i'}

        # Fetch filtered data and sort by serial number
        coil_data = list(db.coil_production.find(query, {'_id': 0}).sort('slNo', 1))
        
        return jsonify({'coil_data': json.loads(json_util.dumps(coil_data))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update the export_data function to handle different export types correctly
@production_overview.route('/export_data')
def export_data():
  try:
      from_date = request.args.get('from_date', None)
      to_date = request.args.get('to_date', None)
      serial_no = request.args.get('serial_no', None)
      export_type = request.args.get('type', 'chart')
      
      # Get sorting parameters
      sort_by = request.args.get('sort_by', None)
      sort_direction = request.args.get('sort_direction', None)

      # Build query
      query = {}
      if from_date and to_date:
          # Don't convert to datetime here, keep as string for MongoDB query
          query['clearanceDate'] = {
              '$gte': from_date,
              '$lte': to_date
          }
      if serial_no:
          query['serialNo'] = {'$regex': serial_no, '$options': 'i'}

      # Print query for debugging
      print(f"Export query: {query}")
      
      # Only apply sorting if sort parameters are provided
      if sort_by and sort_direction and export_type == 'table':
          # Determine sort direction for MongoDB
          mongo_sort_direction = 1 if sort_direction == 'asc' else -1
          # Use MongoDB's sorting
          data = list(db.coil_production.find(query, {'_id': 0}).sort(sort_by, mongo_sort_direction))
      else:
          # No sorting applied, just fetch the data
          data = list(db.coil_production.find(query, {'_id': 0}))
      
      # Print number of records found
      print(f"Found {len(data)} records for export")
      
      # Convert to DataFrame
      df = pd.DataFrame(data)
      
      # If DataFrame is empty, add a message
      if df.empty:
          df = pd.DataFrame([{'Message': 'No data found for the selected filters'}])
      
      # Create Excel file in memory
      output = BytesIO()
      
      # Use openpyxl engine instead of xlsxwriter
      with pd.ExcelWriter(output, engine='openpyxl') as writer:
          # Get the workbook and worksheet
          workbook = writer.book
          
          # Create a new worksheet for the data
          worksheet = workbook.create_sheet("Data")
          
          # Add title row
          worksheet.cell(row=1, column=1, value="Coil Production Data")
          worksheet.cell(row=1, column=1).font = openpyxl.styles.Font(bold=True, size=14)
          worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=5)
          
          # Track the current row for dynamic positioning
          current_row = 2
          
          # Add filter information row
          filter_info = ""
          if from_date and to_date:
              filter_info = f"Date Range: {from_date} to {to_date}"
          elif from_date:
              filter_info = f"Date From: {from_date}"
          elif to_date:
              filter_info = f"Date To: {to_date}"
          
          if serial_no:
              filter_info += f" | Serial No: {serial_no}" if filter_info else f"Serial No: {serial_no}"
              
          if filter_info:
              worksheet.cell(row=current_row, column=1, value=filter_info)
              worksheet.cell(row=current_row, column=1).font = openpyxl.styles.Font(italic=True)
              worksheet.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=5)
              current_row += 1
          
          # Add sorting information row only for table exports with explicit sorting
          if export_type == 'table' and sort_by and sort_direction:
              sort_info = f"Sorted by: {sort_by} ({sort_direction})"
              worksheet.cell(row=current_row, column=1, value=sort_info)
              worksheet.cell(row=current_row, column=1).font = openpyxl.styles.Font(italic=True)
              worksheet.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=5)
              current_row += 1
          
          # Add an empty row between filter/sort info and table data
          current_row += 1
          
          # Write column headers
          header_row = current_row
          for c_idx, column in enumerate(df.columns, 1):
              worksheet.cell(row=header_row, column=c_idx, value=column)
              worksheet.cell(row=header_row, column=c_idx).font = openpyxl.styles.Font(bold=True)
          
          # Write the DataFrame starting from the row after headers
          for r_idx, row in enumerate(df.iterrows(), header_row + 1):
              for c_idx, value in enumerate(row[1], 1):
                  worksheet.cell(row=r_idx, column=c_idx, value=value)
          
          # Remove the default sheet
          if "Sheet" in workbook.sheetnames:
              del workbook["Sheet"]
      
      output.seek(0)
      
      # Generate filename with current timestamp
      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      
      return send_file(
          output,
          mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          as_attachment=True,
          download_name=f'coil_production_{export_type}_{timestamp}.xlsx'
      )
  except Exception as e:
      print(f"Export error: {str(e)}")
      return jsonify({'error': str(e)}), 500

def generate_coil_chart(coil_data):
    if not coil_data:
        return None

    df = pd.DataFrame(coil_data)
    
    # Convert clearanceDate to datetime and sort
    df['clearanceDate'] = pd.to_datetime(df['clearanceDate'])
    df = df.sort_values('clearanceDate')
    
    fig = go.Figure()

    # Thickness comparison
    fig.add_trace(go.Scatter(
        x=df['clearanceDate'],
        y=df['planThickness'],
        name='Planned Thickness',
        line=dict(color='#1f77b4', width=2),
        mode='lines+markers',
        hovertemplate="<b>Serial No:</b> %{customdata}<br>" +
                     "<b>Date:</b> %{x|%Y-%m-%d %H:%M:%S}<br>" +
                     "<b>Planned Thickness:</b> %{y:.2f} mm<extra></extra>",
        customdata=df['serialNo']
    ))
    fig.add_trace(go.Scatter(
        x=df['clearanceDate'],
        y=df['finalThk'],
        name='Final Thickness',
        line=dict(color='#ff7f0e', width=2),
        mode='lines+markers',
        hovertemplate="<b>Serial No:</b> %{customdata}<br>" +
                     "<b>Date:</b> %{x|%Y-%m-%d %H:%M:%S}<br>" +
                     "<b>Final Thickness:</b> %{y:.2f} mm<extra></extra>",
        customdata=df['serialNo']
    ))

    # Width comparison
    fig.add_trace(go.Scatter(
        x=df['clearanceDate'],
        y=df['planWidth'],
        name='Planned Width',
        line=dict(color='#2ca02c', width=2),
        mode='lines+markers',
        yaxis='y2',
        hovertemplate="<b>Serial No:</b> %{customdata}<br>" +
                     "<b>Date:</b> %{x|%Y-%m-%d %H:%M:%S}<br>" +
                     "<b>Planned Width:</b> %{y:.0f} mm<extra></extra>",
        customdata=df['serialNo']
    ))
    fig.add_trace(go.Scatter(
        x=df['clearanceDate'],
        y=df['finalWidth'],
        name='Final Width',
        line=dict(color='#d62728', width=2),
        mode='lines+markers',
        yaxis='y2',
        hovertemplate="<b>Serial No:</b> %{customdata}<br>" +
                     "<b>Date:</b> %{x|%Y-%m-%d %H:%M:%S}<br>" +
                     "<b>Final Width:</b> %{y:.0f} mm<extra></extra>",
        customdata=df['serialNo']
    ))

    # Customize the layout
    fig.update_layout(
        title='Coil Production Analysis',
        xaxis=dict(
            title='Date and Time',
            tickangle=45,
            tickformat='%Y-%m-%d %H:%M:%S',
            tickfont=dict(size=10),
            type='date'
        ),
        yaxis=dict(
            title='Thickness (mm)',
            side='left',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis2=dict(
            title='Width (mm)',
            side='right',
            overlaying='y',
            showgrid=False,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1
        ),
        hovermode='x unified',
        plot_bgcolor='rgba(240, 240, 240, 0.8)',
        width=900,
        height=600,
        margin=dict(l=50, r=50, t=80, b=50)
    )

    # Add shapes to highlight deviations
    for i, row in df.iterrows():
        if abs(row['planThickness'] - row['finalThk']) > 0.1:
            fig.add_shape(
                type="rect",
                x0=row['clearanceDate'],
                x1=row['clearanceDate'],
                y0=0,
                y1=1,
                yref="paper",
                fillcolor="rgba(255, 0, 0, 0.1)",
                line_width=0,
                layer="below"
            )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def generate_distribution_chart(distribution_data):
    distribution_data = list(db.production_distribution.find({}, {
        '_id': 0,
        'product': 1,
        'number_of_products': 1
    }))

    if not distribution_data:
        return None

    df = pd.DataFrame(distribution_data)
    
    # Calculate percentages
    total_products = df['number_of_products'].sum()
    df['percentage'] = (df['number_of_products'] / total_products * 100).round(1)
    
    # Sort by percentage in descending order
    df = df.sort_values('percentage', ascending=False)
    
    colors = [
        'rgb(82, 113, 255)',   # Blue
        'rgb(255, 99, 71)',    # Coral
        'rgb(34, 197, 94)',    # Green
        'rgb(168, 85, 247)',   # Purple
        'rgb(251, 146, 60)',   # Orange
        'rgb(236, 72, 153)',   # Pink
        'rgb(234, 179, 8)'     # Yellow
    ]

    fig = go.Figure(data=[go.Pie(
        labels=df['product'],
        values=df['percentage'],
        hole=0.4,
        marker=dict(colors=colors),
        textinfo='label+percent',
        hovertemplate="<b>%{label}</b><br>" +
                     "Percentage: %{percent}<br>" +
                     "Number of Products: %{customdata:,}<br>" +
                     "<extra></extra>",
        texttemplate="%{percent}",
        customdata=df['number_of_products'],
        textposition='outside',
        textfont=dict(size=10)
    )])

    fig.update_layout(
        title=dict(
            text='Production Distribution by Products',  # Shortened title
            x=0.75,
            y=0.95,
            xanchor='right',
            yanchor='top',
            font=dict(size=18)  # Reduced font size
        ),
        showlegend=False,
        height=400,        # Further reduced height
        margin=dict(l=40, r=40, t=40, b=40),  
        plot_bgcolor='white'
    )

    # Update the total products annotation position
    fig.add_annotation(
        text=f"Total Products: {total_products:,}",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.1,  # Move below the chart
        showarrow=False,
        font=dict(size=14),
        xanchor='center'
    )

    return fig.to_html(
        full_html=False,
        include_plotlyjs='cdn',
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'responsive': True
        }
    )

# Rename the function for clarity while keeping the original name for compatibility
def generate_monthly_production_chart(coil_data):
    """
    This function generates a daily production chart based on clearance dates.
    The name is kept for backward compatibility.
    """
    return generate_daily_production_chart(coil_data)

# Add a new function with a more appropriate name
def generate_daily_production_chart(coil_data):
    """
    Generates a daily production chart showing the number of coils produced each day.
    """
    if not coil_data:
        return None

    df = pd.DataFrame(coil_data)
    
    # Convert clearanceDate to datetime
    df['clearanceDate'] = pd.to_datetime(df['clearanceDate'])
    
    # Extract date from clearanceDate (without time)
    df['production_date'] = df['clearanceDate'].dt.date
    
    # Group by date and count coils
    daily_counts = df.groupby('production_date').size().reset_index(name='count')
    daily_counts = daily_counts.sort_values('production_date')
    
    # Create the bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily_counts['production_date'],
        y=daily_counts['count'],
        marker_color='rgb(55, 83, 109)',
        text=daily_counts['count'],
        textposition='auto',
    ))
    
    fig.update_layout(
        title='Daily Coil Production',
        xaxis_title='Date',
        yaxis_title='Number of Coils',
        plot_bgcolor='rgba(242, 244, 247, 1)',
        paper_bgcolor='white',
        height=400,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    # If there are too many dates, limit the number of ticks shown
    if len(daily_counts) > 15:
        # Show every nth date to avoid overcrowding
        n = max(1, len(daily_counts) // 15)
        tickvals = daily_counts['production_date'].iloc[::n]
        fig.update_xaxes(
            tickangle=45,
            tickmode='array',
            tickvals=tickvals,
            showgrid=True, 
            gridwidth=1, 
            gridcolor='white'
        )
    else:
        fig.update_xaxes(
            tickangle=45,
            tickmode='array',
            tickvals=daily_counts['production_date'],
            showgrid=True, 
            gridwidth=1, 
            gridcolor='white'
        )
    
    fig.update_yaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor='white'
    )
    
    return fig.to_html(full_html=False)

def generate_daily_output_chart(data):
    if not data:
        return None

    df = pd.DataFrame(data)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['output'],
        marker_color='rgb(82, 113, 255)'
    ))

    fig.update_layout(
        title='Daily Production Output',
        xaxis_title='Date',
        yaxis_title='Production Output',
        plot_bgcolor='rgba(242, 244, 247, 1)',
        paper_bgcolor='white',
        height=400,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='white')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='white')

    return fig.to_html(full_html=False)








