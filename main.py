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

def create_bar_chart(df):
    # Create a list of colors corresponding to each category
    category_colors = {
        "Production Time": "green",
        "Unplanned Stoppages": "red",
        "Not Occupied": "grey",
        "Planned Stoppages": "yellow"
    }

    # Create a list of data for plotting
    data = []
    for index, row in df.iterrows():
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

        # Create bar chart
        create_bar_chart(df)

if __name__ == "__main__":
    main()
