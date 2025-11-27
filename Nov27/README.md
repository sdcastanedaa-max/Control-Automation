# Hair Dryer Assistant - Streamlit Version

An interactive hair drying recommendation assistant that calculates optimal drying strategies based on environmental conditions, hair type, and porosity.

## Features

✨ **Interactive Design**
- Modern, responsive UI matching the HTML version
- Real-time weather data from Open-Meteo API
- Auto-detected electricity prices by location
- External CSS styling for consistency

🎯 **Smart Recommendations**
- Priority-based drying strategies (gentle to fast)
- Towel-dry level optimization
- Hybrid air-drying recommendations
- Energy cost calculations
- Hair damage risk assessment

📊 **Data Visualization**
- Interactive cost analysis charts
- Grouped by priority and towel-dry levels
- Selectable combinations to explore different options

## Setup

### Requirements
```bash
pip install streamlit plotly requests numpy
```

### Running the App

```bash
streamlit run StreamlitDashboard.py
```

The app will open at `http://localhost:8501`

## Files

- `StreamlitDashboard.py` - Main Python application
- `styles.css` - External CSS styling (auto-loaded)
- `README.md` - This file

## How to Use

1. **Enter Location** - City name or coordinates (e.g., "Barcelona" or "41.3874,2.1686")
2. **Select Hair Characteristics**
   - Hair Thickness: Fine, Medium, or Thick
   - Hair Porosity: Low, Normal, or High
3. **Generate Recommendations** - Click the button to fetch weather and calculate results
4. **Select Strategy** - Use the dropdowns to explore different priority/towel-dry combinations
5. **View Results**
   - Drying protocol with phases
   - Energy cost breakdown
   - Cost comparison chart
   - Warnings and tips

## Key Features

### Hybrid Drying
When conditions allow, the app recommends combining air-drying with blow-drying to reduce heat damage.

### Interactive Selection
Click on chart bars or use the dropdowns to instantly update recommendations for different combinations.

### Smart Pricing
Electricity prices auto-detect based on location, with fallback to European averages.

### Warnings & Tips
Real-time alerts for:
- High heat settings
- High humidity
- Favorable drying conditions
- Fine hair heat damage risks
- Wet hair recommendations

## Technical Details

- **Weather API**: Open-Meteo (free, no key required)
- **Geolocation**: Open-Meteo Geocoding + Nominatim (optional)
- **Charts**: Plotly for interactive visualizations
- **Styling**: CSS with CSS variables for dark mode support

## Notes

- The CSS file must be in the same directory as the Python script
- Dark mode is automatically detected and applied
- All calculations are real-time based on actual weather data
- Energy costs use region-specific electricity prices
