import streamlit as st
import requests
import json
import math
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Hair Dryer Assistant", layout="wide")

# Load external CSS
with open("/Users/para/Desktop/automation/Nov27/styles.css") as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

# Helper functions - MUST be defined before use
def evaluate_air_drying_suitability(temperature, humidity, drying_power, time_priority):
    """Check if environment is safe for partial air drying"""
    return (
        temperature >= 18 and
        humidity < 75 and
        drying_power >= 0.5 and
        time_priority <= 0.7
    )

def calculate_air_dry_duration(time_priority, hair_type):
    """Calculate air drying duration based on conditions"""
    air_dry_minutes = 20 + (1 - time_priority) * 10
    multipliers = {"fine": 0.8, "medium": 1.0, "thick": 1.2}
    air_dry_minutes *= multipliers[hair_type]
    return min(30, air_dry_minutes)

def calculate_recommendations(temp, humidity, hair_type, porosity, towel_level, time_priority):
    """Calculate recommendations based on conditions"""
    
    # Drying power
    dp = (1 - humidity/100) * (1 + 0.02 * (temp - 20))
    
    # Heat index calculation
    heat_idx = {"fine": 0, "medium": 1, "thick": 2}[hair_type]
    if porosity == "low":
        heat_idx += 1
    if porosity == "high":
        heat_idx -= 1
    
    # Environment adjustment
    if dp < 0.6:
        heat_idx += 1
    if dp > 1.2:
        heat_idx -= 1
    
    # Priority adjustment
    heat_idx += round(0.5 * (time_priority - 0.5))
    
    # Clamp
    heat_idx = max(0, min(2, heat_idx))
    
    # Heat settings
    heat_settings = [
        {"name": "Low", "temp": "50-60°C", "distance": "18-20 cm"},
        {"name": "Medium", "temp": "70-80°C", "distance": "15-18 cm"},
        {"name": "High", "temp": "90-100°C", "distance": "18-20 cm"}
    ]
    
    bulk_heat = heat_settings[heat_idx]
    finish_heat = heat_settings[max(0, heat_idx - 1)]
    
    # Time calculations
    bulk_time = (2 + (towel_level - 50) / 25) * {"fine": 0.7, "medium": 1.0, "thick": 1.4}[hair_type]
    bulk_time /= (0.5 + dp * 0.5)
    bulk_time /= (1 + time_priority * 0.3)
    
    finish_time = (0.5 + (towel_level - 50) / 50) * {"fine": 0.6, "medium": 1.0, "thick": 1.3}[hair_type]
    
    # Evaluate hybrid drying
    hybrid_drying_recommended = evaluate_air_drying_suitability(temp, humidity, dp, time_priority)
    air_dry_minutes = 0
    modified_bulk_time = bulk_time
    modified_finish_time = finish_time
    
    if hybrid_drying_recommended:
        air_dry_minutes = calculate_air_dry_duration(time_priority, hair_type)
        modified_bulk_time = bulk_time * 0.6
        modified_finish_time = finish_time * 0.7
    
    total_time = modified_bulk_time + modified_finish_time
    
    # Environment type
    if humidity >= 70 and temp <= 18:
        env_type = "Humid & Cool"
    elif humidity >= 70 and temp > 18:
        env_type = "Humid & Warm"
    elif humidity < 70 and temp <= 18:
        env_type = "Dry & Cool"
    else:
        env_type = "Dry & Warm"
    
    # Energy cost
    power_map = {"Low": 800, "Medium": 1200, "High": 1500}
    bulk_power = power_map[bulk_heat["name"]]
    finish_power = power_map[finish_heat["name"]]
    energy_kwh = (bulk_power * modified_bulk_time + finish_power * modified_finish_time) / 60000
    
    # Use default electricity price for now (will be overridden in main code)
    elec_price = 0.26
    cost = energy_kwh * elec_price
    
    # Warnings and tips
    warnings = []
    tips = []
    
    if heat_idx == 2:
        warnings.append("⚠️ Using high heat setting. Keep the dryer moving continuously and maintain distance to prevent damage.")
    if dp < 0.6:
        tips.append("💡 High humidity detected. Emphasize airflow and movement. Expect longer drying time.")
    if dp > 1.2:
        tips.append("💡 Favorable drying conditions. You can use lower heat for gentler drying.")
    if hair_type == "fine" and heat_idx >= 1:
        warnings.append("⚠️ Fine hair is more vulnerable to heat damage. Consider reducing heat if time allows.")
    if towel_level > 85:
        tips.append("💡 Hair is quite wet. Towel-dry more thoroughly to reduce heat exposure time.")
    if hybrid_drying_recommended:
        tips.append("🌿 Hybrid drying recommended! Start with natural air drying, then finish with gentle blow drying. This reduces heat damage while avoiding prolonged wetness.")
    
    return {
        "dp": dp,
        "env_type": env_type,
        "heat_index": heat_idx,
        "heat_setting": bulk_heat["name"],
        "temp_range": bulk_heat["temp"],
        "distance": bulk_heat["distance"],
        "finish_temp_range": finish_heat["temp"],
        "finish_distance": finish_heat["distance"],
        "bulk_time": round(modified_bulk_time, 1),
        "finish_time": round(modified_finish_time, 1),
        "total_time": round(total_time, 1),
        "warnings": warnings,
        "tips": tips,
        "cost": cost,
        "hybrid_drying_recommended": hybrid_drying_recommended,
        "air_dry_minutes": round(air_dry_minutes, 1)
    }



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
    hair_type = st.selectbox("Hair Thickness", ["Fine", "Medium", "Thick"], index=1, label_visibility="visible", key="thickness_input")
    hair_type = hair_type.lower()
    st.markdown('</div>', unsafe_allow_html=True)

