import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, date, time

img = Image.open('Nestle_Logo.png')
st.set_page_config(page_title="DMO-P Validation Tool", page_icon=img, layout="wide")

# Step 1: Read the Excel file and preprocess the data
def load_data(file_path):
    df = pd.read_excel(file_path)
    # Convert 'Start Datetime' and 'End Datetime' columns to datetime
    df['Start Datetime'] = pd.to_datetime(df['Start Datetime'])
    df['End Datetime'] = pd.to_datetime(df['End Datetime'])
    return df

def format_duration(duration):
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    seconds = duration.seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def create_timeline(df, default_cat, start_date, end_date, start_time, end_time, selected_categories, selected_equipment, y_axis):
    # Create a list of colors corresponding to each category
    category_colors = {
        "Production Time": "green",
        "Unplanned Stoppages": "red",
        "Not Occupied": "grey",
        "Planned Stoppages": "yellow"
    }

    # Combine start datetime with start time and end datetime with end time
    combined_start_datetime = datetime.combine(start_date, start_time)
    combined_end_datetime = datetime.combine(end_date, end_time)

    # Filter data based on selected categories and date range
    filtered_df = df[(df[default_cat].isin(selected_categories)) &
                     (df['Start Datetime'] >= combined_start_datetime) &
                     (df['End Datetime'] <= combined_end_datetime) &
                     ((df['Original Equipment'].isin(selected_equipment)) &
                      (df['Reclassified Equipment'].isin(selected_equipment)))]

    # Create a list of data for plotting
    data = []
    for index, row in filtered_df.iterrows():
        category = row['Original Category']
        start_time = row['Start Datetime']
        end_time = row['End Datetime']
        duration = end_time - start_time
        formatted_duration = format_duration(duration)
        data.append({
            'Original Equipment': row['Original Equipment'],
            'Reclassified Equipment': row['Reclassified Equipment'],
            'Category': category,
            'Original Sub Category': row['Original Sub Category'],
            'Reclassified Category': row['Reclassified Category'],
            'Reclassified Sub Category': row['Reclassified Sub Category'],
            'Start Datetime': start_time,
            'End Datetime': end_time,
            'Duration': formatted_duration,
            'PLC Code': row['PLC Code'],
            'Reclassified Reason': row['Reclassified Reason'],
            'Original Reason': row['Original Reason'],
        })

    # Create a DataFrame from the list of data
    df_plot = pd.DataFrame(data)

    if y_axis == "Original Equipment":
        colour = "Category"
        sub_cat = "Original Sub Category"
        reason = "Original Reason"
    else:
        colour = 'Reclassified Category'
        sub_cat = 'Reclassified Sub Category'
        reason = 'Reclassified Reason'

    # Plot the graph using Plotly Express
    fig = px.timeline(df_plot, x_start="Start Datetime", x_end="End Datetime", y=y_axis,
                      color=colour, color_discrete_map=category_colors,
                      hover_data={sub_cat: True,
                                  "Start Datetime": "|%Y-%m-%d %H:%M:%S",
                                  "End Datetime": "|%Y-%m-%d %H:%M:%S",
                                  "Duration": True,
                                  "PLC Code": True,
                                  reason: True})
    fig.update_yaxes(categoryorder="category ascending")
    fig.update_layout(title=f"🕔 Duration of {y_axis}",
                      xaxis_title="Datetime",
                      yaxis_title=y_axis,
                      width=1200,
                      height=400)
    st.plotly_chart(fig)

def main():
    st.title("📊 DMO-Performance Reclassification Validation Tools")

    # Upload file
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        df = load_data(uploaded_file)
        st.sidebar.title("🔍 Data Filter:")

        # Create a multi-select dropdown for category filter in the sidebar
        default_cat = st.sidebar.selectbox("Select Category", ["Original Category", "Reclassified Category"], index=1)
        available_categories = df['Original Category'].unique()
        selected_categories = [category for category in available_categories if st.sidebar.checkbox(category, value=True)]

        # Create a multi-select dropdown for equipment filter in the sidebar
        available_equipment = df['Reclassified Equipment'].unique()
        st.sidebar.title("🛠 Choose Equipment(s):")
        all_machine_option = "All Machine"
        available_equipment_with_all = list(available_equipment)
        selected_equipment = st.sidebar.multiselect("Choose Equipment(s):", available_equipment_with_all, default=available_equipment_with_all)

        st.sidebar.title("⏳ Time Window :")
        # Create date range picker for filtering by date in the sidebar
        start_date = st.sidebar.date_input("Start Date", min_value=df['Start Datetime'].min().date(),
                                            max_value=df['End Datetime'].max().date(),
                                            value=df['Start Datetime'].min().date())
        start_time = st.sidebar.slider("Start Time", value=pd.Timestamp("06:00:00").time(), format="HH:mm:ss")

        end_date = st.sidebar.date_input("End Date", min_value=df['Start Datetime'].min().date(),
                                            max_value=df['End Datetime'].max().date(),
                                            value=df['End Datetime'].max().date())
        end_time = st.sidebar.slider("End Time", value=pd.Timestamp("06:00:00").time(), format="HH:mm:ss")

        duration_type = st.sidebar.selectbox("Select Duration units", ["Seconds", "Hours", "Days"], index=1)

        combined_start_datetime = datetime.combine(start_date, start_time)
        combined_end_datetime = datetime.combine(end_date, end_time)

        filtered_df = df[(df[default_cat].isin(selected_categories)) &
                            (df['Start Datetime'] >= combined_start_datetime) &
                            (df['End Datetime'] <= combined_end_datetime) &
                            ((df['Original Equipment'].isin(selected_equipment)) &
                            (df['Reclassified Equipment'].isin(selected_equipment)))]

        if duration_type == 'Seconds':
            time_factor = 1
        elif duration_type == 'Hours':
            time_factor = (1 / 3600)
        elif duration_type == 'Days':
            time_factor = 1 / (3600 * 24)
        filtered_df['Duration'] = time_factor * (filtered_df['End Datetime'] - filtered_df['Start Datetime']).dt.total_seconds()

        st.write("📅 DMO Event Listing")
        st.dataframe(filtered_df, height=150)

        # Plot the timeline
        create_timeline(df, default_cat, start_date, end_date, start_time, end_time, selected_categories, selected_equipment, "Original Equipment")
        create_timeline(df, default_cat, start_date, end_date, start_time, end_time, selected_categories, selected_equipment, "Reclassified Equipment")

        # Plot the Pareto chart
        st.write("📊 Pareto Chart")
        create_pareto_chart(df, 'Reclassified Category')

        # Plot the Waterfall chart
        st.write("📊 Waterfall Chart")
        create_waterfall_chart(df, 'Reclassified Category')

    st.sidebar.image("Nestle_Signature.png")
    st.sidebar.write("""<p style='font-size: 14px;'>This Web-App is designed to facilitate DOR member of PT Nestlé Indonesia - Panjang Factory in identifying DMO Performance Category reclassification and track compliance based on <b><a href="https://nestle.sharepoint.com/:b:/t/NMTTechnical2023/EZ2DQYyVfblDhGV11hbULU0BAPm34HHC5ZHCUERmFu3tnQ?e=IdQUp4" style="color:blue;">St-21.908-03 - Manufacturing Resources Performance Measurement Definition and Calculations</a></b></p>""", unsafe_allow_html=True)
    st.sidebar.write("""<p style='font-size: 13px;'>For any inquiries, error handling, or assistance, please feel free to reach us through Email: <br>
    <a href="mailto:Ananda.Cahyo@id.nestle.com">Ananda.Cahyo@id.nestle.com <br></p>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
