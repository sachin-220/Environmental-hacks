"""
National Air Quality Index (NAQI) Calculation Engine (CPCB India Standard)
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class NationalAQICalculator:
    """
    Computes official Indian Central Pollution Control Board (CPCB) National Air Quality Index (NAQI).
    Calculates pollutant sub-indices, identifies the dominant pollutant, and assigns regulatory health categories.
    """

    # Official CPCB Breakpoints: (C_low, C_high, I_low, I_high)
    BREAKPOINTS: Dict[str, List[Tuple[float, float, float, float]]] = {
        "pm25": [
            (0.0, 30.0, 0.0, 50.0),
            (31.0, 60.0, 51.0, 100.0),
            (61.0, 90.0, 101.0, 200.0),
            (91.0, 120.0, 201.0, 300.0),
            (121.0, 250.0, 301.0, 400.0),
            (250.1, 500.0, 401.0, 500.0)
        ],
        "pm10": [
            (0.0, 50.0, 0.0, 50.0),
            (51.0, 100.0, 51.0, 100.0),
            (101.0, 250.0, 101.0, 200.0),
            (251.0, 350.0, 201.0, 300.0),
            (351.0, 430.0, 301.0, 400.0),
            (430.1, 800.0, 401.0, 500.0)
        ],
        "no2": [
            (0.0, 40.0, 0.0, 50.0),
            (41.0, 80.0, 51.0, 100.0),
            (81.0, 180.0, 101.0, 200.0),
            (181.0, 280.0, 201.0, 300.0),
            (281.0, 400.0, 301.0, 400.0),
            (400.1, 800.0, 401.0, 500.0)
        ],
        "o3": [
            (0.0, 50.0, 0.0, 50.0),
            (51.0, 100.0, 51.0, 100.0),
            (101.0, 168.0, 101.0, 200.0),
            (169.0, 208.0, 201.0, 300.0),
            (209.0, 748.0, 301.0, 400.0),
            (748.1, 1000.0, 401.0, 500.0)
        ],
        "so2": [
            (0.0, 40.0, 0.0, 50.0),
            (41.0, 80.0, 51.0, 100.0),
            (81.0, 380.0, 101.0, 200.0),
            (381.0, 800.0, 201.0, 300.0),
            (801.0, 1600.0, 301.0, 400.0),
            (1600.1, 2000.0, 401.0, 500.0)
        ],
        "co": [
            (0.0, 1.0, 0.0, 50.0),
            (1.1, 2.0, 51.0, 100.0),
            (2.1, 10.0, 101.0, 200.0),
            (10.1, 17.0, 201.0, 300.0),
            (17.1, 34.0, 301.0, 400.0),
            (34.1, 50.0, 401.0, 500.0)
        ]
    }

    @classmethod
    def calculate_sub_index(cls, pollutant: str, conc: float) -> Optional[float]:
        """
        Calculates linear interpolated sub-index:
        I = I_low + ((I_high - I_low) / (C_high - C_low)) * (C - C_low)
        """
        key = pollutant.lower().replace(".", "").replace("_", "")
        # Map common keys
        if key in ["pm25", "pm25dry"]:
            key = "pm25"
        elif key in ["pm10"]:
            key = "pm10"
        elif key in ["no2", "nox"]:
            key = "no2"
        elif key in ["o3", "ozone"]:
            key = "o3"
        elif key in ["so2"]:
            key = "so2"
        elif key in ["co"]:
            key = "co"

        if key not in cls.BREAKPOINTS:
            return None

        if conc < 0.0:
            conc = 0.0

        table = cls.BREAKPOINTS[key]
        for c_low, c_high, i_low, i_high in table:
            if c_low <= conc <= c_high:
                sub_index = i_low + ((i_high - i_low) / (c_high - c_low)) * (conc - c_low)
                return float(np.clip(sub_index, 0.0, 500.0))

        # If concentration exceeds highest bracket, cap at 500
        if conc > table[-1][1]:
            return 500.0
        return 0.0

    @classmethod
    def get_aqi_category(cls, aqi_value: float) -> str:
        """Assigns official CPCB health category"""
        if aqi_value <= 50.0:
            return "Good"
        elif aqi_value <= 100.0:
            return "Satisfactory"
        elif aqi_value <= 200.0:
            return "Moderate"
        elif aqi_value <= 300.0:
            return "Poor"
        elif aqi_value <= 400.0:
            return "Very Poor"
        else:
            return "Severe"

    @classmethod
    def evaluate_aqi(cls, pollutant_concentrations: Dict[str, float]) -> Dict[str, Any]:
        """
        Computes NAQI for a collection of pollutant concentrations.
        Returns:
            aqi: overall max sub-index
            dominant_pollutant: pollutant driving the max AQI
            category: health category
            sub_indices: individual pollutant sub-indices
        """
        sub_indices = {}
        for pol, val in pollutant_concentrations.items():
            try:
                num_val = float(val)
            except (ValueError, TypeError):
                continue
            idx = cls.calculate_sub_index(pol, num_val)
            if idx is not None:
                sub_indices[pol] = round(idx, 1)

        if not sub_indices:
            return {
                "aqi": 0.0,
                "dominant_pollutant": "NONE",
                "category": "Unknown",
                "sub_indices": {}
            }

        max_pol = max(sub_indices, key=sub_indices.get)
        max_aqi = round(float(sub_indices[max_pol]), 1)
        category = cls.get_aqi_category(max_aqi)

        return {
            "aqi": max_aqi,
            "dominant_pollutant": max_pol,
            "category": category,
            "sub_indices": sub_indices
        }
