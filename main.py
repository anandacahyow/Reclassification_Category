import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# File uploader widget
uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file is not None:
    # Read the Excel file
    df = pd.read_excel(uploaded_file)

    # Convert datetime columns to datetime objects
    df['Start Datetime'] = pd.to_datetime(df['Start Datetime'])
    df['End Datetime'] = pd.to_datetime(df['End Datetime'])

    # Map Original Category values to colors
    color_map = {
        "Production Time": "green",
        "Unplanned Stoppages": "red",
        "Not Occupied": "grey",
        "Planned Stoppages": "yellow"
    }

    # Add a new column for colors
    df['Color'] = df['Original Category'].map(color_map)

    # Create traces for each category
    data = []
    for i, row in df.iterrows():
        trace = go.Bar(
            y=[row['Original Category']],
            x=[(row['End Datetime'] - row['Start Datetime']).total_seconds() / 3600],  # Duration in hours
            orientation='h',
            marker=dict(color=row['Color']),
            name=row['Original Category']
        )
        data.append(trace)

    # Layout
    layout = go.Layout(
        title='Duration of Original Categories',
        yaxis=dict(
            title='Original Category'
        ),
        xaxis=dict(
            title='Duration (hours)'
        ),
        barmode='stack'
    )

    # Create the figure
    fig = go.Figure(data=data, layout=layout)

    # Show the plot
    st.plotly_chart(fig)
