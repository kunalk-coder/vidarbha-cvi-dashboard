import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import os

# 1. Page Configuration
st.set_page_config(page_title="Vidarbha CVI Enterprise", layout="wide")
st.title("🌍 Village-Level CVI - Vidarbha Enterprise Dashboard")

# --- GLOBAL DATA CENTER ---
st.sidebar.header("📂 Data Center")
uploaded_file = st.sidebar.file_uploader("Upload Custom CSV:", type=['csv'])

if uploaded_file is not None:
    df_global = pd.read_csv(uploaded_file)
elif os.path.exists('cvi_data.csv'):
    df_global = pd.read_csv('cvi_data.csv')
else:
    df_global = pd.DataFrame()

def get_risk_category(score):
    if score <= 2.5: return 'Low Risk'
    elif score <= 5.0: return 'Medium Risk'
    elif score <= 7.5: return 'High Risk'
    else: return 'Very High Risk'

if not df_global.empty and 'CVI_Score' in df_global.columns:
    df_global['Risk_Category'] = df_global['CVI_Score'].apply(get_risk_category)

# --- 5 TABS ARCHITECTURE ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ Dashboard", 
    "🧮 CVI Generator", 
    "📈 Analytics", 
    "📑 Auto-Reports", 
    "📚 Methodology"
])

# ==========================================
# TAB 1: MAIN DASHBOARD (Map, Table & Filters)
# ==========================================
with tab1:
    st.header("Interactive Vulnerability Map & Data")
    
    if not df_global.empty:
        districts = ["All Vidarbha"] + df_global['District'].unique().tolist()
        selected_district = st.sidebar.selectbox("Filter District for Map:", districts)
        
        df_map = df_global[df_global['District'] == selected_district] if selected_district != "All Vidarbha" else df_global.copy()

        # KPI Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Villages (Map)", len(df_map))
        col2.metric("Highest Risk Score", df_map['CVI_Score'].max() if not df_map.empty else 0)
        col3.metric("Average CVI", round(df_map['CVI_Score'].mean(), 2) if not df_map.empty else 0)

        st.divider()
        
        # --- MISSING TABLE ADDED HERE ---
        st.subheader("📋 Filtered Data Table")
        st.dataframe(df_map, use_container_width=True)
        
        st.divider()
        
        # --- MISSING MAP LEGEND ADDED HERE ---
        st.write("🗺️ **Vidarbha Vulnerability Map (Folium Advanced):**")
        st.markdown("**Map Legend:** 🟢 **Low Risk** (0-2.5) | 🟡 **Medium Risk** (2.6-5.0) | 🟠 **High Risk** (5.1-7.5, Blinking) | 🔴 **Very High Risk** (7.6-10, Fast Blinking)")

        if 'lat' in df_map.columns and 'lon' in df_map.columns:
            m = folium.Map(location=[df_map['lat'].mean(), df_map['lon'].mean()], zoom_start=7)
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

            for _, row in df_map.iterrows():
                score = row['CVI_Score']
                if score <= 2.5: div_class = 'dot green-solid'
                elif score <= 5.0: div_class = 'dot yellow-solid'
                elif score <= 7.5: div_class = 'dot orange-blink'
                else: div_class = 'dot red-blink'
                
                icon = folium.DivIcon(html=f'<div class="{div_class}"></div>')
                folium.Marker([row['lat'], row['lon']], icon=icon, tooltip=f"<b>{row['Village_Name']}</b><br>Score: {score}").add_to(m)

            st_folium(m, width=1000, height=500)
    else:
        st.warning("Please upload a CSV file from the sidebar.")

