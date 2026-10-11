export type ProvenanceType = 'MODELLED' | 'COUNTERFACTUAL' | 'OBSERVED' | 'INFERRED' | 'SCENARIO';

export interface SystemHealth {
  status: string;
  system_name: string;
  version: string;
  dmdc_model: {
    status: string;
    rank: number;
    raw_spectral_radius: number;
    stabilized_spectral_radius: number;
    state_dimension: number;
    control_dimension: number;
  };
  attribution_engine: string;
  mpc_engine: string;
  uncertainty_engine: string;
  spatial_grid_records: number;
  operating_mode: string;
  scientific_disclaimer: string;
}

export interface CurrentState {
  timestamp: string;
  location: string;
  coordinates: { latitude: number; longitude: number };
  aqi: number;
  category: string;
  aqi_category?: string;
  dominant_pollutant: string;
  pm25: number;
  pm10: number;
  o3: number;
  no2: number;
  so2: number;
  co: number;
  boundary_layer_height: number;
  temperature_2m_k: number;
  temperature_2m_c: number;
  relative_humidity: number;
  surface_pressure: number;
  wind_speed_10m: number;
  u_wind_10m: number;
  v_wind_10m: number;
  inversion_strength: number;
  cams_aerosol: number;
  stability_index: string;
  data_status: string;
  provenance: ProvenanceType;
}

export interface ForecastHour {
  hour: number;
  horizon_label: string;
  pm25: number;
  pm25_lower: number;
  pm25_upper: number;
  pm10: number;
  pm10_lower?: number;
  pm10_upper?: number;
  o3: number;
  o3_lower?: number;
  o3_upper?: number;
  no2: number;
  no2_lower?: number;
  no2_upper?: number;
  boundary_layer_height: number;
  inversion_strength: number;
  wind_speed_10m: number;
  aqi: number;
  aqi_lower?: number;
  aqi_upper?: number;
  category: string;
  dominant_pollutant: string;
}

export interface ForecastData {
  horizon_hours: number;
  rollout_latency_ms: number;
  scientific_disclaimer: string;
  uncertainty_label: string;
  hourly_timeline: ForecastHour[];
  provenance: ProvenanceType;
}

export interface GridCell {
  lat: number;
  lon: number;
  val?: number;
  value?: number;
  grid_id?: string;
  u_wind?: number;
  v_wind?: number;
}

export interface SpatialGridData {
  variable: string;
  time_step: number;
  total_cells_in_slice: number;
  domain_bounds: {
    lat_min: number;
    lat_max: number;
    lon_min: number;
    lon_max: number;
  };
  cells: GridCell[];
  provenance: ProvenanceType;
}

export interface SectorShare {
  sector: string;
  displayName?: string;
  share_percent: number;
  pm25_equivalent_ugm3?: number;
  pm25_reduction_ugm3?: number;
  zero_out_reduction_ugm3?: number;
  provenance?: ProvenanceType;
}

export interface AttributionData {
  provenance_notice: string;
  source_breakdown: {
    local_urban_percent: number;
    regional_crop_fires_percent: number;
    transboundary_background_percent: number;
  };
  sector_contributions: SectorShare[];
}

export interface PlumeEstimate {
  cluster_id: string;
  centroid_lat: number;
  centroid_lon: number;
  fire_count: number;
  total_frp_mw: number;
  distance_to_delhi_km: number;
  bearing_deg: number;
  aligned_with_wind: boolean;
  transit_speed_kmh: number;
  estimated_arrival_hours: number;
  urgency: string;
  confidence: string | number;
  provenance: ProvenanceType;
  cluster_center_lat?: number;
  cluster_center_lon?: number;
  total_frp?: number;
  distance_km?: number;
  estimated_transit_hours?: number;
  estimated_arrival_timestamp?: string;
  transport_potential_score?: number;
  is_upwind?: boolean;
}

