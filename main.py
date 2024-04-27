import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import plotly.graph_objs as go

img = Image.open('Nestle_Logo.png')
st.set_page_config(page_title="DMO-P Reclassification Checking Tool", page_icon=img,layout="wide")

# Step 1: Read the Excel file and preprocess the data
@st.cache
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

def create_timeline(df, start_date, end_date, start_time, end_time, selected_categories, selected_equipment, y_axis):
    # Create a list of colors corresponding to each category
    category_colors = {
        "Production Time": "green",
        "Unplanned Stoppages": "red",
        "Not Occupied": "grey",
        "Planned Stoppages": "yellow"
    }

    # Filter data based on selected categories and date range
    filtered_df = df[(df['Original Category'].isin(selected_categories)) &
                     (df['Start Datetime'].dt.date >= start_date) &
                     (df['End Datetime'].dt.date <= end_date) &
                     (df['Start Datetime'].dt.time >= start_time) &
                     (df['End Datetime'].dt.time <= end_time) &
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
            'PLC Code': row['PLC Code']
        })

    # Create a DataFrame from the list of data
    df_plot = pd.DataFrame(data)

    if y_axis == "Original Equipment":
        colour = "Category"
        sub_cat = "Original Sub Category"
    else:
        colour = 'Reclassified Category'
        sub_cat = 'Reclassified Sub Category'
    # Plot the graph using Plotly Express
    fig = px.timeline(df_plot, x_start="Start Datetime", x_end="End Datetime", y=y_axis,
                      color=colour, color_discrete_map=category_colors,
                      hover_data={sub_cat: True,
                                  "Start Datetime": "|%Y-%m-%d %H:%M:%S",
                                  "End Datetime": "|%Y-%m-%d %H:%M:%S",
                                  "Duration": True,
                                  "PLC Code": True})
    fig.update_yaxes(categoryorder="category ascending")
    fig.update_layout(title=f"Duration of {y_axis}",
                      xaxis_title="Datetime",
                      yaxis_title=y_axis,
                      width = 1200,
                      height = 400)
    st.plotly_chart(fig)

def create_pareto(df, category_column, value_column):
    # Group data by category and sum the duration
    df_grouped = df.groupby(category_column)[value_column].sum().reset_index()

    # Sort categories based on the sum of duration
    df_sorted = df_grouped.sort_values(by=value_column, ascending=False)

    # Calculate cumulative percentage
    df_sorted["cumulative_percentage"] = (df_sorted[value_column].cumsum() / df_sorted[value_column].sum()) * 100

    # Plot Pareto diagram
    #fig = px.bar(df_sorted, x=category_column, y=value_column, title=f"Pareto Diagram - {category_column}",labels={category_column: "Categories", value_column: "Duration (s)"})
    #fig.add_scatter(x=df_sorted[category_column], y=df_sorted["cumulative_percentage"], mode="lines", line=dict(color="red"),name="Cumulative Percentage")
    
    fig = go.Figure()
    # Add bars for frequencies
    fig.add_trace(go.Bar(
        x=df_sorted[category_column],
        y=df_sorted[value_column],
        name='Frequency'
    ))
    
    st.plotly_chart(fig)

# Step 2: Create a Streamlit app
def main():
    st.title("📊 DMO Performance Reclassification Checking Tools")

    # Upload file
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        df = load_data(uploaded_file)
        st.sidebar.title("🔍 Data Filter:")

        # Create a multi-select dropdown for category filter in the sidebar
        available_categories = df['Original Category'].unique()
        selected_categories = st.sidebar.multiselect("Select categories", available_categories, default=available_categories)

        # Create a multi-select dropdown for equipment filter in the sidebar
        available_equipment = df['Reclassified Equipment'].unique()
        selected_equipment = st.sidebar.multiselect("Select equipment", available_equipment, default=available_equipment)

        # Create date range picker for filtering by date in the sidebar
        start_date = st.sidebar.date_input("Start Date", min_value=df['Start Datetime'].min().date(),
                                       max_value=df['End Datetime'].max().date(),
                                       value=df['Start Datetime'].min().date())
        end_date = st.sidebar.date_input("End Date", min_value=df['Start Datetime'].min().date(),
                                     max_value=df['End Datetime'].max().date(),
                                     value=df['End Datetime'].max().date())

        # Create time sliders for filtering by time in the sidebar
        start_time = st.sidebar.slider("Start Time", value=pd.Timestamp("00:00").time(), format="HH:mm:ss")
        end_time = st.sidebar.slider("End Time", value=pd.Timestamp("23:59:59").time(), format="HH:mm:ss")

        # Create bar chart with filter for Original Category
        create_timeline(df, start_date, end_date, start_time, end_time, selected_categories, selected_equipment, "Original Equipment")

        # Create bar chart with filter for Reclassified Category
        create_timeline(df, start_date, end_date, start_time, end_time, selected_categories, selected_equipment, "Reclassified Equipment")

        st.write(df)
        filtered_df = df[(df['Original Category'].isin(selected_categories)) &
                         (df['Start Datetime'].dt.date >= start_date) &
                         (df['End Datetime'].dt.date <= end_date) &
                         (df['Start Datetime'].dt.time >= start_time) &
                         (df['End Datetime'].dt.time <= end_time) &
                         ((df['Original Equipment'].isin(selected_equipment)) &
                          (df['Reclassified Equipment'].isin(selected_equipment)))]
        filtered_df['Duration'] = (filtered_df['End Datetime'] - filtered_df['Start Datetime']).dt.total_seconds()
        
        # Create Pareto diagram for Both Category
        create_pareto(filtered_df, "Original Category", "Duration")
        create_pareto(filtered_df, "Reclassified Category", "Duration")
        
        st.sidebar.image("Nestle_Signature.png")
        st.sidebar.write("""<p style='font-size: 14px;'>This Web-App is designed to facilitate DOR member of PT Nestlé Indonesia - Panjang Factory identifying DMO Performance Category reclassification and track complaiance based on <b>St-21.908-03 - Manufacturing Resources Performance Measurement Definition and Calculations
<b></p>""", unsafe_allow_html=True)
        st.sidebar.write("""<p style='font-size: 13px;'>For any inquiries, error handling, or assistance, please feel free to reach us through Email: <br>
<a href="mailto:Ananda.Cahyo@id.nestle.com">Ananda.Cahyo@id.nestle.com <br></p>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