# ==========================================
# TAB 2: CVI CALCULATOR & GENERATOR
# ==========================================
with tab2:
    st.header("⚙️ Data Creation Engine (SaaS)")
    st.write("Input raw metrics to dynamically generate standardized CVI data.")
    template_data = pd.DataFrame({"Village_Name": ["New_Village"], "District": ["Nagpur"], "Exposure": [0.5], "Sensitivity": [0.5], "Adaptive_Capacity": [0.5], "lat": [21.14], "lon": [79.08]})
    
    edited_df = st.data_editor(template_data, num_rows="dynamic", use_container_width=True)
    if st.button("🚀 Calculate & Generate CSV"):
        edited_df.insert(5, 'CVI_Score', (((edited_df['Exposure'] + edited_df['Sensitivity']) - edited_df['Adaptive_Capacity']) * 5).clip(0, 10).round(1))
        st.success("✅ Data Generated! Please download and upload it from the sidebar to view in Analytics.")
        st.dataframe(edited_df)
        st.download_button("📥 Download Database", edited_df.to_csv(index=False).encode('utf-8'), "new_cvi_data.csv", "text/csv")

# ==========================================
# TAB 3: ADVANCED ANALYTICS (Plotly)
# ==========================================
with tab3:
    st.header("📈 Deep-Dive Analytics")
    if not df_global.empty and 'Risk_Category' in df_global.columns:
        colA, colB = st.columns(2)
        with colA:
            st.subheader("Overall Risk Distribution")
            fig_pie = px.pie(df_global, names='Risk_Category', hole=0.4, 
                             color='Risk_Category',
                             color_discrete_map={'Low Risk':'#00FF00', 'Medium Risk':'#FFFF00', 'High Risk':'#FFA500', 'Very High Risk':'#FF0000'})
            st.plotly_chart(fig_pie, use_container_width=True)
        with colB:
            st.subheader("Top Vulnerable Villages")
            top_danger = df_global.sort_values(by='CVI_Score', ascending=False).head(10)
            fig_bar = px.bar(top_danger, x='Village_Name', y='CVI_Score', color='CVI_Score', color_continuous_scale='Reds')
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No calculated data available. Please upload a valid CSV.")

# ==========================================
# TAB 4: AUTOMATED REPORTS
# ==========================================
with tab4:
    st.header("📑 Executive Summary Generator")
    if not df_global.empty and 'District' in df_global.columns:
        report_dist = st.selectbox("Select District for Report:", df_global['District'].unique())
        rep_df = df_global[df_global['District'] == report_dist]
        
        st.markdown(f"### 📋 Official CVI Report: **{report_dist} District**")
        st.write(f"- **Total Villages Assessed:** {len(rep_df)}")
        st.write(f"- **District Average CVI:** {rep_df['CVI_Score'].mean():.2f} / 10")
        
        if 'Risk_Category' in rep_df.columns:
            high_risk_count = len(rep_df[rep_df['CVI_Score'] > 5.0])
            st.write(f"- **Villages in High/Very High Risk:** {high_risk_count} out of {len(rep_df)}")
            
            if high_risk_count > 0:
                st.error(f"⚠️ **Action Required:** {high_risk_count} villages need immediate climate intervention funding and resource allocation.")
            else:
                st.success("✅ **Status Safe:** All monitored villages are currently within manageable risk thresholds.")
            
            st.dataframe(rep_df[['Village_Name', 'CVI_Score', 'Risk_Category']].sort_values(by='CVI_Score', ascending=False), use_container_width=True)
    else:
        st.info("Please upload data to generate reports.")

# ==========================================
# TAB 5: METHODOLOGY
# ==========================================
with tab5:
    st.header("📚 Technical Documentation")
    st.markdown("""
    ### 1. The Mathematical Model
    The Climate Vulnerability Index (CVI) is calculated using a standard normalized formula:
    **`CVI = ((Exposure + Sensitivity) - Adaptive Capacity) * 5`**
    
    * **Exposure:** Frequency of climate events (Droughts, Floods).
    * **Sensitivity:** Degree to which the village is affected (Agriculture dependency).
    * **Adaptive Capacity:** Availability of resources to cope (Hospitals, Funds).
    
    ### 2. Risk Legend (0-10 Scale)
    * 🟢 **0.0 - 2.5:** Low Risk (Optimal conditions)
    * 🟡 **2.6 - 5.0:** Medium Risk (Monitoring required)
    * 🟠 **5.1 - 7.5:** High Risk (Action plan needed - *Slow Blinking Marker*)
    * 🔴 **7.6 - 10.0:** Very High Risk (Emergency protocols - *Fast Blinking Marker*)
    
    * | Full-Stack Geospatial Project*
    """)