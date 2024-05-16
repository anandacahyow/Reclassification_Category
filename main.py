import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import plotly.graph_objs as go
import plotly.figure_factory as ff
from datetime import datetime, date, time
from concurrent.futures import ThreadPoolExecutor

img = Image.open('Nestle_Logo.png')
st.set_page_config(page_title="DMO-P Validation Tool", page_icon=img, layout="wide")

# Step 1: Read the Excel file and preprocess the data
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path)
    df['Start Datetime'] = pd.to_datetime(df['Start Datetime'])
    df['End Datetime'] = pd.to_datetime(df['End Datetime'])
    return df

def format_duration(duration):
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    seconds = duration.seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def create_timeline(df, default_cat, start_date, end_date, start_time, end_time, selected_categories, selected_equipment, y_axis):
    category_colors = {
        "Production Time": "green",
        "Unplanned Stoppages": "red",
        "Not Occupied": "grey",
        "Planned Stoppages": "yellow"
    }
    
    combined_start_datetime = datetime.combine(start_date, start_time)
    combined_end_datetime = datetime.combine(end_date, end_time)
    
    filtered_df = df[(df[default_cat].isin(selected_categories)) &
                     (df['Start Datetime'] >= combined_start_datetime) &
                     (df['End Datetime'] <= combined_end_datetime) &
                     (df['Original Equipment'].isin(selected_equipment)) &
                     (df['Reclassified Equipment'].isin(selected_equipment))]
    
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

    df_plot = pd.DataFrame(data)

    colour = "Category" if y_axis == "Original Equipment" else 'Reclassified Category'
    sub_cat = "Original Sub Category" if y_axis == "Original Equipment" else 'Reclassified Sub Category'
    reason = 'Original Reason' if y_axis == "Original Equipment" else 'Reclassified Reason'
    
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

def create_pareto(df, category_column, value_column, duration_type, avail_cat):
    color_catalogue = {
        "Production Time": "green",
        "Unplanned Stoppages": "red",
        "Not Occupied": "grey",
        "Planned Stoppages": "yellow"
    }
    category_colors = {df[avail_cat].unique()[0]: color_catalogue.get(df[avail_cat].unique()[0])} if len(df[avail_cat].unique()) == 1 else color_catalogue
        
    df_grouped = df.groupby(category_column)[value_column].sum().reset_index()
    df_sorted = df_grouped.sort_values(by=value_column, ascending=False)
    df_sorted["cumulative_percentage"] = (df_sorted[value_column].cumsum() / df_sorted[value_column].sum()) * 100

    fig = go.Figure()
    marker_colors = list(category_colors.values()) if len(df[avail_cat].unique()) == 1 else [category_colors.get(category, "blue") for category in df_sorted[category_column]]
    fig.add_trace(go.Bar(
        x=df_sorted[category_column],
        y=df_sorted[value_column],
        name='Hours',
        text=df_sorted[value_column].round(2),
        textposition='outside',
        marker_color=marker_colors
    ))

    fig.add_trace(go.Scatter(
        x=df_sorted[category_column],
        y=df_sorted['cumulative_percentage'],
        name='Cumulative Percentage',
        line=dict(color="navy"),
        yaxis='y2'
    ))

    fig.update_layout(
        title=f"✅ {df[avail_cat].unique()[0] if len(df[avail_cat].unique()) == 1 else category_column} Pareto Diagram",
        height=500,
        yaxis=dict(title=duration_type),
        yaxis2=dict(title='Cumulative Percentage (%)', overlaying='y', side='right'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    st.plotly_chart(fig)

def create_waterfall(df, category_column1, category_column2, value_column, duration_type):
    pivot_df = df.pivot_table(index=category_column1, values=value_column, aggfunc='sum')
    predefined_categories = ['Not Occupied', 'Planned Stoppages', 'Production Time', 'Unplanned Stoppages']
    pivot_df = pivot_df.reindex(predefined_categories, fill_value=0)
    df_sorted1 = pivot_df.reset_index()

    pivot_df2 = df.pivot_table(index=category_column2, values=value_column, aggfunc='sum')
    pivot_df2 = pivot_df2.reindex(predefined_categories, fill_value=0)
    df_sorted2 = pivot_df2.reset_index()

    merged_df = pd.merge(df_sorted1, df_sorted2, left_on=category_column1, right_on=category_column2)
    merged_df.drop(columns=[category_column2], inplace=True)
    merged_df['Duration_Difference'] = merged_df['Duration_y'] - merged_df['Duration_x']
    merged_df.columns = ['Category', 'Original', 'Reclassified', 'Gap']
    merged_df = merged_df.sort_values(by='Gap', ascending=False)
    categories = merged_df['Category'].tolist()
    values = [round(num, 2) for num in merged_df['Gap'].tolist()]
    
    fig = go.Figure(go.Waterfall(
        x=categories,
        y=values,
        measure=["relative" if val != 1 else "total" for val in values],
        base=-10,
        increasing=dict(marker=dict(color="green")),
        decreasing=dict(marker=dict(color="red")),
        connector=dict(line=dict(color="grey", width=2)),
        text=values,
        textposition="outside",
        hoverinfo="y+text",
    ))

    fig.update_layout(
        title='📈 Gap Analysis with Waterfall Graph',
        yaxis=dict(title=duration_type),
        xaxis=dict(title='Category'),
        showlegend=True,
        height=500
    )

    col1, col2 = st.columns(2)
    with col1:
        st.write("▶ Total Duration (hrs) of Original Vs Reclassification per Performance Category")
        total_sum = merged_df.sum()
        total_row = pd.DataFrame({'Category': ['Total'], 'Original': [total_sum['Original']], 'Reclassified': [total_sum['Reclassified']], 'Gap': [total_sum['Gap']]})
        merged_df = pd.concat([merged_df, total_row]).reset_index(drop=True)
        st.write(merged_df)
    with col2:
        st.plotly_chart(fig)

def main():
    st.title("📊 DMO-Performance Reclassification Validation Tools")
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        df = load_data(uploaded_file)
        st.sidebar.title("🔍 Data Filter:")

        default_cat = st.sidebar.selectbox("Select Category", ["Original Category", "Reclassified Category"], index=1)
        available_categories = df['Original Category'].unique()
        selected_categories = [category for category in available_categories if st.sidebar.checkbox(category, value=True)]

        available_equipment = df['Original Equipment'].unique()
        selected_equipment = [equipment for equipment in available_equipment if st.sidebar.checkbox(equipment, value=True)]

        start_date = st.sidebar.date_input("Start date", df['Start Datetime'].min())
        end_date = st.sidebar.date_input("End date", df['End Datetime'].max())

        start_time = st.sidebar.time_input("Start time", time(0, 0))
        end_time = st.sidebar.time_input("End time", time(23, 59))

        y_axis = st.sidebar.radio("Select Graph Axis", ["Original Equipment", "Reclassified Equipment"])

        if st.sidebar.button("Generate Graphs"):
            with ThreadPoolExecutor() as executor:
                future_timeline = executor.submit(create_timeline, df, default_cat, start_date, end_date, start_time, end_time, selected_categories, selected_equipment, y_axis)
                future_pareto = executor.submit(create_pareto, df, 'Reclassified Reason', 'Duration', 'Hours', default_cat)
                future_waterfall = executor.submit(create_waterfall, df, 'Original Category', 'Reclassified Category', 'Duration', 'Hours')

                future_timeline.result()
                future_pareto.result()
                future_waterfall.result()

if __name__ == "__main__":
    main()
