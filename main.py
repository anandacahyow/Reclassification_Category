import streamlit as st
import pandas as pd
import plotly.express as px

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

def create_bar_chart(df, start_date, end_date, start_time, end_time, selected_categories):
    # Combine date and time inputs into timestamps for filtering
    start_datetime = pd.Timestamp(start_date.strftime('%Y-%m-%d')) + pd.Timedelta(hours=start_time.hour, minutes=start_time.minute, seconds=start_time.second)
    end_datetime = pd.Timestamp(end_date.strftime('%Y-%m-%d')) + pd.Timedelta(hours=end_time.hour, minutes=end_time.minute, seconds=end_time.second)
    
    # Filter data based on selected categories and date range
    filtered_df = df[(df['Original Category'].isin(selected_categories)) &
                     (df['Start Datetime'] >= start_datetime) &
                     (df['End Datetime'] <= end_datetime)]

    # Create a list of data for plotting
    data = []
    for index, row in filtered_df.iterrows():
        start_time = row['Start Datetime']
        end_time = row['End Datetime']
        duration = end_time - start_time
        formatted_duration = format_duration(duration)
        data.append({
            'Category': row['Original Category'],
            'Original Sub Category': row['Original Sub Category'],
            'Start Datetime': start_time,
            'End Datetime': end_time,
            'Duration': formatted_duration,
            'PLC Code': row['PLC Code']
        })

    # Create a DataFrame from the list of data
    df_plot = pd.DataFrame(data)

    # Plot the graph using Plotly Express
    fig = px.timeline(df_plot, x_start="Start Datetime", x_end="End Datetime", color="Category",
                      hover_data={"Category": True,
                                  "Original Sub Category": True,
                                  "Start Datetime": "|%Y-%m-%d %H:%M:%S",
                                  "End Datetime": "|%Y-%m-%d %H:%M:%S",
                                  "Duration": True,
                                  "PLC Code": True})
    fig.update_traces(marker=dict(line=dict(width=1)))
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_layout(title="Duration of Original Categories",
                      xaxis_title="Datetime")
    st.plotly_chart(fig)

# Step 2: Create a Streamlit app
def main():
    st.title("Streamlit App for Visualizing Original Categories Duration")

    # Upload file
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        df = load_data(uploaded_file)
        st.write("Sample of the data:")
        st.write(df.head())

        # Create a multi-select dropdown for category filter
        available_categories = df['Original Category'].unique()
        selected_categories = st.multiselect("Select categories", available_categories, default=available_categories)

        # Arrange date and time filters side by side
        col1, col2 = st.columns(2)
        with col1:
            # Create date range picker for filtering by date
            start_date = st.date_input("Start Date", min_value=df['Start Datetime'].min().date(),
                                       max_value=df['End Datetime'].max().date(),
                                       value=df['Start Datetime'].min().date())
            end_date = st.date_input("End Date", min_value=df['Start Datetime'].min().date(),
                                     max_value=df['End Datetime'].max().date(),
                                     value=df['End Datetime'].max().date())

        with col2:
            # Create time sliders for filtering by time
            start_time = st.slider("Start Time", value=pd.Timestamp("00:00").time(), format="HH:mm:ss")
            end_time = st.slider("End Time", value=pd.Timestamp("23:59:59").time(), format="HH:mm:ss")

        # Create bar chart with filter
        create_bar_chart(df, start_date, end_date, start_time, end_time, selected_categories)

if __name__ == "__main__":
    main()