with col_porosity:
    st.markdown('<div class="input-group minimal-input">', unsafe_allow_html=True)
    porosity = st.selectbox("Hair Porosity", ["Low", "Normal", "High"], index=1, label_visibility="visible", key="porosity_input")
    porosity = porosity.lower() if porosity != "Normal" else "normal"
    st.markdown('</div>', unsafe_allow_html=True)

with col_button:
    st.markdown('<div style="padding-top: 18px;">', unsafe_allow_html=True)
    generate_btn = st.button("Generate", key="generate_btn")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Processing
if generate_btn:
    try:
        # Fetch weather
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        geo_data = requests.get(geo_url).json()
        if geo_data.get("results"):
            lat = geo_data["results"][0]["latitude"]
            lon = geo_data["results"][0]["longitude"]
        else:
            lat, lon = 41.3874, 2.1686
        
        weather_data = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&"
            "current=temperature_2m,relative_humidity_2m&timezone=auto"
        ).json()
        
        temp = weather_data["current"]["temperature_2m"]
        humidity = weather_data["current"]["relative_humidity_2m"]
        
        # Electricity price mapping
        price_map = {
            "spain": 0.28, "barcelona": 0.28, "madrid": 0.28,
            "france": 0.22, "paris": 0.22,
            "germany": 0.35, "berlin": 0.35,
            "italy": 0.26, "rome": 0.26,
            "uk": 0.28, "london": 0.28,
            "netherlands": 0.30, "amsterdam": 0.30,
            "portugal": 0.25, "lisbon": 0.25,
            "sweden": 0.18, "denmark": 0.24,
            "poland": 0.20, "greece": 0.24, "athens": 0.24,
            "usa": 0.16, "canada": 0.14,
            "australia": 0.32, "japan": 0.30
        }
        elec_price = next((v for k, v in price_map.items() if k in location.lower()), 0.26)
        
    except:
        temp, humidity, elec_price = 20, 60, 0.26

    # Generate FULL 2D matrix
    priorities = [round(x, 1) for x in np.arange(0, 1.1, 0.1)]
    towel_dry_levels = [50, 65, 80]
    
    all_results = []
    costs_data = []
    
    # Calculate all combinations
    for towel_level in towel_dry_levels:
        for priority in priorities:
            rec = calculate_recommendations(temp, humidity, hair_type, porosity, towel_level, priority)
            rec["towel_level"] = towel_level
            rec["priority"] = priority
            all_results.append(rec)
            costs_data.append({"cost": rec["cost"], "priority": priority, "towel_level": towel_level})
    
    # Find lowest cost
    lowest_cost_idx = min(range(len(costs_data)), key=lambda i: costs_data[i]["cost"])
    
    st.session_state.results = {
        "weather": {"temp": temp, "humidity": humidity},
        "location": location,
        "elec_price": elec_price,
        "all_results": all_results,
        "costs_data": costs_data,
        "lowest_cost_idx": lowest_cost_idx,
        "priorities": priorities,
        "towel_levels": towel_dry_levels
    }

