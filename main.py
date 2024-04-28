import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import plotly.graph_objs as go
import plotly.figure_factory as ff
from datetime import datetime, date, time

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

    # Combine start datetime with start time and end datetime with end time
    combined_start_datetime = datetime.combine(start_date, start_time)
    combined_end_datetime = datetime.combine(end_date, end_time)
    st.write(combined_start_datetime)
    st.write(combined_end_datetime)

    # Filter data based on selected categories and date range
    filtered_df = df[(df['Original Category'].isin(selected_categories)) &
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
    fig.update_layout(title=f"🕔 Duration of {y_axis}",
                      xaxis_title="Datetime",
                      yaxis_title=y_axis,
                      width=1200,
                      height=400)
    st.plotly_chart(fig)


def create_pareto(df, category_column, value_column,duration_type):
    # Group data by category and sum the duration
    df_grouped = df.groupby(category_column)[value_column].sum().reset_index()

    # Sort categories based on the sum of duration
    df_sorted = df_grouped.sort_values(by=value_column, ascending=False)
    st.write(df.groupby(category_column)[value_column])

    # Calculate cumulative percentage
    df_sorted["cumulative_percentage"] = (df_sorted[value_column].cumsum() / df_sorted[value_column].sum()) * 100

    # Plot Pareto diagram
    fig = go.Figure()

    # Add bars for frequencies with text outside the bars
    fig.add_trace(go.Bar(
        x=df_sorted[category_column],
        y=df_sorted[value_column],
        name='Hours',
        text=df_sorted[value_column].round(2),  # Round the values to two decimal places
        textposition='outside'  # Display text outside the bars
    ))
    
    # Add the cumulative percentage line
    fig.add_trace(go.Scatter(
        x=df_sorted[category_column],
        y=df_sorted['cumulative_percentage'],
        name='Cumulative Percentage',
        line=dict(color="orange"),
        yaxis='y2'  # Secondary y-axis
    ))
    
    # Update the layout
    fig.update_layout(
        title=f"✅ {category_column} Pareto Diagram",
        yaxis=dict(
            title=duration_type
        ),
        yaxis2=dict(
            title='Cumulative Percentage (%)',
            overlaying='y',
            side='right'
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    st.plotly_chart(fig)

def create_waterfall(df, category_column1, category_column2, value_column, duration_type):
    # Group data by category and sum the duration
    df_grouped1 = df.groupby(category_column1)[value_column].sum().reset_index()
    # Sort categories based on the sum of duration
    df_sorted1 = df_grouped1.sort_values(by=value_column, ascending=False)

    # Group data by category and sum the duration
    df_grouped2 = df.groupby(category_column2)[value_column].sum().reset_index()
    # Sort categories based on the sum of duration
    df_sorted2 = df_grouped2.sort_values(by=value_column, ascending=False)

    merged_df = pd.merge(df_sorted1, df_sorted2, left_on=category_column1, right_on=category_column2)
    merged_df.drop(columns=[category_column2], inplace=True)
    merged_df['Duration_Difference'] = merged_df['Duration_y'] - merged_df['Duration_x']
    merged_df.columns = ['Category', 'Original', 'Reclassified', 'Gap']

    #categories = list(['Ref']) + merged_df['Category'].tolist()
    #values = list([sum(merged_df['Reclassified'].tolist())]) + merged_df['Gap'].tolist()

    merged_df = merged_df.sort_values(by='Gap',ascending=False)
    categories = merged_df['Category'].tolist()
    values = merged_df['Gap'].tolist()
    values = [round(num, 2) for num in values]
    
    fig = go.Figure(go.Waterfall(
        x=categories,
        y=values,
        measure=["relative" if val != 0 else "total" for val in values],  # Different measure for each bar
        base=-10,  # Set the base to 100
        increasing=dict(marker=dict(color="green")),  # Set color for increasing values
        decreasing=dict(marker=dict(color="red")),  # Set color for decreasing values
        connector=dict(line=dict(color="grey", width=2)),  # Customize connector line
        text=values,  # Custom text for each bar
        #text=[0] + [values[i] - values[i - 1] for i in range(1, len(values))],  # Custom text for each bar
        textposition="outside",  # Set text position outside the bars
        hoverinfo="y+text",  # Display y value and custom text on hover
    ))
    # Update layout
    fig.update_layout(
        title='📈 Gap Analysis with Waterfall Graph',
        yaxis=dict(title=duration_type),
        xaxis=dict(title='Category'),
        showlegend=True,
        height=600
    )
    col1, col2 = st.columns(2)
    with col1:
        st.write("▶ Total Duration (hrs) of Original Vs Reclassification per Performance Category")
        total_sum = merged_df.sum()
        total_row = pd.DataFrame({'Category': ['Total'], 'Original': [total_sum['Original']], 'Reclassified': [total_sum['Reclassified']], 'Gap': [total_sum['Gap']]})
        merged_df = pd.concat([merged_df, total_row])
        merged_df = merged_df.reset_index(drop=True)
        st.write(merged_df)
    with col2:
        st.plotly_chart(fig)
        
# Step 2: Create a Streamlit app
def main():
    st.title("📊 DMO-Performance Reclassification Validation Tools")

    # Upload file
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        df = load_data(uploaded_file)
        st.sidebar.title("🔍 Data Filter:")

        # Create a multi-select dropdown for category filter in the sidebar
        available_categories = df['Original Category'].unique()
        #selected_categories = st.sidebar.multiselect("Select categories", available_categories, default=available_categories)
        selected_categories = [category for category in available_categories if st.sidebar.checkbox(category, value=True)]

        # Create a multi-select dropdown for equipment filter in the sidebar
        available_equipment = df['Reclassified Equipment'].unique()
        #selected_equipment = st.sidebar.multiselect("Select equipment", available_equipment, default=available_equipment)
        st.sidebar.title("🛠 Choose Equipment(s):")
        selected_equipment = [category for category in available_equipment if st.sidebar.checkbox(category, value=True)]

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

        # Create bar chart with filter for Original Category
        create_timeline(df, start_date, end_date, start_time, end_time, selected_categories, selected_equipment, "Original Equipment")

        # Create bar chart with filter for Reclassified Category
        create_timeline(df, start_date, end_date, start_time, end_time, selected_categories, selected_equipment, "Reclassified Equipment")
        
        st.dataframe(df, height=150)
        
        filtered_df = df[(df['Original Category'].isin(selected_categories)) &
                         (df['Start Datetime'].dt.date >= start_date) &
                         (df['End Datetime'].dt.date <= end_date) &
                         (df['Start Datetime'].dt.time >= start_time) &
                         (df['End Datetime'].dt.time <= end_time) &
                         ((df['Original Equipment'].isin(selected_equipment)) &
                          (df['Reclassified Equipment'].isin(selected_equipment)))]

        if duration_type == 'Seconds':
            time_factor = 1
        elif duration_type == 'Hours':
            time_factor = (1/3600)
        elif duration_type == 'Days':
            time_factor = 1/(3600*24)
        filtered_df['Duration'] = time_factor*(filtered_df['End Datetime'] - filtered_df['Start Datetime']).dt.total_seconds()
        
        # Create Pareto diagram for Both Category
        col1, col2 = st.columns(2)
        with col1:
            create_pareto(filtered_df, "Original Category", "Duration", duration_type)

        with col2:
            create_pareto(filtered_df, "Reclassified Category", "Duration", duration_type)
        
        create_waterfall(filtered_df,"Original Category","Reclassified Category", "Duration", duration_type)
        
        st.sidebar.image("Nestle_Signature.png")
        st.sidebar.write("""<p style='font-size: 14px;'>This Web-App is designed to facilitate DOR member of PT Nestlé Indonesia - Panjang Factory in identifying DMO Performance Category reclassification and track compliance based on <b>St-21.908-03 - Manufacturing Resources Performance Measurement Definition and Calculations
<b></p>""", unsafe_allow_html=True)
        st.sidebar.write("""<p style='font-size: 13px;'>For any inquiries, error handling, or assistance, please feel free to reach us through Email: <br>
<a href="mailto:Ananda.Cahyo@id.nestle.com">Ananda.Cahyo@id.nestle.com <br></p>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
