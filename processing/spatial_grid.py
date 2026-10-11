"""
Spatial Grid Generation, Domain Nesting, and Coordinate Mapping Engine
"""
import math
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from config.settings import settings, DomainBounds, DomainGridConfig
from config.logging_config import get_logger

logger = get_logger("processing.spatial_grid")


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on Earth in kilometers"""
    R = 6371.0  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def calculate_bearing_degrees(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate initial bearing from point 1 to point 2 in degrees [0, 360).
    0 = North, 90 = East, 180 = South, 270 = West.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - (math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda))
    initial_bearing = math.atan2(x, y)
    bearing_deg = (math.degrees(initial_bearing) + 360.0) % 360.0
    return bearing_deg


class SpatialGridManager:
    """Manages nested model grids (D01 27km, D02 9km, D03 3km) and point-to-grid remapping"""

    def __init__(self, domain_config: Optional[DomainGridConfig] = None):
        # Default to inner high-resolution Delhi NCR domain (D03, 3km)
        self.domain_config = domain_config or settings.NESTED_DOMAINS[2]
        self.grid_df = self._generate_grid()
        self._tree: Optional[cKDTree] = None
        self._build_spatial_index()

    def _generate_grid(self) -> pd.DataFrame:
        """
        Generate regular 2D grid cells across the domain bounding box.
        Approximates 1 deg lat ~ 111 km, 1 deg lon ~ 111 * cos(lat) km.
        """
        b = self.domain_config.bounds
        res_km = self.domain_config.resolution_km
        center_lat = (b.south + b.north) / 2.0
        
        # Grid step sizes in degrees
        d_lat = res_km / 111.0
        d_lon = res_km / (111.0 * math.cos(math.radians(center_lat)))
        
        lats = np.arange(b.south, b.north + (d_lat / 2.0), d_lat)
        lons = np.arange(b.west, b.east + (d_lon / 2.0), d_lon)
        
        rows = []
        for r_idx, lat in enumerate(lats):
            for c_idx, lon in enumerate(lons):
                grid_id = f"{self.domain_config.domain_id}_R{r_idx:02d}_C{c_idx:02d}"
                rows.append({
                    "grid_id": grid_id,
                    "domain_id": self.domain_config.domain_id,
                    "row_idx": r_idx,
                    "col_idx": c_idx,
                    "latitude": round(float(lat), 4),
                    "longitude": round(float(lon), 4),
                    "resolution_km": res_km
                })
        
        grid_df = pd.DataFrame(rows)
        logger.info(
            f"Generated grid {self.domain_config.domain_id} ({self.domain_config.name}): "
            f"{len(grid_df)} cells at {res_km} km resolution"
        )
        return grid_df

    def _build_spatial_index(self):
        """Construct KDTree for fast O(log N) nearest-neighbor lookups"""
        coords = self.grid_df[["latitude", "longitude"]].values
        self._tree = cKDTree(coords)

    def find_nearest_grid_cell(self, lat: float, lon: float) -> Dict[str, Any]:
        """Find the closest grid cell to a given lat/lon coordinate"""
        dist, idx = self._tree.query([lat, lon])
        cell = self.grid_df.iloc[idx].to_dict()
        exact_km = haversine_distance_km(lat, lon, cell["latitude"], cell["longitude"])
        cell["distance_km"] = round(exact_km, 3)
        return cell

    def map_points_to_grid(self, points_df: pd.DataFrame, lat_col: str = "latitude", lon_col: str = "longitude") -> pd.DataFrame:
        """Map a DataFrame of point observations (stations, fires) to grid cell IDs"""
        if points_df.empty or lat_col not in points_df.columns or lon_col not in points_df.columns:
            return points_df

        coords = points_df[[lat_col, lon_col]].values
        distances, indices = self._tree.query(coords)
        
        matched_cells = self.grid_df.iloc[indices].reset_index(drop=True)
        res_df = points_df.copy().reset_index(drop=True)
        res_df["grid_id"] = matched_cells["grid_id"]
        res_df["grid_latitude"] = matched_cells["latitude"]
        res_df["grid_longitude"] = matched_cells["longitude"]
        return res_df

    def bilinear_interpolate(self, lat: float, lon: float, values_grid: np.ndarray) -> float:
        """
        Perform 2D bilinear interpolation from a regular grid matrix.
        """
        # Ensure values_grid matches (rows, cols) of the current domain
        n_rows = self.grid_df["row_idx"].max() + 1
        n_cols = self.grid_df["col_idx"].max() + 1
        
        b = self.domain_config.bounds
        lat_frac = (lat - b.south) / (b.north - b.south) * (n_rows - 1)
        lon_frac = (lon - b.west) / (b.east - b.west) * (n_cols - 1)
        
        r0 = int(np.clip(math.floor(lat_frac), 0, n_rows - 2))
        r1 = r0 + 1
        c0 = int(np.clip(math.floor(lon_frac), 0, n_cols - 2))
        c1 = c0 + 1
        
        dr = lat_frac - r0
        dc = lon_frac - c0
        
        # 4 corners
        v00 = values_grid[r0, c0]
        v01 = values_grid[r0, c1]
        v10 = values_grid[r1, c0]
        v11 = values_grid[r1, c1]
        
        val = (1 - dr) * (1 - dc) * v00 + (1 - dr) * dc * v01 + dr * (1 - dc) * v10 + dr * dc * v11
        return float(val)


# Pre-instantiate standard managers
d03_grid_manager = SpatialGridManager(settings.NESTED_DOMAINS[2])
d01_grid_manager = SpatialGridManager(settings.NESTED_DOMAINS[0])
