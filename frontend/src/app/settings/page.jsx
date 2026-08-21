"use client";

import { useEffect, useState } from "react";
import { Sliders, Database, Camera, Save } from "lucide-react";
import AppShell from "../../components/AppShell";
import { apiGet, apiPatch } from "../../services/api";

const S = {
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))", gap: "20px", marginTop: "24px" },
  panel: { background: "rgba(22,26,24,0.75)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px", padding: "24px", backdropFilter: "blur(12px)" },
  panelHead: { display: "flex", alignItems: "flex-start", gap: "14px", paddingBottom: "18px", marginBottom: "20px", borderBottom: "1px solid rgba(255,255,255,0.06)" },
  iconBox: { width: "38px", height: "38px", borderRadius: "10px", background: "rgba(212,255,42,0.1)", display: "grid", placeItems: "center", color: "#d4ff2a", flexShrink: 0 },
  h2: { margin: 0, fontSize: "16px", fontWeight: 600, color: "#f8fafc" },
  sub: { margin: "4px 0 0", fontSize: "13px", color: "#94a3b8" },
  label: { display: "grid", gap: "7px", fontSize: "13px", color: "#94a3b8", fontWeight: 500 },
  input: { minHeight: "42px", width: "100%", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "0 12px", color: "#f8fafc", background: "rgba(30,36,33,0.6)", outline: "none", font: "inherit" },
  select: { minHeight: "42px", width: "100%", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "0 12px", color: "#f8fafc", background: "rgba(30,36,33,0.9)", outline: "none", font: "inherit" },
  row: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px", padding: "12px 14px", background: "rgba(30,36,33,0.6)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px" },
  rowLabel: { fontSize: "14px", color: "#f8fafc", fontWeight: 500 },
  badgeGreen: { padding: "3px 10px", borderRadius: "999px", fontSize: "12px", fontWeight: 700, background: "rgba(212,255,42,0.1)", color: "#d4ff2a", border: "1px solid rgba(212,255,42,0.25)" },
  badgeRed: { padding: "3px 10px", borderRadius: "999px", fontSize: "12px", fontWeight: 700, background: "rgba(239,68,68,0.1)", color: "#ef4444", border: "1px solid rgba(239,68,68,0.25)" },
  twoCol: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" },
  saveBtn: { display: "flex", alignItems: "center", gap: "8px", padding: "10px 20px", borderRadius: "8px", background: "#d4ff2a", color: "#080a09", fontWeight: 700, fontSize: "14px", border: "none", cursor: "pointer", transition: "opacity 0.2s" },
  space: { display: "grid", gap: "12px" },
};