export interface PlumeData {
  active_fire_clusters_count: number;
  target_airshed: string;
  plume_estimates: PlumeEstimate[];
  plume_clock_status: string;
  scientific_disclaimer: string;
  provenance: ProvenanceType;
}

export interface DriverScore {
  driver: string;
  driver_name: string;
  score: number;
  description: string;
}

export interface WhyAQIRisesData {
  timestamp: string;
  horizon_hours: number;
  initial_aqi: number;
  predicted_aqi: number;
  delta_aqi: number;
  dominant_driver: string;
  driver_scores: DriverScore[];
  drivers?: any[];
  spectral_mode_association: string | any[];
  narrative_summary: string;
  provenance: ProvenanceType;
}

export interface InfeasibilityCertificate {
  certificate_id: string;
  status: string;
  title: string;
  authority: string;
  governing_law: string;
  transboundary_advection_pm25: number;
  zero_local_emission_floor_pm25: number;
  zero_local_emission_floor_aqi: number;
  demanded_target_aqi: number;
  mathematical_proof: string;
  minimum_achievable_aqi: number;
  legal_classification: string;
}

export interface ActionWindowData {
  status: string;
  title: string;
  hours_to_inversion_lid: number;
  countdown_formatted: string;
  current_pbl_height_m: number;
  nocturnal_pbl_threshold_m: number;
  projected_nocturnal_pbl_m: number;
  dispersion_efficiency_multiplier: number;
  action_recommendation: string;
  golden_hour_deadline: string;
  physics_basis: string;
  provenance: ProvenanceType;
}

export interface AirshedFederalismData {
  title: string;
  framework: string;
  arbitrage_multiplier: number;
  headline: string;
  policies_compared: {
    intra_delhi_truck_ban: {
      name: string;
      state: string;
      economic_disruption_cr_per_day: number;
      pm25_reduction_ugm3: number;
      cost_efficiency_cr_per_ug: number;
      societal_impact: string;
    };
    punjab_stubble_subsidy: {
      name: string;
      state: string;
      economic_disruption_cr_per_day: number;
      pm25_reduction_ugm3: number;
      cost_efficiency_cr_per_ug: number;
      societal_impact: string;
    };
  };
  cooperative_compact: {
    mechanism: string;
    daily_fiscal_transfer_cr: number;
    net_delhi_economic_savings_cr_per_day: number;
    net_delhi_air_quality_gain_pct: string;
    game_theory_resolution: string;
  };
  provenance: string;
}

export interface CAQMDirectiveData {
  directive_number: string;
  title: string;
  issuing_authority: string;
  statutory_mandate: string;
  generated_at: string;
  cryptographic_hash: string;
  baseline_telemetry: {
    monitoring_network: string;
    central_delhi_aqi: number;
    category: string;
    dominant_pollutant: string;
    air_receptors_analyzed: number;
    data_provenance: string;
  };
  meteorological_inversion_finding: {
    status: string;
    capping_lid_strength: string;
    nocturnal_pbl_collapse_m: string;
    koopman_dynamical_mode: string;
    golden_action_window_deadline: string;
  };
  counterfactual_source_attribution: {
    local_transport_vehicular: string;
    construction_and_road_dust: string;
    regional_agricultural_stubble: string;
    industrial_point_sources: string;
  };
  mandated_curtailment_schedule: Array<{
    sector: string;
    mandated_curtailment: string;
    compliance_deadline: string;
    legal_basis: string;
  }>;
  legal_enforceability: string;
  signatory: string;
}

export interface MPCStrategyResult {
  feasible: boolean;
  feasibility_status?: string;
  infeasibility_reason?: string | null;
  infeasibility_certificate?: InfeasibilityCertificate | null;
  target_aqi_requested?: number;
  target_aqi_achieved?: number;
  final_predicted_aqi?: number;
  final_predicted_pm25?: number;
  curtailment_percent: Record<string, number>;
  optimal_curtailments?: Record<string, number>;
  expected_pm25_reduction_ugm3: number;
  cost_index: number;
  trajectory_comparison: {
    hour: number;
    baseline_pm25: number;
    controlled_pm25: number;
    averted_pm25: number;
  }[];
  scientific_disclaimer: string;
  provenance: ProvenanceType;
}

