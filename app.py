import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# 1. Page Configuration
st.set_page_config(page_title="Vidarbha CVI Dashboard", layout="wide")
st.title("🌍 Village-Level CVI - Vidarbha Dashboard")

# --- 2 TABS BANAVNE ---
tab1, tab2 = st.tabs(["🗺️ Main Dashboard", "🧮 CVI Calculator & Generator"])

# ==========================================
# TAB 2: DATA GENERATOR
# ==========================================
with tab2:
    st.header("⚙️ Raw Data to CVI Converter")
    st.write("Enter village information and raw scores (Exposure, Sensitivity, Adaptive Capacity) in the empty table. The app will automatically calculate the CVI on a 0–10 scale and generate a CSV file.")
    
    template_data = pd.DataFrame({
        "Village_Name": ["Navin Gaav"],
        "District": ["Nagpur"],
        "Exposure": [0.5],
        "Sensitivity": [0.5],
        "Adaptive_Capacity": [0.5],
        "lat": [21.14],
        "lon": [79.08]
    })
    
    st.write("✏️ ** Click on the table to edit the data or add new rows:**")
    edited_df = st.data_editor(template_data, num_rows="dynamic", use_container_width=True)
    
    if st.button("🚀 Calculate CVI & Generate CSV"):
        calc_score = ((edited_df['Exposure'] + edited_df['Sensitivity']) - edited_df['Adaptive_Capacity']) * 5
        edited_df.insert(5, 'CVI_Score', calc_score)
        edited_df['CVI_Score'] = edited_df['CVI_Score'].clip(0, 10).round(1)
        
        st.success("✅ CVI Calculated Successfully! Khalchi file download kara ani Main Dashboard madhe upload kara.")
        st.dataframe(edited_df, use_container_width=True)
        
        csv_data = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Ready CSV File",
            data=csv_data,
            file_name="custom_generated_cvi.csv",
            mime="text/csv"
        )

# ==========================================
# TAB 1: MAIN DASHBOARD
# ==========================================
with tab1:
    try:
        st.sidebar.header("📂 Data Center")
        uploaded_file = st.sidebar.file_uploader("Upload a New CSV File:", type=['csv'])

        # Backend chi garaj nahi, direct CSV file kiva Uploaded file read kara
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
        else:
            # Local CSV file read kara (Backend bypass)
            if os.path.exists('cvi_data.csv'):
                df = pd.read_csv('cvi_data.csv')
            else:
                df = pd.DataFrame() # Khali dataframe jar file nasel tar
                st.warning("⚠️ 'cvi_data.csv' file not found. please upload a file from left side.")

        if not df.empty:
            st.sidebar.divider()
            st.sidebar.header("🔍 Data Filters")
            districts = df['District'].unique().tolist()
            districts.insert(0, "All Vidarbha") 
            selected_district = st.sidebar.selectbox("Select District:", districts)

            if selected_district != "All Vidarbha":
                df = df[df['District'] == selected_district]

            st.subheader(f"📊 Analytics: {selected_district}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(label="Total Villages", value=len(df))
            with col2:
                highest_cvi = df['CVI_Score'].max()
                danger_village = df[df['CVI_Score'] == highest_cvi]['Village_Name'].iloc[0]
                st.metric(label="Most Vulnerable Village", value=danger_village, delta=f"Score: {highest_cvi}", delta_color="inverse")
            with col3:
                avg_cvi = round(df['CVI_Score'].mean(), 2)
                st.metric(label="Average CVI Score", value=avg_cvi)

            st.divider() 
            col_table, col_chart = st.columns(2)
            with col_table:
                st.write("📋 Filtered Data Table:")
                st.dataframe(df, use_container_width=True)
            with col_chart:
                st.write("📈 CVI Score Graph:")
                chart_data = df.set_index('Village_Name')['CVI_Score']
                st.bar_chart(chart_data)

            st.divider()
            st.write("🗺️ Vidarbha Vulnerability Map (Folium Advanced):")
            st.markdown("**Map Legend:** 🟢 **Low** (0-2.5) | 🟡 **Medium** (2.6-5.0) | 🟠 **High** (5.1-7.5, Blinking) | 🔴 **Very High** (7.6-10, Fast Blinking)")

            if 'lat' in df.columns and 'lon' in df.columns:
                avg_lat = df['lat'].mean()
                avg_lon = df['lon'].mean()
                m = folium.Map(location=[avg_lat, avg_lon], zoom_start=7)

                blink_css = """
                <style>
                @keyframes blinker-fast { 50% { opacity: 0.1; transform: scale(1.5); } }
                @keyframes blinker-slow { 50% { opacity: 0.3; transform: scale(1.3); } }
                .dot { border-radius: 50%; border: 1px solid black; box-shadow: 0 0 5px rgba(0,0,0,0.5); }
                .red-blink { background-color: #FF0000; width: 18px; height: 18px; animation: blinker-fast 0.8s linear infinite; }
                .orange-blink { background-color: #FFA500; width: 15px; height: 15px; animation: blinker-slow 1.5s linear infinite; }
                .yellow-solid { background-color: #FFFF00; width: 12px; height: 12px; }
                .green-solid { background-color: #00FF00; width: 10px; height: 10px; }
                </style>
                """
                m.get_root().html.add_child(folium.Element(blink_css))

                for idx, row in df.iterrows():
                    score = row['CVI_Score']
                    if score <= 2.5: div_class = 'dot green-solid'
                    elif score <= 5.0: div_class = 'dot yellow-solid'
                    elif score <= 7.5: div_class = 'dot orange-blink'
                    else: div_class = 'dot red-blink'
                    
                    html_icon = f'<div class="{div_class}"></div>'
                    icon = folium.DivIcon(html=html_icon)
                    popup_info = f"<b>{row['Village_Name']}</b><br>Score: {score}<br>Dist: {row['District']}"
                    
                    folium.Marker(location=[row['lat'], row['lon']], icon=icon, tooltip=popup_info).add_to(m)

                st_folium(m, width=1000, height=500)
            else:
                st.warning("⚠️ Map dakhvnyasathi CSV madhe 'lat' ani 'lon' columns available nahit.")

    except Exception as e:
        st.error("Kahi tari chukla! Error: " + str(e))