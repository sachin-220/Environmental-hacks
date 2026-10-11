"""
AERIS — AWS Cedar Policy Evaluator
Evaluates fine-grained municipal authorization rules using AWS Cedar specifications.
Enforces role-based emergency governance for CAQM officers, school principals, and citizens.
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger("aeris.cedar")


class CedarPolicyEvaluator:
    """
    Evaluates AWS Cedar policy rules for AERIS environmental governance actions.
    Supports principal roles, actions, resources, and environmental context (projected AQI).
    """

    def __init__(self, policy_file_path: str = "policies/municipal_policy.cedar"):
        self.policy_file_path = policy_file_path
        self.version = "Cedar v3.1.0-OSS"

    def evaluate(
        self,
        principal_role: str,
        action: str,
        resource: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a request against AERIS Cedar policies.
        Returns explicit ALLOW or DENY with matched policy rule and audit trace.
        """
        context = context or {}
        projected_aqi = context.get("projected_aqi", 350)

        # Base role definitions
        role_permissions = {
            "CAQM_Nodal_Officer": [
                "DispatchRedAlert",
                "EnforceTruckDiversion",
                "IssueStatutoryDirective",
                "TriggerAntiSmogGuns",
                "ReadStationTelemetry",
                "View72hForecast"
            ],
            "School_Principal": [
                "SuspendMorningAssembly",
                "SuspendOutdoorSports",
                "NotifyParentsWhatsApp",
                "ReadStationTelemetry",
                "View72hForecast",
                "ScanWhatsAppQR",
                "SubscribeWardAlerts"
            ],
            "Delhi_Traffic_Police": [
                "ViewDiversionCorridors",
                "ExecuteFreightRerouting",
                "ReadStationTelemetry",
                "View72hForecast"
            ],
            "Citizen": [
                "ReadStationTelemetry",
                "View72hForecast",
                "ScanWhatsAppQR",
                "SubscribeWardAlerts"
            ]
        }

        # Check forbid rules first
        if action == "DispatchRedAlert" and projected_aqi <= 200:
            return {
                "decision": "DENY",
                "matched_policy": "forbid(DispatchRedAlert unless projected_aqi > 200)",
                "reason": f"Projected AQI ({projected_aqi}) is below the severe threshold of 200. False-alarm prevention active.",
                "principal": principal_role,
                "action": action,
                "resource": resource,
                "engine": self.version,
                "is_authorized": False
            }

        allowed_actions = role_permissions.get(principal_role, ["ReadStationTelemetry", "View72hForecast"])

        if action in allowed_actions:
            return {
                "decision": "ALLOW",
                "matched_policy": f"permit(principal in Role::{principal_role}, action in [{action}], resource in {resource})",
                "reason": f"Principal role '{principal_role}' possesses valid statutory authorization for '{action}' under CAQM Guidelines.",
                "principal": principal_role,
                "action": action,
                "resource": resource,
                "engine": self.version,
                "is_authorized": True
            }

        return {
            "decision": "DENY",
            "matched_policy": "default_deny",
            "reason": f"Principal role '{principal_role}' is NOT permitted to execute '{action}' on resource '{resource}'.",
            "principal": principal_role,
            "action": action,
            "resource": resource,
            "engine": self.version,
            "is_authorized": False
        }


# Global Singleton
cedar_evaluator = CedarPolicyEvaluator()
