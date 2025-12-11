import streamlit as st
import requests
import json
import math
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta, timezone  # ← This imports the classes
import sys
import os

# Add api directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
from protocol_calculator import (
    calculate_phase_times,
    calculate_all_recommendations,
    evaluate_air_drying_suitability,
    calculate_air_dry_duration,
    get_heat_settings,
    get_power_map,
    fetch_room_conditions,
    fetch_electricity_price,
)

st.set_page_config(page_title="Hair Dryer Assistant", layout="wide")

# Load external CSS
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
if os.path.exists(css_path):
    with open(css_path) as css_file:
        st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

# Helper functions - MUST be defined before use
def calculate_recommendations(temp, humidity, hair_type, porosity, towel_level, time_priority):
    """Calculate recommendations based on conditions"""
    
    # Use shared protocol calculator for phase times
    result = calculate_phase_times(temp, humidity, hair_type, porosity, towel_level, time_priority)
    
    # Get heat settings for reference
    heat_settings = get_heat_settings()
    bulk_heat = heat_settings[result["heat_index"]]
    finish_heat = heat_settings[max(0, result["heat_index"] - 1)]
    
    # Warnings and tips
    warnings = []
    tips = []
    
    if result["heat_index"] == 2:
        warnings.append("⚠️ Using high heat setting. Keep the dryer moving continuously and maintain distance to prevent damage.")
    if result["dp"] < 0.6:
        tips.append("💡 High humidity detected. Emphasize airflow and movement. Expect longer drying time.")
    if result["dp"] > 1.2:
        tips.append("💡 Favorable drying conditions. You can use lower heat for gentler drying.")
    if hair_type == "fine" and result["heat_index"] >= 1:
        warnings.append("⚠️ Fine hair is more vulnerable to heat damage. Consider reducing heat if time allows.")
    if towel_level > 85:
        tips.append("💡 Hair is quite wet. Towel-dry more thoroughly to reduce heat exposure time.")
    if result["hybrid_drying_recommended"]:
        tips.append("🌿 Hybrid drying recommended! Start with natural air drying, then finish with gentle blow drying. This reduces heat damage while avoiding prolonged wetness.")
    
    # Merge warnings and tips into result
    result["warnings"] = warnings
    result["tips"] = tips
    
    return result



# Define heat settings and power map globally (used in results)
heat_settings = [
    {"name": "Low", "temp": "50-60°C", "distance": "18-20 cm"},
    {"name": "Medium", "temp": "70-80°C", "distance": "15-18 cm"},
    {"name": "High", "temp": "90-100°C", "distance": "18-20 cm"}
]
power_map = {"Low": 800, "Medium": 1200, "High": 1500}

# Title row with inline inputs
st.markdown('<div class="title-row">', unsafe_allow_html=True)

col_title, col_location, col_thickness, col_porosity, col_button = st.columns([1.2, 1.5, 1.2, 1.2, 1])

with col_title:
    st.markdown('<h1>Hair Dryer Assistant</h1>', unsafe_allow_html=True)

with col_location:
    st.markdown('<div class="input-group minimal-input">', unsafe_allow_html=True)
    location = st.text_input("Location", value="Barcelona", placeholder="City or Coords", label_visibility="visible", key="location_input")
    st.markdown('</div>', unsafe_allow_html=True)

with col_thickness:
    st.markdown('<div class="input-group minimal-input">', unsafe_allow_html=True)
    hair_type_opt = st.selectbox("Hair Thickness (feel an individual strand)", 
        ["Fine (hard to see and feel)", "Medium (visible but not coarse)", "Thick (strong and sturdy)"], 
        index=1, label_visibility="visible", key="thickness_input")
    hair_type = hair_type_opt.split(" ")[0].lower()
    st.markdown('</div>', unsafe_allow_html=True)

with col_porosity:
    st.markdown('<div class="input-group minimal-input">', unsafe_allow_html=True)
    porosity_opt = st.selectbox("Hair Porosity (drop strand in water 3–5 min)", 
        ["Low (floats, repels water, dries slow)", "Normal (sinks slowly)", "High (sinks fast, dries fast, may frizz)"], 
        index=1, label_visibility="visible", key="porosity_input")
    porosity = porosity_opt.split(" ")[0].lower()
    st.markdown('</div>', unsafe_allow_html=True)

with col_button:
    st.markdown('<div style="padding-top: 18px;">', unsafe_allow_html=True)
    generate_btn = st.button("Generate", key="generate_btn")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Processing
