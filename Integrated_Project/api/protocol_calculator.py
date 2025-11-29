"""
Shared protocol calculation logic for hair dryer safety system.
Used by both StreamlitDashboard and mock_protocol_api.
"""

from typing import Dict, Tuple, Optional
import requests


def fetch_room_conditions(location: str) -> Tuple[float, float]:
    """
    Fetch temperature and humidity for a given location using Open-Meteo API.
    
    Args:
        location: City name or coordinates
        
    Returns:
        Tuple of (temperature_celsius, humidity_percent)
        Falls back to (20.0, 60.0) if API fails
    """
    try:
        # Geocode location
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        geo_data = requests.get(geo_url, timeout=5).json()
        
        if geo_data.get("results"):
            lat = geo_data["results"][0]["latitude"]
            lon = geo_data["results"][0]["longitude"]
        else:
            # Fallback to Barcelona coordinates
            lat, lon = 41.3874, 2.1686
        
        # Get weather data
        weather_url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&"
                       "current=temperature_2m,relative_humidity_2m&timezone=auto")
        weather_data = requests.get(weather_url, timeout=5).json()
        
        temp = weather_data["current"]["temperature_2m"]
        humidity = weather_data["current"]["relative_humidity_2m"]
        
        return float(temp), float(humidity)
    except Exception as e:
        print(f"Error fetching room conditions: {e}")
        return 20.0, 60.0


