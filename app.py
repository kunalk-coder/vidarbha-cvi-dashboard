import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# 1. Page Configuration
st.set_page_config(page_title="Vidarbha CVI Dashboard", layout="wide")
st.title("🌍 Village-Level CVI - Vidarbha Dashboard")

try:
    # --- 1. DYNAMIC FILE UPLOADER ---
    st.sidebar.header("📂 Data Center")
    uploaded_file = st.sidebar.file_uploader("Upload New CSV File :", type=['csv'])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("✅ Custom Data Uploaded Successfully!")
    else:
        # Live website ke liye direct CSV file read karenge (No Flask backend needed)
        df = pd.read_csv('cvi_data.csv')

    # --- 2. SIDEBAR FILTER ---
    st.sidebar.divider()
    st.sidebar.header("🔍 Data Filters")
    districts = df['District'].unique().tolist()
    districts.insert(0, "All Vidarbha") 
    selected_district = st.sidebar.selectbox("Select District:", districts)

    if selected_district != "All Vidarbha":
        df = df[df['District'] == selected_district]

    # --- 3. KPI METRICS ---
    st.subheader(f"📊 Analytics: {selected_district}")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total Villages", value=len(df))
    with col2:
        if not df.empty:
            highest_cvi = df['CVI_Score'].max()
            danger_village = df[df['CVI_Score'] == highest_cvi]['Village_Name'].iloc[0]
            st.metric(label="Most Vulnerable Village", value=danger_village, delta=f"Score: {highest_cvi}", delta_color="inverse")
    with col3:
        if not df.empty:
            avg_cvi = round(df['CVI_Score'].mean(), 2)
            st.metric(label="Average CVI Score", value=avg_cvi)

    st.divider() 

    # --- 4. TABLE ANI GRAPH ---
    col_table, col_chart = st.columns(2)
    with col_table:
        st.write("📋 Filtered Data Table:")
        st.dataframe(df, use_container_width=True)
    with col_chart:
        st.write("📈 CVI Score Graph:")
        if not df.empty:
            chart_data = df.set_index('Village_Name')['CVI_Score']
            st.bar_chart(chart_data)

    # --- 5. ADVANCED BLINKING MAP (Kunal's Logic) ---
    st.divider()
    st.write("🗺️ Vidarbha Vulnerability Map (Folium Advanced):")

    st.markdown("""
    **Map Legend:** 🟢 **Low** (0-2.5) | 🟡 **Medium** (2.6-5.0) | 🟠 **High** (5.1-7.5, Blinking) | 🔴 **Very High** (7.6-10, Fast Blinking)
    """)

    if not df.empty and 'lat' in df.columns and 'lon' in df.columns:
        # Map center set karne (Vidarbha chya aaju baju)
        avg_lat = df['lat'].mean()
        avg_lon = df['lon'].mean()
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=7)

        # CSS Animation (Blinking Effect) map madhe inject karne
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

        # Gaav map var takne
        for idx, row in df.iterrows():
            score = row['CVI_Score']
            
            # Kunal cha Exact Logic (Colors and Blinking)
            if score <= 2.5: div_class = 'dot green-solid'
            elif score <= 5.0: div_class = 'dot yellow-solid'
            elif score <= 7.5: div_class = 'dot orange-blink'
            else: div_class = 'dot red-blink'
            
            # Dot banavne
            html_icon = f'<div class="{div_class}"></div>'
            icon = folium.DivIcon(html=html_icon)
            
            # Popup mahiti (Gaavache nav ani score)
            popup_info = f"<b>{row['Village_Name']}</b><br>Score: {score}<br>Dist: {row['District']}"
            
            folium.Marker(
                location=[row['lat'], row['lon']],
                icon=icon,
                tooltip=popup_info
            ).add_to(m)

        # Map dakhvne
        st_folium(m, width=1000, height=500)
    else:
        st.warning("⚠️ Map dakhvnyasathi CSV madhe 'lat' ani 'lon' columns available nahit.")

except Exception as e:
    st.error("Backend server sobat connect hot nahiye! Error: " + str(e))