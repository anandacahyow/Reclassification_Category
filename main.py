import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Read the Excel file
df = pd.read_excel("your_file.xlsx")

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

# Create the graph
fig, ax = plt.subplots()
for i, row in df.iterrows():
    ax.barh(i, width=(row['End Datetime'] - row['Start Datetime']), left=row['Start Datetime'], color=row['Color'])

# Format x-axis as datetime
ax.xaxis_date()

# Set x-axis label
ax.set_xlabel('Datetime')

# Set y-axis label
ax.set_ylabel('Original Category')

# Set y-ticks and labels
ax.set_yticks(df.index)
ax.set_yticklabels(df['Original Category'])

# Set the title
ax.set_title('Duration of Original Categories')

# Rotate x-axis labels for better readability
plt.xticks(rotation=45)

# Remove gridlines
plt.grid(False)

# Show the plot
st.pyplot(fig)
