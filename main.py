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

def create_bar_chart(df, start_date, end_date, start_time, end_time, selected_categories):
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
                     (df['End Datetime'].dt.time <= end_time)]

    # Create a list of data for plotting
    data = []
    for index, row in filtered_df.iterrows():
        category = row['Original Category']
        start_time = row['Start Datetime']
        end_time = row['End Datetime']
        duration = end_time - start_time
        data.append({
            'Category': category,
            'Start Datetime': start_time,
            'End Datetime': end_time,
            'Duration': duration
        })

    # Create a DataFrame from the list of data
    df_plot = pd.DataFrame(data)

    # Plot the graph using Plotly Express
    fig = px.timeline(df_plot, x_start="Start Datetime", x_end="End Datetime", y="Category",
                      color="Category", color_discrete_map=category_colors)
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_layout(title="Duration of Original Categories",
                      xaxis_title="Datetime",
                      yaxis_title="Original Category")
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