if generate_btn:
    try:
        # Fetch room conditions and electricity price using shared functions
        temp, humidity = fetch_room_conditions(location)
        elec_price = fetch_electricity_price(location)
    except:
        temp, humidity, elec_price = 20, 60, 0.26

    # Generate all recommendations using shared calculator
    recommendation_data = calculate_all_recommendations(
        temp=temp,
        humidity=humidity,
        hair_type=hair_type,
        porosity=porosity,
        elec_price=elec_price,
    )
    
    # Add warnings and tips to each result
    for result in recommendation_data["all_results"]:
        warnings = []
        tips = []
        
        if result["heat_index"] == 2:
            warnings.append("⚠️ Using high heat setting. Keep the dryer moving continuously and maintain distance to prevent damage.")
        if result["dp"] < 0.6:
            tips.append("💡 High humidity detected. Emphasize airflow and movement. Expect longer drying time.")
        if result["dp"] > 1.2:
            tips.append("💡 Favorable drying conditions. You can use lower heat for gentler drying.")
        if hair_type == "fine" and result["heat_index"] >= 1:
            warnings.append("⚠️ Fine hair is more vulnerable to heat damage. Consider reducing heat if time allows.")
        if result["towel_level"] > 85:
            tips.append("💡 Hair is quite wet. Towel-dry more thoroughly to reduce heat exposure time.")
        if result["hybrid_drying_recommended"]:
            tips.append("🌿 Hybrid drying recommended! Start with natural air drying, then finish with gentle blow drying. This reduces heat damage while avoiding prolonged wetness.")
        
        result["warnings"] = warnings
        result["tips"] = tips
    
    st.session_state.results = {
        "weather": {"temp": temp, "humidity": humidity},
        "location": location,
        "elec_price": elec_price,
        "all_results": recommendation_data["all_results"],
        "costs_data": recommendation_data["costs_data"],
        "lowest_cost_idx": recommendation_data["lowest_cost_idx"],
        "priorities": recommendation_data["priorities"],
        "towel_levels": recommendation_data["towel_levels"],
        "optimal_result": recommendation_data["optimal_result"],
    }

