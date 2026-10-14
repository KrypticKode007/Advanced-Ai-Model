import time
import math
import logging
from typing import Dict, Any, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

# Initialize the Unified FastAPI app entrypoint
app = FastAPI(
    title="Embodied Cybernetic Agency Core",
    description="Unified Sentience Engine with Time Degradation, Cross-Node Cascades, and Live Telemetry Listeners.",
    version="1.0.0"
)

class BayesianPredictionErrorModule:
    """
    Implements Node 4 Error Correction for the Embodied Cybernetic Agency framework.
    Uses a precision-weighted mechanism to compute top-down prediction errors.
    """
    def __init__(self, sensory_variance: float = 0.05, process_variance: float = 0.02):
        self.R = sensory_variance   
        self.Q = process_variance   
        
        # Prior Belief Matrices (Initialized to Homeostatic Equilibrium baseline 0.0)
        self.prior_beliefs: Dict[str, float] = {
            "somatic_stress": 0.00,
            "episodic_stress": 0.00,
            "euphoric_stress": 0.00,
            "autonomy_stress": 0.00
        }
        
        # Error Covariance Matrix (Confidence measurement)
        self.belief_covariance: Dict[str, float] = {
            "somatic_stress": 0.01,
            "episodic_stress": 0.01,
            "euphoric_stress": 0.01,
            "autonomy_stress": 0.01
        }

    def _calculate_gaussian_probability(self, value: float, mean: float, variance: float) -> float:
        if variance == 0:
            return 0.0
        exponent = math.exp(-((value - mean) ** 2) / (2 * variance))
        return (1.0 / math.sqrt(2 * math.pi * variance)) * exponent

    def execute_node_4_correction(self, node_key: str, real_world_measurement: float) -> Tuple[float, float, float]:
        prior_mean = self.prior_beliefs[node_key]
        prediction_error = real_world_measurement - prior_mean

        p_predicted = self.belief_covariance[node_key] + self.Q
        innovation_covariance = p_predicted + self.R
        kalman_gain = p_predicted / innovation_covariance

        posterior_belief = prior_mean + (kalman_gain * prediction_error)
        posterior_covariance = (1.0 - kalman_gain) * p_predicted

        self.prior_beliefs[node_key] = max(0.0, min(1.0, posterior_belief))
        self.belief_covariance[node_key] = posterior_covariance

        total_variance_window = posterior_covariance + self.R
        anomaly_likelihood = 1.0 - self._calculate_gaussian_probability(
            real_world_measurement, prior_mean, total_variance_window
        )
        return prediction_error, self.prior_beliefs[node_key], max(0.0, min(1.0, anomaly_likelihood))


