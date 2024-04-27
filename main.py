import streamlit as st
import pandas as pd
import plotly.figure_factory as ff

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

    # Prepare data for the timeline plot
    df['Task'] = df['Original Category']
    df['Start'] = df['Start Datetime']
    df['Finish'] = df['End Datetime']
    df['Color'] = df['Color']

    # Create the timeline plot
    fig = ff.create_gantt(df, colors='Color', index_col='Task', show_colorbar=True, group_tasks=True)

    # Update layout
    fig.update_layout(title='Timeline of Events', xaxis_title='Time', yaxis_title='Category')

    # Show the plot
    st.plotly_chart(fig)
