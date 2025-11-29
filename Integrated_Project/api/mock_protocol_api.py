from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List
import uvicorn
import logging
from datetime import datetime
import os
from protocol_calculator import calculate_protocol

logger = logging.getLogger(__name__)

app = FastAPI(title="Hair Dryer Safety Protocol API")

class Condition(BaseModel):
    sensor_type: str  # "temperature" or "current"
    threshold: float
    duration_ms: int

class Protocol(BaseModel):
    conditions: List[Condition]
    max_total_runtime_ms: int = 1800000  # 30 min default

@app.get("/protocol", response_model=Protocol)
async def get_protocol(
    temp: float = Query(22.0, description="Temperature in Celsius"),
    humidity: float = Query(55.0, description="Humidity percentage (0-100)"),
    hair_type: str = Query("medium", description="One of: fine, medium, thick"),
    porosity: str = Query("normal", description="One of: low, normal, high"),
    towel_level: float = Query(80.0, description="Remaining wetness percentage (0-100)"),
    time_priority: float = Query(0.5, description="Time priority (0.0-1.0, 1.0=fastest)"),
    temp_threshold: float = Query(110.0, description="Temperature threshold in Celsius"),
    current_threshold: float = Query(7.5, description="Current threshold in Amperes"),
) -> Protocol:
    """
    Generate safety protocol based on user inputs and environmental conditions.
    
    Query Parameters:
    - temp: Room/environmental temperature in Celsius
    - humidity: Environmental humidity percentage
    - hair_type: Hair thickness (fine, medium, thick)
    - porosity: Hair porosity (low, normal, high)
    - towel_level: Remaining wetness after towel dry (0-100%)
    - time_priority: Time priority level (0.0=gentle, 1.0=fast)
    - temp_threshold: Temperature threshold in Celsius
    - current_threshold: Current threshold in Amperes
    """
    try:
        # Calculate complete protocol using shared calculator
        protocol_data = calculate_protocol(
            temp=temp,
            humidity=humidity,
            hair_type=hair_type,
            porosity=porosity,
            towel_level=towel_level,
            time_priority=time_priority,
            temp_threshold=temp_threshold,
            current_threshold=current_threshold,
        )
        
        # Convert conditions to Pydantic models
        conditions = [
            Condition(**cond) for cond in protocol_data["conditions"]
        ]
        
        return Protocol(
            conditions=conditions,
            max_total_runtime_ms=protocol_data["max_total_runtime_ms"]
        )
        
    except Exception as e:
        logger.error(f"Protocol error: {e}")
        # Fallback defaults
        return Protocol(
            conditions=[
                Condition(sensor_type="temperature", threshold=80.0, duration_ms=5000),
                Condition(sensor_type="current", threshold=2.0, duration_ms=3000)
            ]
        )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