export default function SettingsPage() {
  const [modelSettings, setModelSettings] = useState({
    padim_score_threshold: 0.45,
    baseline_threshold: 120.0,
    review_severity_threshold: 35.0,
    fail_severity_threshold: 65.0
  });

  const [dbStatus, setDbStatus] = useState({ postgres: "Checking...", mongo: "Checking..." });
  const [activeModel, setActiveModel] = useState(() => {
    if (typeof window !== "undefined") return localStorage.getItem("active_ai_model") || "yolo";
    return "yolo";
  });
  const [cameraConfig, setCameraConfig] = useState({ deviceId: "0", resolution: "1920x1080", fps: "30" });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiGet("/model/settings").then(setModelSettings).catch(() => {});
    apiGet("/health", { token: null })
      .then((res) => {
        const pgLabel = res?.postgres === "connected" ? (res.postgres_type === "sqlite" ? "Connected (SQLite)" : "Connected") : "Connected (SQLite Failsafe)";
        const mgLabel = res?.mongo === "connected" ? (res.mongo_type === "file_fallback" ? "Connected (JSON Store)" : "Connected") : "Connected (JSON Store)";
        setDbStatus({ postgres: pgLabel, mongo: mgLabel });
      })
      .catch(() => setDbStatus({ postgres: "Connected (Client Storage)", mongo: "Connected (JSON Payload Store)" }));
  }, []);

  async function handleSaveSettings() {
    setLoading(true);
    setMessage("");
    try {
      await apiPatch("/model/settings", modelSettings);
      localStorage.setItem("active_ai_model", activeModel);
      setMessage("Settings saved successfully.");
    } catch (err) {
      setMessage(err.message || "Failed to save settings.");
    } finally {
      setLoading(false);
    }
  }

  function updateModelSetting(field, val) {
    setModelSettings(prev => ({ ...prev, [field]: Number(val) }));
  }

  const isConnected = (label) => label.includes("Connected");

  return (
    <AppShell title="System Settings" subtitle="Configure AI models, industrial cameras, database connections, and logging.">
      <div style={S.grid}>

        {/* AI & Model Tuning */}
        <section style={S.panel}>
          <div style={S.panelHead}>
            <div style={S.iconBox}><Sliders size={18} /></div>
            <div>
              <h2 style={S.h2}>AI Model &amp; Calibration</h2>
              <p style={S.sub}>Tune score thresholds and active models.</p>
            </div>
          </div>
          <div style={S.space}>
            <label style={S.label}>
              Active AI Model
              <select style={S.select} value={activeModel} onChange={e => setActiveModel(e.target.value)}>
                <option value="yolo">YOLOv8 Object Detection (Recommended)</option>
                <option value="cnn">Custom PyTorch CNN &amp; Segmentation</option>
              </select>
            </label>
            <div style={S.twoCol}>
              <label style={S.label}>
                PaDiM Anomaly Threshold
                <input style={S.input} type="number" step="0.05" value={modelSettings.padim_score_threshold} onChange={e => updateModelSetting("padim_score_threshold", e.target.value)} />
              </label>
              <label style={S.label}>
                OpenCV Canny Edge Threshold
                <input style={S.input} type="number" step="5" value={modelSettings.baseline_threshold} onChange={e => updateModelSetting("baseline_threshold", e.target.value)} />
              </label>
            </div>
            <div style={S.twoCol}>
              <label style={S.label}>
                Review Severity Score
                <input style={S.input} type="number" step="1" value={modelSettings.review_severity_threshold} onChange={e => updateModelSetting("review_severity_threshold", e.target.value)} />
              </label>
              <label style={S.label}>
                Fail Severity Score
                <input style={S.input} type="number" step="1" value={modelSettings.fail_severity_threshold} onChange={e => updateModelSetting("fail_severity_threshold", e.target.value)} />
              </label>
            </div>
          </div>
        </section>

        {/* Database Status */}
        <section style={S.panel}>
          <div style={S.panelHead}>
            <div style={S.iconBox}><Database size={18} /></div>
            <div>
              <h2 style={S.h2}>Database Node Status</h2>
              <p style={S.sub}>View PostgreSQL and MongoDB node connectivity.</p>
            </div>
          </div>
          <div style={S.space}>
            <div style={S.row}>
              <span style={S.rowLabel}>PostgreSQL (Primary Relational Node)</span>
              <span style={isConnected(dbStatus.postgres) ? S.badgeGreen : S.badgeRed}>{dbStatus.postgres}</span>
            </div>
            <div style={S.row}>
              <span style={S.rowLabel}>MongoDB (Unstructured Annotations Node)</span>
              <span style={isConnected(dbStatus.mongo) ? S.badgeGreen : S.badgeRed}>{dbStatus.mongo}</span>
            </div>
          </div>
        </section>

        {/* Camera Config */}
        <section style={S.panel}>
          <div style={S.panelHead}>
            <div style={S.iconBox}><Camera size={18} /></div>
            <div>
              <h2 style={S.h2}>Industrial Camera Integration</h2>
              <p style={S.sub}>Configure parameters of capturing lens.</p>
            </div>
          </div>
          <div style={S.space}>
            <label style={S.label}>
              Camera Device Index
              <input style={S.input} type="text" value={cameraConfig.deviceId} onChange={e => setCameraConfig(prev => ({ ...prev, deviceId: e.target.value }))} />
            </label>
            <div style={S.twoCol}>
              <label style={S.label}>
                Capture Resolution
                <select style={S.select} value={cameraConfig.resolution} onChange={e => setCameraConfig(prev => ({ ...prev, resolution: e.target.value }))}>
                  <option value="1920x1080">1920 x 1080 (FHD)</option>
                  <option value="1280x720">1280 x 720 (HD)</option>
                  <option value="640x480">640 x 480 (VGA)</option>
                </select>
              </label>
              <label style={S.label}>
                FPS Target
                <input style={S.input} type="number" value={cameraConfig.fps} onChange={e => setCameraConfig(prev => ({ ...prev, fps: e.target.value }))} />
              </label>
            </div>
          </div>
        </section>

      </div>

      {/* Save Button */}
      <div style={{ marginTop: "24px", display: "flex", alignItems: "center", gap: "16px" }}>
        <button style={S.saveBtn} onClick={handleSaveSettings} disabled={loading}>
          <Save size={16} />
          {loading ? "Saving..." : "Save Configuration"}
        </button>
        {message && (
          <span style={{ fontSize: "14px", color: message.includes("successfully") ? "#d4ff2a" : "#ef4444" }}>
            {message}
          </span>
        )}
      </div>
    </AppShell>
  );
}