def fetch_electricity_price(location: str) -> float:
    """
    Fetch electricity price for a location.
    Tries REE API for Spain, falls back to regional price map.
    
    Args:
        location: City name or country
        
    Returns:
        Electricity price in €/kWh
    """
    from datetime import datetime, timedelta, timezone
    
    try:
        # Check if location is Spain
        is_spain = any(city in location.lower() for city in ["spain", "barcelona", "madrid", "bilbao", "valencia", "seville"])
        
        if is_spain:
            try:
                endpoint = 'https://apidatos.ree.es'
                get_archives = '/en/datos/mercados/precios-mercados-tiempo-real'
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Host': 'apidatos.ree.es'
                }
                
                # Get today's data
                utc_tz = timezone.utc
                today = datetime.now(utc_tz).replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT00:00:00Z')
                tomorrow = (datetime.now(utc_tz) + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT00:00:00Z')
                
                params = {
                    'start_date': today,
                    'end_date': tomorrow,
                    'time_trunc': 'hour'
                }
                
                response = requests.get(
                    endpoint + get_archives,
                    headers=headers,
                    params=params,
                    timeout=(3, 10)
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'included' in data and len(data['included']) > 0:
                        prices = data['included'][0].get('attributes', {}).get('values', [])
                        if prices:
                            current_hour = datetime.now().hour
                            if current_hour < len(prices):
                                price_mwh = prices[current_hour]['value']
                                price_kwh = price_mwh / 1000  # Convert €/MWh to €/kWh
                                return float(price_kwh)
            except Exception as e:
                print(f"REE API error: {e}")
        
        # Fallback to regional price map
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
        return next((v for k, v in price_map.items() if k in location.lower()), 0.26)
    except Exception as e:
        print(f"Error fetching electricity price: {e}")
        return 0.26


def evaluate_air_drying_suitability(temperature: float, humidity: float, drying_power: float, time_priority: float) -> bool:
    """Check if environment is safe for partial air drying"""
    return (
        temperature >= 18 and
        humidity < 75 and
        drying_power >= 0.5 and
        time_priority <= 0.7
    )


def calculate_air_dry_duration(time_priority: float, hair_type: str) -> float:
    """Calculate air drying duration based on conditions"""
    air_dry_minutes = 20 + (1 - time_priority) * 10
    multipliers = {"fine": 0.8, "medium": 1.0, "thick": 1.2}
    air_dry_minutes *= multipliers[hair_type]
    return min(30, air_dry_minutes)


def calculate_phase_times(
    temp: float,
    humidity: float,
    hair_type: str,
    porosity: str,
    towel_level: float,
    time_priority: float,
) -> Dict:
    """
    Calculate drying phase times and parameters.
    
    Args:
        temp: Temperature in Celsius
        humidity: Humidity percentage (0-100)
        hair_type: One of "fine", "medium", "thick"
        porosity: One of "low", "normal", "high"
        towel_level: Remaining wetness percentage (0-100)
        time_priority: Time priority (0.0-1.0, where 1.0 = fastest)
    
    Returns:
        Dict containing phase times and parameters
    """
    # Drying power
    dp = (1 - humidity / 100) * (1 + 0.02 * (temp - 20))
    
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
    
    # Store energy for later cost calculation with actual electricity price
    cost = energy_kwh  # Will be multiplied by actual elec_price later
    
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
        "cost": cost,
        "hybrid_drying_recommended": hybrid_drying_recommended,
        "air_dry_minutes": round(air_dry_minutes, 1),
        "bulk_power": bulk_power,
        "finish_power": finish_power,
        "energy_kwh": energy_kwh,
    }


def get_heat_settings() -> list:
    """Get standard heat settings"""
    return [
        {"name": "Low", "temp": "50-60°C", "distance": "18-20 cm"},
        {"name": "Medium", "temp": "70-80°C", "distance": "15-18 cm"},
        {"name": "High", "temp": "90-100°C", "distance": "18-20 cm"}
    ]


def get_power_map() -> Dict[str, int]:
    """Get power consumption map for heat settings"""
    return {"Low": 800, "Medium": 1200, "High": 1500}


def calculate_protocol(
    temp: float,
    humidity: float,
    hair_type: str,
    porosity: str,
    towel_level: float,
    time_priority: float,
    temp_threshold: float,
    current_threshold: float,
) -> Dict:
    """
    Calculate complete safety protocol with thresholds.
    
    This is the main entry point for protocol generation.
    
    Args:
        temp: Temperature in Celsius
        humidity: Humidity percentage (0-100)
        hair_type: One of "fine", "medium", "thick"
        porosity: One of "low", "normal", "high"
        towel_level: Remaining wetness percentage (0-100)
        time_priority: Time priority (0.0-1.0, where 1.0 = fastest)
        temp_threshold: Temperature threshold in Celsius
        current_threshold: Current threshold in Amperes
    
    Returns:
        Dict containing:
        - conditions: list of safety conditions (temperature, current)
        - max_total_runtime_ms: maximum runtime in milliseconds
        - phase_times: dict with drying phase information
    """
    # Calculate phase times
    phase_times = calculate_phase_times(
        temp=temp,
        humidity=humidity,
        hair_type=hair_type,
        porosity=porosity,
        towel_level=towel_level,
        time_priority=time_priority,
    )
    
    # Duration based on actual phase times (in milliseconds)
    bulk_duration_ms = int(phase_times['bulk_time'] * 60 * 1000)  # Bulk phase in ms
    total_duration_ms = int(phase_times['total_time'] * 60 * 1000)  # Total drying time in ms
    
    return {
        "conditions": [
            {
                "sensor_type": "temperature",
                "threshold": round(temp_threshold, 2),
                "duration_ms": bulk_duration_ms
            },
            {
                "sensor_type": "current",
                "threshold": round(current_threshold, 2),
                "duration_ms": total_duration_ms
            }
        ],
        "max_total_runtime_ms": 1800000,  # 30 minutes default
        "phase_times": phase_times,
    }


def calculate_all_recommendations(
    temp: float,
    humidity: float,
    hair_type: str,
    porosity: str,
    elec_price: float,
    priorities: list = None,
    towel_dry_levels: list = None,
) -> Dict:
    """
    Generate all recommendation combinations for analysis.
    
    Used by StreamlitDashboard to show cost analysis across all parameters.
    
    Args:
        temp: Temperature in Celsius
        humidity: Humidity percentage (0-100)
        hair_type: One of "fine", "medium", "thick"
        porosity: One of "low", "normal", "high"
        elec_price: Electricity price in €/kWh
        priorities: List of time priority values (default: [0.0, 0.1, ..., 1.0])
        towel_dry_levels: List of towel-dry levels (default: [50, 65, 80])
    
    Returns:
        Dict with:
        - all_results: list of all calculated recommendations
        - costs_data: list of cost data for charting
        - lowest_cost_idx: index of lowest cost result
        - optimal_result: the optimal (lowest cost) recommendation
    """
    import numpy as np
    
    if priorities is None:
        priorities = [round(x, 1) for x in np.arange(0, 1.1, 0.1)]
    if towel_dry_levels is None:
        towel_dry_levels = [50, 65, 80]
    
    all_results = []
    costs_data = []
    
    # Generate all combinations
    for towel_level in towel_dry_levels:
        for priority in priorities:
            phase_times = calculate_phase_times(
                temp=temp,
                humidity=humidity,
                hair_type=hair_type,
                porosity=porosity,
                towel_level=towel_level,
                time_priority=priority,
            )
            
            # Add metadata
            phase_times["towel_level"] = towel_level
            phase_times["priority"] = priority
            
            # Calculate cost
            cost = phase_times["energy_kwh"] * elec_price
            phase_times["cost"] = cost
            
            all_results.append(phase_times)
            costs_data.append({
                "cost": cost,
                "priority": priority,
                "towel_level": towel_level
            })
    
    # Find lowest cost
    lowest_cost_idx = min(range(len(costs_data)), key=lambda i: costs_data[i]["cost"])
    optimal_result = all_results[lowest_cost_idx]
    
    return {
        "all_results": all_results,
        "costs_data": costs_data,
        "lowest_cost_idx": lowest_cost_idx,
        "optimal_result": optimal_result,
        "priorities": priorities,
        "towel_levels": towel_dry_levels,
    }