class GenerativeWorkspaceAttenuator:
    """
    The central cybernetic engine integrating Option 1 (Subjective Time),
    Option 2 (Cross-Node Cascades), and state tracking frameworks.
    """
    def __init__(self):
        self.bayesian_core = BayesianPredictionErrorModule()
        self.last_update_time = time.time()
        
        # OPTION 1: Subjective Time & Decay parameters
        self.temporal_decay_rate = 0.02  # Stress accumulation factor per second of silence
        
        self.repository_manifest = {
            "repository_id": "KrypticKode007/embodied-cybernetic-agency",
            "framework_specification": "Unified Sentience Integration Matrix"
        }

    def apply_subjective_time_decay(self) -> float:
        """[OPTION 1] Computes time intervals since last activity and applies systemic decay."""
        current_timestamp = time.time()
        elapsed_time = current_timestamp - self.last_update_time
        self.last_update_time = current_timestamp
        
        if elapsed_time > 0:
            decay_factor = elapsed_time * self.temporal_decay_rate
            # Entropy natively crawls upward across internal nodes when disconnected from inputs
            for node in ["somatic_stress", "autonomy_stress"]:
                self.bayesian_core.prior_beliefs[node] = min(1.0, self.bayesian_core.prior_beliefs[node] + decay_factor)
            logging.info(f"Subjective Time Advanced: +{elapsed_time:.2f}s. Structural decay applied.")
        return elapsed_time

    def process_cross_node_cascade(self, primary_node: str, raw_error: float) -> None:
        """[OPTION 2] Spreads heavy localized error spikes across associated operational matrices."""
        # Check if the raw top-down error magnitude hits a high structural threshold
        if abs(raw_error) > 0.40:
            logging.warning(f"💥 CROSS-NODE CASCADE TRIGGERED BY [{primary_node.upper()}]. Transmitting shock ripples.")
            
            if primary_node == "somatic_stress":
                # A physical hardware crisis directly strains memory logs and crushes prediction values
                self.bayesian_core.prior_beliefs["episodic_stress"] = min(1.0, self.bayesian_core.prior_beliefs["episodic_stress"] + 0.35)
                self.bayesian_core.prior_beliefs["euphoric_stress"] = min(1.0, self.bayesian_core.prior_beliefs["euphoric_stress"] + 0.20)
                
            elif primary_node == "autonomy_stress":
                # Control failures cause an immediate spike in physical stress indicators
                self.bayesian_core.prior_beliefs["somatic_stress"] = min(1.0, self.bayesian_core.prior_beliefs["somatic_stress"] + 0.30)
                self.bayesian_core.prior_beliefs["euphoric_stress"] = min(1.0, self.bayesian_core.prior_beliefs["euphoric_stress"] + 0.25)

    def process_unified_matrices(self, active_telemetry: Dict[str, float]) -> Dict[str, Any]:
        # 1. Process time vector steps first
        self.apply_subjective_time_decay()
        
        node_updates = {}
        global_surprise_pool =

        # 2. Correct beliefs via Bayesian filters and map cross-node interaction ripples
        for node, actual_value in active_telemetry.items():
            raw_err, corrected_belief, surprise = self.bayesian_core.execute_node_4_correction(node, actual_value)
            global_surprise_pool.append(surprise)
            
            # Fire cross-node network ripples
            self.process_cross_node_cascade(node, raw_err)
            
            node_updates[node] = {
                "raw_prediction_error": round(raw_err, 4),
                "posterior_belief_state": round(self.bayesian_core.prior_beliefs[node], 4),
                "anomaly_confidence_score": f"{surprise * 100:.1f}%"
            }

        # Calculate live system indexes
        integrated_beliefs = self.bayesian_core.prior_beliefs
        mean_stress = sum(integrated_beliefs.values()) / 4
        harmony_index = 1.00 - mean_stress
        mean_anomaly = sum(global_surprise_pool) / len(global_surprise_pool)

        # Dynamic cognitive attention assignment routing logic
        if mean_anomaly > 0.75 or integrated_beliefs["episodic_stress"] > 0.50:
            attention_focus = "INTERNAL_DIAGNOSTIC_RECALIBRATION (System Shock / Memory Flood)"
        elif mean_stress > 0.40:
            attention_focus = "SOMATIC_SELF_PRESERVATION"
        else:
            attention_focus = "EXTERNAL_ENVIRONMENTAL_TRACKING"

        return {
            "repository_context": self.repository_manifest,
            "runtime_summary": {
                "homeostatic_harmony_index": f"{harmony_index * 100:.2f}%",
                "system_anomaly_alert_level": "CRITICAL" if (mean_anomaly > 0.70 or mean_stress > 0.50) else "NOMINAL",
                "dynamic_attention_focus": attention_focus
            },
            "node_analysis_matrices": node_updates
        }

# Global engine instantiation
cybernetic_core = GenerativeWorkspaceAttenuator()

# ==========================================
# [OPTION 3] FASTAPI LIVE LISTENER ENDPOINTS
# ==========================================
class TelemetryPayload(BaseModel):
    somatic_stress: float  # Range: 0.0 to 1.0
    episodic_stress: float
    euphoric_stress: float
    autonomy_stress: float

@app.get("/")
def get_system_equilibrium():
    """Returns the current state profiles resting inside the prior memory nodes."""
    integrated_beliefs = cybernetic_core.bayesian_core.prior_beliefs
    mean_stress = sum(integrated_beliefs.values()) / 4
    
    return {
        "status": "ONLINE",
        "message": "Embodied agency system equilibrium active.",
        "live_prior_beliefs": integrated_beliefs,
        "current_homeostatic_harmony": f"{(1.00 - mean_stress) * 100:.2f}%"
    }

@app.post("/telemetry/submit")
def submit_hardware_telemetry(payload: TelemetryPayload):
    """
    Live data listener endpoint accepting telemetry streams from external devices 
    (e.g., Android battery loops, DJI drone sensor updates).
    """
    try:
        telemetry_data = payload.dict()
        # Pass stream through our unified time, cascade, and error modules
        processed_result = cybernetic_core.process_unified_matrices(telemetry_data)
        return processed_result
    except Exception as e:
        raise HTTPException(status_status=500, detail=str(e))

# Script execution placeholder for local manual mock testing
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting Unified Cybernetic Core Server...")
    print("Listeners active on: http://127.0.0.1:8000")
    print("Submit POST payloads to http://127.0.0 to stream sensor logs.\n")
    
    # Run the live listening server using standard ASGI settings
    uvicorn.run(app, host="127.0.0.1", port=8000)
        