# Results Section
if "results" in st.session_state:
    results = st.session_state.results
    temp = results["weather"]["temp"]
    humidity = results["weather"]["humidity"]
    elec_price = results["elec_price"]

    # Use optimal (lowest cost) result
    num_priorities = len(results["priorities"])
    num_towels = len(results["towel_levels"])
    
    # Calculate indices from optimal result
    selected_towel_idx = results["towel_levels"].index(results["optimal_result"]["towel_level"])
    selected_priority_idx = results["priorities"].index(results["optimal_result"]["priority"])

    result_idx = selected_towel_idx * num_priorities + selected_priority_idx
    selected_result = results["all_results"][result_idx]

    # All four sections in one row
    st.markdown('<div class="section">', unsafe_allow_html=True)
    col_settings, col_environment, col_protocol, col_energy = st.columns([1, 1, 1, 1])

    # Column 1: Hair Settings Summary
    with col_settings:
        st.markdown('### ⚙️ Hair Settings')
        st.markdown(f"""
        <div class="result-item">
            <span class="result-label">Location</span>
            <span class="result-value">{results["location"]}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Hair Type</span>
            <span class="result-value">{hair_type.capitalize()}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Porosity</span>
            <span class="result-value">{porosity.capitalize()}</span>
        </div>
        """, unsafe_allow_html=True)

    # Column 2: Environment Conditions
    with col_environment:
        st.markdown('### 🌡️ Environment Conditions')
        st.markdown(f"""
        <div class="result-item">
            <span class="result-label">Temperature</span>
            <span class="result-value">{temp:.1f}°C</span>
        </div>
        <div class="result-item">
            <span class="result-label">Humidity</span>
            <span class="result-value">{humidity:.0f}%</span>
        </div>
        <div class="result-item">
            <span class="result-label">Drying Power Index</span>
            <span class="result-value">{selected_result['dp']:.2f}</span>
        </div>
        <div class="result-item">
            <span class="result-label">Environment Type</span>
            <span class="result-value">{selected_result['env_type']}</span>
        </div>
        """, unsafe_allow_html=True)

        if selected_result.get('tips'):
            st.markdown(f'<div class="info">{"<br>".join(selected_result["tips"])}</div>', unsafe_allow_html=True)

    # Column 3: Drying Protocol
    with col_protocol:
        st.markdown('### 📋 Drying Protocol')

        # Towel-dry phase
        towel_dry_duration = 1 if (100 - results["towel_levels"][selected_towel_idx]) <= 20 else 2 if (100 - results["towel_levels"][selected_towel_idx]) <= 35 else 3
        reduction = int((1 - (selected_result["bulk_time"] + selected_result["finish_time"]) / (selected_result["bulk_time"] + selected_result["finish_time"] + towel_dry_duration)) * 100) if (selected_result["bulk_time"] + selected_result["finish_time"] > 0) else 0

        # Towel-dry phase - always visible
        col_towel_label, col_towel_btn = st.columns([0.9, 0.1])
        with col_towel_label:
            st.markdown(f"""<div class="result-item phase-section">
                <span class="result-label">Towel-Dry Phase</span>
                <span class="result-value">~{towel_dry_duration} min</span>
            </div>""", unsafe_allow_html=True)
        with col_towel_btn:
            if st.button("ⓘ", key="towel_dry_info_btn", help="Show towel-dry details"):
                st.session_state.towel_dry_info = not st.session_state.get("towel_dry_info", False)

        if st.session_state.get("towel_dry_info", False):
            st.markdown(f"""
            <div class="phase-details visible">
            <strong>Remaining Wetness:</strong> {results["towel_levels"][selected_towel_idx]}%<br>
            <strong>Reduces blow-dry time by:</strong> ~{reduction}%<br><br>
            <strong>Visual Progress Guide:</strong><br>
            🚫 Dripping or pooling: Too wet (0-30%)<br>
            💧 Towel heavy, hair saturated: ~40%<br>
            🤏 Towel less damp, drips stop: ~60-70%<br>
            ✓ Hair moist, lifts easily, ready to dry: ~80%
            </div>
            """, unsafe_allow_html=True)

        # Air-dry phase - always visible with button
        col_air_label, col_air_btn = st.columns([0.9, 0.1])
        with col_air_label:
            if selected_result['hybrid_drying_recommended']:
                st.markdown(f"""<div class="result-item phase-section">
                    <span class="result-label">Air Dry Phase</span>
                    <span class="result-value">{selected_result['air_dry_minutes']} min</span>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="result-item phase-section disabled">
                    <span class="result-label disabled">Air Dry Phase: Not recommended</span>
                </div>""", unsafe_allow_html=True)
        with col_air_btn:
            if st.button("ⓘ", key="air_dry_info_btn", help="Show air-dry details"):
                st.session_state.air_dry_info = not st.session_state.get("air_dry_info", False)

        if st.session_state.get("air_dry_info", False):
            st.markdown("""
            <div class="phase-details visible">
            <strong>Temperature:</strong> Room temperature<br>
            <strong>Benefit:</strong> No heat required, reduces heat damage
            </div>
            """, unsafe_allow_html=True)

        # Bulk phase - always visible
        col_bulk_label, col_bulk_btn = st.columns([0.9, 0.1])
        with col_bulk_label:
            st.markdown(f"""<div class="result-item phase-section">
                <span class="result-label">Bulk Phase ({selected_result['heat_setting']} heat)</span>
                <span class="result-value">{selected_result['bulk_time']} min</span>
            </div>""", unsafe_allow_html=True)
        with col_bulk_btn:
            if st.button("ⓘ", key="bulk_phase_info_btn", help="Show bulk phase details"):
                st.session_state.bulk_phase_info = not st.session_state.get("bulk_phase_info", False)

        if st.session_state.get("bulk_phase_info", False):
            st.markdown(f"""
            <div class="phase-details visible">
            <strong>Temperature:</strong> {selected_result['temp_range']}<br>
            <strong>Distance:</strong> {selected_result['distance']}<br>
            <strong>Target:</strong> ~90% dry
            </div>
            """, unsafe_allow_html=True)

        # Finish phase - always visible
        col_finish_label, col_finish_btn = st.columns([0.9, 0.1])
        with col_finish_label:
            st.markdown(f"""<div class="result-item phase-section">
                <span class="result-label">Finish Phase (Low/Medium heat)</span>
                <span class="result-value">{selected_result['finish_time']} min</span>
            </div>""", unsafe_allow_html=True)
        with col_finish_btn:
            if st.button("ⓘ", key="finish_phase_info_btn", help="Show finish phase details"):
                st.session_state.finish_phase_info = not st.session_state.get("finish_phase_info", False)

        if st.session_state.get("finish_phase_info", False):
            st.markdown(f"""
            <div class="phase-details visible">
            <strong>Temperature:</strong> {selected_result['finish_temp_range']}<br>
            <strong>Distance:</strong> {selected_result['finish_distance']}<br>
            <strong>Target:</strong> ~10% dry
            </div>
            """, unsafe_allow_html=True)

        # Total time - PROMINENTLY DISPLAYED
        st.markdown(f"""
        <div style='border-left: 3px solid #21898D; padding: 0.75rem 1rem; margin: 1.5rem 0;'>
            <div style='display: flex; align-items: center; justify-content: space-between;'>
                <span style='font-size: 12px; font-weight: 600; color: var(--color-text); text-transform: uppercase; letter-spacing: 0.6px;'>Total Drying Time</span>
                <span style='font-size: 20px; font-weight: 700; color: #21898D;'>⏱️ {selected_result['total_time']} min</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if selected_result.get('warnings'):
            st.markdown(f'<div class="warning">{"<br>".join(selected_result["warnings"])}</div>', unsafe_allow_html=True)
    
    with col_energy:
        st.markdown('### ⚡ Energy Cost')

        # Calculate energy and cost from stored data
        bulk_power = power_map[selected_result["heat_setting"]]
        finish_idx = max(0, selected_result["heat_index"] - 1)
        finish_power = power_map[heat_settings[finish_idx]["name"]]
        energy_kwh = (bulk_power * selected_result["bulk_time"] + finish_power * selected_result["finish_time"]) / 60000
        cost = selected_result["cost"]  # Use pre-calculated cost that matches the chart

        st.markdown(f"""
        <div class="result-item">
            <span class="result-label">Electricity Price</span>
            <span class="result-value">€{elec_price:.4f}/kWh</span>
        </div>
        <div class="result-item">
            <span class="result-label">Hair Dryer Power</span>
            <span class="result-value">{int((bulk_power + finish_power)/2)}W</span>
        </div>
        <div class="result-item">
            <span class="result-label">Total Energy Used</span>
            <span class="result-value">{energy_kwh:.3f} kWh</span>
        </div>
        <div class="result-item">
            <span class="result-label">Estimated Cost</span>
            <span class="result-value">€{cost:.3f}</span>
        </div>
        """, unsafe_allow_html=True)

        is_recommended = result_idx == results["lowest_cost_idx"]
        priority_pct = int(results["priorities"][selected_priority_idx] * 100)
        if is_recommended:
            st.markdown(f'<div class="recommended-badge">✓ Recommended: Priority {priority_pct}%, {results["towel_levels"][selected_towel_idx]}% Wetness (Lowest Cost)</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="recommended-badge">Priority {priority_pct}%, {results["towel_levels"][selected_towel_idx]}% Wetness</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
    # Row 3: Cost Chart
    st.markdown('### 📊 Cost Analysis by Priority & Towel-Dry Level')

    # Create chart
    fig = go.Figure()
    colors = ['rgba(33, 128, 141, 0.8)', 'rgba(33, 128, 141, 0.5)', 'rgba(33, 128, 141, 0.3)']

    for i, towel_level in enumerate(results["towel_levels"]):
        level_costs = [c["cost"] for c in results["costs_data"] if c["towel_level"] == towel_level]
        fig.add_trace(go.Bar(
            name=f'{towel_level}% Wetness',
            x=[f'{int(p*100)}%' for p in results["priorities"]],
            y=level_costs,
            marker_color=colors[i],
            marker_line_color='rgba(33, 128, 141, 1)',
            marker_line_width=2,
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Priority: %{x}<br>' +
                         'Cost: €%{y:.4f}<extra></extra>'
        ))

    fig.update_layout(
        xaxis_title="Time Priority (0% Gentle → 100% Fast)",
        yaxis_title="Cost (€)",
        barmode='group',
        height=280,
        showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e293b', size=12),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        margin=dict(l=40, r=20, t=20, b=40)
    )

    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

    # Add instruction text
    st.markdown("""
    <div class="info">
    💡 <strong>Tip:</strong> Use the selectors below to explore different drying strategies. Try different priority levels (0% = gentle, 100% = fast) and towel-dry levels to find your preferred balance between time and energy cost.
    </div>
    """, unsafe_allow_html=True)


st.markdown("---")
st.markdown("*Powered by Open-Meteo weather API, REE electricity prices (Spain), & regional energy rates*")

# === ADD THIS AT THE VERY END (after all existing Streamlit code) ===
import os
import subprocess
import threading
import atexit

def start_api_server():
    """Start mock API in background"""
    api_path = os.path.join(os.path.dirname(__file__), "api", "mock_protocol_api.py")
    subprocess.Popen(["python", api_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Start API server when Streamlit starts
api_thread = threading.Thread(target=start_api_server, daemon=True)
api_thread.start()
print("🚀 Mock API started: http://127.0.0.1:8000/protocol")
