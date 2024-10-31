import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re

# Load data and clean column names
data = pd.read_excel('C:\\Users\\GeorgiaLaurie\\INTTIN\\Technology - General\\Technologies\\Tin in Sodium Ion Batteries\\Outputs\\Scopus search break down.xlsx', sheet_name='Masterdoc')
data.columns = data.columns.str.strip()  # Strip any extra spaces from column names

# Ensure Title column has no NaN values by replacing them with a placeholder
data['Title'] = data['Title'].fillna("").str.strip()

# Filter out rows where 'Title' is empty, just whitespace, or 'Unknown'
data = data[(data['Title'] != "") & (data['Title'] != "Unknown")]

# Parsing function to extract specific capacities and current densities from "Specific Capacity" column
def parse_specific_capacity(text):
    if pd.isna(text):
        return []
    
    # Normalize spaces and replace non-standard characters with standard equivalents
    text = re.sub(r'[\u2009\u202F\u00A0]', ' ', str(text))  
    text = re.sub(r'[–−]', '-', text)  

    # Extended regex to capture multiple formats
    matches = re.findall(
        r'(\d+(?:\.\d+)?)\s*mAh\s*g-1\s*(?:at\s*|,|and)?\s*(\d+(?:\.\d+)?\s*(?:A|mA)\s*g-1)', 
        text
    )

    return [(float(capacity), float(density.split()[0])) for capacity, density in matches]

# Parsing function for cycle life data specifically for the bubble chart
def parse_cycle_life_data(text):
    if pd.isna(text):
        return []
    
    # Normalize spaces and replace non-standard characters with standard equivalents
    text = re.sub(r'[\u2009\u202F\u00A0]', ' ', str(text))
    text = re.sub(r'[–−]', '-', text)  

    # Regex to capture specific capacity, current density, and cycle number in Cycle Life
    matches = re.findall(
        r'(\d+(?:\.\d+)?)\s*mAh\s*g-1\s*at\s*(\d+(?:\.\d+)?)\s*(?:A|mA)\s*g-1.*?(\d+)\s*cycles', 
        text
    )

    return [(float(capacity), float(density), int(cycles)) for capacity, density, cycles in matches]

# Apply parsing functions to extract specific capacity and current density values
data['Capacity_Data'] = data['Specific Capacity'].apply(parse_specific_capacity)
data['Cycle_Life_Capacity_Data'] = data['Cycle Life'].apply(parse_cycle_life_data)

# Create unique list of anode titles for dropdown
anode_titles = sorted(data['Title'].dropna().unique())

# Streamlit app layout
st.title("Performance Analysis of Tin-Based Anode Materials")

# Sidebar for selecting anode type
selected_anode = st.sidebar.selectbox("Select Anode Type", ["All"] + anode_titles)

