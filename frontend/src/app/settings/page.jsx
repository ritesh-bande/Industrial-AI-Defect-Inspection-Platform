"use client";

import { useEffect, useState } from "react";
import { Settings, Sliders, Database, Camera, Save, RefreshCw } from "lucide-react";
import AppShell from "../../components/AppShell";
import { apiGet, apiPatch } from "../../services/api";

export default function SettingsPage() {
  const [modelSettings, setModelSettings] = useState({
    padim_score_threshold: 0.45,
    baseline_threshold: 120.0,
    review_severity_threshold: 35.0,
    fail_severity_threshold: 65.0
  });
  
  const [dbStatus, setDbStatus] = useState({
    postgres: "Checking...",
    mongo: "Checking..."
  });
  
  const [activeModel, setActiveModel] = useState("yolo");
  const [cameraConfig, setCameraConfig] = useState({
    deviceId: "0",
    resolution: "1920x1080",
    fps: "30"
  });
  
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Fetch settings on mount
    apiGet("/model/settings")
      .then(setModelSettings)
      .catch(() => {});
      
    // Fetch database check
    apiGet("/health", { token: null })
      .then(res => {
        setDbStatus({
          postgres: "Connected",
          mongo: res.artifacts.yolo_library ? "Connected" : "Mock (File Fallback)"
        });
      })
      .catch(() => {
        setDbStatus({
          postgres: "Disconnected",
          mongo: "Disconnected"
        });
      });
  }, []);

  async function handleSaveSettings() {
    setLoading(true);
    setMessage("");
    try {
      // Save settings
      await apiPatch("/model/settings", modelSettings);
      
      // Save active model selection locally or in local state
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

  return (
    <AppShell title="System Settings" subtitle="Configure AI models, industrial cameras, database connections, and logging.">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
        
        {/* AI & Model Tuning */}
        <section className="tool-panel bg-white border border-gray-200 rounded-lg shadow-sm p-6">
          <div className="panel-heading mb-4 flex items-center gap-3 border-b pb-4">
            <Sliders size={22} className="text-blue-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-800">AI Model & Calibration</h2>
              <p className="text-sm text-gray-500">Tune score thresholds and active models.</p>
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Active AI Model</label>
              <select 
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                value={activeModel}
                onChange={e => setActiveModel(e.target.value)}
              >
                <option value="yolo">YOLOv8 Object Detection (Recommended)</option>
                <option value="cnn">Custom PyTorch CNN & Segmentation</option>
              </select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">PaDiM Anomaly Threshold</label>
                <input 
                  type="number" 
                  step="0.05"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={modelSettings.padim_score_threshold}
                  onChange={e => updateModelSetting("padim_score_threshold", e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">OpenCV Canny Edge Threshold</label>
                <input 
                  type="number" 
                  step="5"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={modelSettings.baseline_threshold}
                  onChange={e => updateModelSetting("baseline_threshold", e.target.value)}
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Review Severity Score</label>
                <input 
                  type="number" 
                  step="1"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={modelSettings.review_severity_threshold}
                  onChange={e => updateModelSetting("review_severity_threshold", e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fail Severity Score</label>
                <input 
                  type="number" 
                  step="1"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={modelSettings.fail_severity_threshold}
                  onChange={e => updateModelSetting("fail_severity_threshold", e.target.value)}
                />
              </div>
            </div>
          </div>
        </section>

        {/* Database Status */}
        <section className="tool-panel bg-white border border-gray-200 rounded-lg shadow-sm p-6">
          <div className="panel-heading mb-4 flex items-center gap-3 border-b pb-4">
            <Database size={22} className="text-blue-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-800">Database Node Status</h2>
              <p className="text-sm text-gray-500">View PostgreSQL and MongoDB node connectivity.</p>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 border rounded-md">
              <span className="text-sm font-medium text-gray-700">PostgreSQL (Primary Relational Node)</span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                dbStatus.postgres === "Connected" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
              }`}>
                {dbStatus.postgres}
              </span>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 border rounded-md">
              <span className="text-sm font-medium text-gray-700">MongoDB (Unstructured Annotations Node)</span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                dbStatus.mongo.includes("Connected") ? "bg-green-100 text-green-800" : "bg-amber-100 text-amber-800"
              }`}>
                {dbStatus.mongo}
              </span>
            </div>
          </div>
        </section>

        {/* Camera Simulation Config */}
        <section className="tool-panel bg-white border border-gray-200 rounded-lg shadow-sm p-6">
          <div className="panel-heading mb-4 flex items-center gap-3 border-b pb-4">
            <Camera size={22} className="text-blue-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-800">Industrial Camera Integration</h2>
              <p className="text-sm text-gray-500">Configure parameters of capturing lens.</p>
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Camera Device Index</label>
              <input 
                type="text" 
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                value={cameraConfig.deviceId}
                onChange={e => setCameraConfig(prev => ({ ...prev, deviceId: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Capture Resolution</label>
                <select 
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={cameraConfig.resolution}
                  onChange={e => setCameraConfig(prev => ({ ...prev, resolution: e.target.value }))}
                >
                  <option value="1920x1080">1920 x 1080 (FHD)</option>
                  <option value="1280x720">1280 x 720 (HD)</option>
                  <option value="640x480">640 x 480 (VGA)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">FPS Target</label>
                <input 
                  type="number"
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  value={cameraConfig.fps}
                  onChange={e => setCameraConfig(prev => ({ ...prev, fps: e.target.value }))}
                />
              </div>
            </div>
          </div>
        </section>

      </div>
      
      {/* Save Button */}
      <div className="mt-6 flex items-center gap-4">
        <button 
          onClick={handleSaveSettings}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition duration-200"
          disabled={loading}
        >
          <Save size={16} />
          {loading ? "Saving Settings..." : "Save Configuration"}
        </button>
        {message && (
          <span className={`text-sm ${message.includes("successfully") ? "text-green-600" : "text-red-600"}`}>
            {message}
          </span>
        )}
      </div>
    </AppShell>
  );
}