export interface DemoStep {
  step: number;
  title: string;
  target_section: string;
  narrative: string;
}

export interface ActivityEvent {
  timestamp: string;
  service: string;
  message: string;
  latency_ms: number;
}

export interface BackendActivity {
  pipeline_status: {
    data_ingestion: string;
    wrfchem_state: string;
    dmdc_forecast: string;
    attribution: string;
    mpc_engine: string;
  };
  last_updated: string;
  events: ActivityEvent[];
  operating_mode: string;
  system_status: string;
}

export interface WardInfo {
  id: string;
  name: string;
  district: string;
  lat: number;
  lon: number;
  base_aqi: number;
  sensitivity: string;
  schools_count: number;
  hospitals_count: number;
  vulnerable_population: string;
  dominant_source: string;
  risk_summary: string;
}

export interface HealthAdvisory {
  vulnerable_groups: string;
  outdoor_jogging: string;
  schools_status: string;
  air_purifiers: string;
}

export interface ActiveGeoAlert {
  alert_id: string;
  ward_id: string;
  ward_name: string;
  district: string;
  coordinates: { lat: number; lon: number };
  current_aqi: number;
  projected_peak_aqi: number;
  projected_peak_time: string;
  severity: 'MODERATE' | 'POOR' | 'VERY_POOR' | 'SEVERE' | 'EMERGENCY';
  dominant_pollutant: string;
  primary_driver: string;
  action_window_hours_left: number;
  health_advisory: HealthAdvisory;
  school_protocol: {
    status: string;
    recommendation: string;
  };
  hospital_protocol: {
    status: string;
    recommendation: string;
  };
}

export interface BroadcastHistoryItem {
  id: string;
  timestamp: string;
  ward_id: string;
  ward_name: string;
  severity: string;
  category: string;
  headline: string;
  message: string;
  target_audiences: string[];
  channels: string[];
  recipients_reached: number;
  status: string;
}

export interface ActiveAlertsResponse {
  timestamp: string;
  active_alerts_count: number;
  emergency_broadcast_active: boolean;
  headline: string;
  global_recommendation: string;
  subscribers_count: number;
  total_broadcasts_today: number;
  alerts: ActiveGeoAlert[];
  recent_broadcasts: BroadcastHistoryItem[];
}

export interface SchoolGuideline {
  aqi_tier: string;
  outdoor_assemblies: string;
  sports_recess: string;
  mask_protocol: string;
  indoor_action: string;
}

export interface SchoolSafetyProtocolResponse {
  title: string;
  statutory_reference: string;
  effective_date: string;
  peak_risk_window: string;
  school_guidelines: SchoolGuideline[];
  total_schools_covered_ncr: number;
  automated_notification_status: string;
}

export interface AWSServiceHealth {
  name: string;
  category: string;
  status: string;
  tier: string;
  metrics: Record<string, string>;
}

export interface AWSInfrastructureResponse {
  cloud_provider: string;
  compliance_mode: string;
  region: string;
  last_audited: string;
  services: AWSServiceHealth[];
}

export interface CitizenSubscriptionPayload {
  name: string;
  phone?: string;
  email?: string;
  ward_id: string;
  role: string;
  channels: string[];
}

export interface AlertBroadcastPayload {
  ward_id: string;
  severity: string;
  category: string;
  title: string;
  message: string;
  target_audiences: string[];
  channels: string[];
}

export type NavigationPage = 
  | 'overview'
  | 'alerts'
  | 'monitoring'
  | 'forecast'
  | 'atmosphere'
  | 'sources'
  | 'intervention'
  | 'aws'
  | 'model';


