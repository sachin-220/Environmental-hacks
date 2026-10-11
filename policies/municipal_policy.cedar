// ==============================================================================
// AERIS — AWS CEDAR AUTHORIZATION & POLICY SPECIFICATION
// Open-source municipal policy language for emergency environmental governance.
// Evaluates fine-grained permissions for citizen alerts, CAQM directives, and MPC actions.
// ==============================================================================

// Rule 1: CAQM Nodal Officers have full permission to dispatch Red Alerts and enforce truck diversions
permit (
    principal in Role::"CAQM_Nodal_Officer",
    action in [
        Action::"DispatchRedAlert",
        Action::"EnforceTruckDiversion",
        Action::"IssueStatutoryDirective",
        Action::"TriggerAntiSmogGuns"
    ],
    resource in AirshedWard::"Delhi_NCR"
);

// Rule 2: School Administrators can dispatch school-level advisories and suspend outdoor activities
permit (
    principal in Role::"School_Principal",
    action in [
        Action::"SuspendMorningAssembly",
        Action::"SuspendOutdoorSports",
        Action::"NotifyParentsWhatsApp"
    ],
    resource in Institution::"School_Campus"
);

// Rule 3: Municipal Traffic Police can view and execute route diversions
permit (
    principal in Role::"Delhi_Traffic_Police",
    action in [
        Action::"ViewDiversionCorridors",
        Action::"ExecuteFreightRerouting"
    ],
    resource in Corridor::"Outer_Ring_Road"
);

// Rule 4: Citizens and Residents have unconditional read access to live telemetry and forecasts
permit (
    principal,
    action in [
        Action::"ReadStationTelemetry",
        Action::"View72hForecast",
        Action::"ScanWhatsAppQR",
        Action::"SubscribeWardAlerts"
    ],
    resource in PublicData::"AERIS_Airshed"
);

// Rule 5: Forbid high-severity municipal broadcasts if projected AQI is below 200 (Prevent false alarms)
forbid (
    principal,
    action == Action::"DispatchRedAlert",
    resource
)
unless {
    context.projected_aqi > 200
};