# Results Section
if "results" in st.session_state:
    results = st.session_state.results
    temp = results["weather"]["temp"]
    humidity = results["weather"]["humidity"]
    elec_price = results["elec_price"]

    # Default selection
    selected_priority_idx = st.session_state.get("selected_priority_idx", results["lowest_cost_idx"] // len(results["towel_levels"]))
    selected_towel_idx = st.session_state.get("selected_towel_idx", results["lowest_cost_idx"] % len(results["towel_levels"]))

    result_idx = selected_priority_idx * len(results["towel_levels"]) + selected_towel_idx
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
            st.markdown(f"""<div class="result-item">
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

        # Air-dry phase - always visible if recommended
        if selected_result['hybrid_drying_recommended']:
            col_air_label, col_air_btn = st.columns([0.9, 0.1])
            with col_air_label:
                st.markdown(f"""<div class="result-item">
                    <span class="result-label">Air Dry Phase</span>
                    <span class="result-value">{selected_result['air_dry_minutes']} min</span>
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
        else:
            st.markdown(f"""
            <div class="result-item disabled">
                <span class="result-label disabled">Air Dry Phase: Not recommended</span>
            </div>
            """, unsafe_allow_html=True)

        # Bulk phase - always visible
        col_bulk_label, col_bulk_btn = st.columns([0.9, 0.1])
        with col_bulk_label:
            st.markdown(f"""<div class="result-item">
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
            st.markdown(f"""<div class="result-item">
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
                <span style='font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.6px;'>Total Drying Time</span>
                <span style='font-size: 20px; font-weight: 700; color: #21898D;'>⏱️ {selected_result['total_time']} min</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if selected_result.get('warnings'):
            st.markdown(f'<div class="warning">{"<br>".join(selected_result["warnings"])}</div>', unsafe_allow_html=True)
    
    with col_energy:
        st.markdown('### ⚡ Energy Cost')

        # Calculate cost
        bulk_power = power_map[selected_result["heat_setting"]]
        finish_idx = max(0, selected_result["heat_index"] - 1)
        finish_power = power_map[heat_settings[finish_idx]["name"]]
        energy_kwh = (bulk_power * selected_result["bulk_time"] + finish_power * selected_result["finish_time"]) / 60000
        cost = energy_kwh * elec_price

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
    st.markdown('<div class="section">', unsafe_allow_html=True)
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

    # Interactive Selection Controls
    col_priority, col_towel = st.columns(2)

    with col_priority:
        selected_priority = st.selectbox(
            "🎯 Priority Level",
            options=[f"{int(p*100)}%" for p in results["priorities"]],
            index=selected_priority_idx,
            key="priority_selector",
            help="0% = Gentle/Slow | 100% = Fast/High Heat"
        )
        selected_priority_idx = results["priorities"].index(float(selected_priority.strip('%')) / 100)

    with col_towel:
        selected_towel = st.selectbox(
            "💧 Towel-Dry Level",
            options=[f"{int(t)}% Wetness" for t in results["towel_levels"]],
            index=selected_towel_idx,
            key="towel_selector",
            help="Remaining wetness after towel drying"
        )
        selected_towel_idx = results["towel_levels"].index(int(selected_towel.split('%')[0]))

    # Update selected result based on user selection
    result_idx = selected_priority_idx * len(results["towel_levels"]) + selected_towel_idx
    selected_result = results["all_results"][result_idx]

    # Store in session state for persistence
    st.session_state.selected_priority_idx = selected_priority_idx
    st.session_state.selected_towel_idx = selected_towel_idx

    st.markdown('</div>', unsafe_allow_html=True)

# Instructions
with st.expander("ℹ️ How to use"):
    st.markdown("""
    **📊 Cost Chart:**
    - **X-axis**: Time priority (0%=Gentle/slower, 100%=Fast/higher heat)
    - **Y-axis**: Energy cost in €
    - **Colors**: Towel-dry levels (50%, 65%, 80% wetness remaining)
    
    **🎯 Lowest cost settings highlighted**
    
    **💡 Tips:**
    - Lower towel-dry levels (more towel drying) = lower energy cost
    - Higher priority (faster) = higher energy cost
    - Environment conditions affect drying time significantly
    """)

st.markdown("---")
st.markdown("*Powered by Open-Meteo weather API & real-time energy calculations*")
