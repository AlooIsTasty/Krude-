/**
 * Krude - API Client
 * Connects frontend dashboard with backend FastAPI server.
 */

const API_BASE = ""; // Relative paths for same-origin serving

const API = {
  async getOverview() {
    const res = await fetch(`${API_BASE}/api/overview`);
    if (!res.ok) throw new Error("Failed to fetch system overview");
    return await res.json();
  },

  async getRiskScores() {
    const res = await fetch(`${API_BASE}/api/risk/scores`);
    if (!res.ok) throw new Error("Failed to fetch corridor risk scores");
    return await res.json();
  },

  async refreshRiskIntel() {
    const res = await fetch(`${API_BASE}/api/risk/refresh`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to refresh risk intelligence");
    return await res.json();
  },

  async simulateScenario(payload) {
    const res = await fetch(`${API_BASE}/api/scenario/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Simulation failed");
    }
    return await res.json();
  },

  async rankProcurement(corridorRiskScores = null) {
    const res = await fetch(`${API_BASE}/api/procurement/rank`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ corridor_risk_scores: corridorRiskScores })
    });
    if (!res.ok) throw new Error("Failed to rank procurement");
    return await res.json();
  },

  async optimizeProcurement(payload) {
    const res = await fetch(`${API_BASE}/api/procurement/optimize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Failed to optimize procurement");
    return await res.json();
  },

  async calculateReserveDrawdown(safetyFloorDays = 3.0, durationDays = 30) {
    const res = await fetch(`${API_BASE}/api/reserve/drawdown`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        safety_floor_days: safetyFloorDays,
        disruption_duration_days: durationDays
      })
    });
    if (!res.ok) throw new Error("Failed to calculate reserve drawdown");
    return await res.json();
  },

  async getDigitalTwinState(payload) {
    const res = await fetch(`${API_BASE}/api/digital-twin/state`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Failed to fetch digital twin state");
    return await res.json();
  },

  async getModelStatus() {
    const res = await fetch(`${API_BASE}/api/model/status`);
    if (!res.ok) throw new Error("Failed to fetch model status");
    return await res.json();
  },

  async analyzeHeadline(headline, corridor = null) {
    const res = await fetch(`${API_BASE}/api/model/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ headline, corridor })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Headline analysis failed");
    }
    return await res.json();
  },

  async setModelBackend(payload) {
    const res = await fetch(`${API_BASE}/api/model/set-backend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to switch model backend");
    }
    return await res.json();
  },

  async exportTrainingDataset() {
    const res = await fetch(`${API_BASE}/api/model/export-dataset`, {
      method: "POST"
    });
    if (!res.ok) throw new Error("Failed to export dataset");
    return await res.json();
  }
};