# Display All Table or Specific Anode Data
if selected_anode == "All":
    # Prepare data for 'All' table view
    all_data = data[['Title', 'Capacity_Data', 'Cycle_Life_Capacity_Data', 'DOI']].copy()
    
    # Separate Capacity Data into two columns
    all_data['Specific Capacity (mAh g-1)'] = all_data['Capacity_Data'].apply(
        lambda x: ', '.join(str(capacity) for capacity, _ in x) if x else "N/A"
    )
    all_data['Current Density (A g-1)'] = all_data['Capacity_Data'].apply(
        lambda x: ', '.join(str(density) for _, density in x) if x else "N/A"
    )
    
    # Separate Cycle Life Capacity Data into three columns
    all_data['Cycle Specific Capacity (mAh g-1)'] = all_data['Cycle_Life_Capacity_Data'].apply(
        lambda x: ', '.join(str(capacity) for capacity, _, _ in x) if x else "N/A"
    )
    all_data['Cycle Current Density (A g-1)'] = all_data['Cycle_Life_Capacity_Data'].apply(
        lambda x: ', '.join(str(density) for _, density, _ in x) if x else "N/A"
    )
    all_data['No. of Cycles'] = all_data['Cycle_Life_Capacity_Data'].apply(
        lambda x: ', '.join(str(cycles) for _, _, cycles in x) if x else "N/A"
    )

    # Display as table
    st.subheader("All Anode Materials Performance Data")
    st.write(all_data[['Title', 'Specific Capacity (mAh g-1)', 'Current Density (A g-1)', 
                       'Cycle Specific Capacity (mAh g-1)', 'Cycle Current Density (A g-1)', 
                       'No. of Cycles', 'DOI']])

    # Aggregate and plot all data for specific capacity vs. current density
    st.write("### Aggregate Specific Capacity vs. Current Density")
    fig, ax = plt.subplots()
    max_density = 0  # Track maximum current density for setting x-axis range
    for title in anode_titles:
        subset = data[data['Title'] == title]
        for capacity_data in subset['Capacity_Data']:
            if capacity_data:
                capacities, densities = zip(*capacity_data)
                max_density = max(max_density, max(densities))
                ax.plot(densities, capacities, 'o-', label=title)

    ax.set_xlim(0, max_density * 1.1)  # Extend x-axis slightly beyond max density
    ax.set_xlabel("Current Density (A g-1)")
    ax.set_ylabel("Specific Capacity (mAh g-1)")
    ax.set_title("Specific Capacity vs. Current Density (All Materials)")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1), ncol=2)  # Legend with multiple columns
    st.pyplot(fig)

    # Bubble chart for cycle life data in Cycle Life column, only including rows with cycle life data
    st.write("### Aggregate Cycle Life Performance Data (Bubble Chart)")
    fig2, ax2 = plt.subplots()
    for _, row in all_data.iterrows():
        title = row['Title']
        cycle_data = row['Cycle_Life_Capacity_Data']
        if cycle_data:  # Include only rows with cycle life data
            capacities, densities, cycle_numbers = zip(*cycle_data)
            max_density = max(max_density, max(densities))
            bubble_sizes = [cycle / 10 for cycle in cycle_numbers]  # Bubble size based on cycle count
            scatter = ax2.scatter(densities, capacities, s=bubble_sizes, alpha=0.6, label=title, edgecolors='w', linewidth=0.5)

    ax2.set_xlim(0, max_density * 1.1)  # Extend x-axis slightly beyond max density
    ax2.set_xlabel("Current Density (A g-1)")
    ax2.set_ylabel("Specific Capacity (mAh g-1)")
    ax2.set_title("Specific Capacity vs. Current Density (Bubble Size = Cycle Number)")
    ax2.legend(loc="upper left", bbox_to_anchor=(1, 1), ncol=2)  # Legend with multiple columns
    st.pyplot(fig2)

else:
    # Filter data for selected anode material
    anode_data = data[data['Title'] == selected_anode].iloc[0]
    st.subheader(f"Performance Analysis for {selected_anode}")
    st.markdown(f"**DOI:** [{anode_data['DOI']}]({anode_data['DOI']})")

    # Display Specific Capacity vs. Current Density for selected anode
    capacity_data = anode_data['Capacity_Data']
    if capacity_data:
        capacities, densities = zip(*capacity_data)
        st.write("### Specific Capacity vs. Current Density")
        fig, ax = plt.subplots()
        ax.plot(densities, capacities, 'o-', label="Specific Capacity")
        ax.set_xlim(0, max(densities) * 1.1)  # Ensure x-axis starts from 0
        ax.set_xlabel("Current Density (A g-1)")
        ax.set_ylabel("Specific Capacity (mAh g-1)")
        ax.set_title(f"Specific Capacity at Various Current Densities for {selected_anode}")
        ax.legend(loc="upper left", bbox_to_anchor=(1, 1), ncol=2)  # Legend with multiple columns
        st.pyplot(fig)
    else:
        st.write("No specific capacity data available for this anode material.")

    # Display Cycle Life Data if available
    st.write("### Cycle Life Data")
    cycle_life_data = anode_data['Cycle_Life_Capacity_Data']
    if cycle_life_data:
        st.write("Cycle-specific Capacity and Current Density data:")
        for (capacity, density, cycles) in cycle_life_data:
            st.write(f"{cycles} cycles at {density} A g-1: {capacity} mAh g-1")
    else:
        st.write("No cycle life data available for this anode material.")