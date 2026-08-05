"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ChevronRight,
  Cpu,
  Factory,
  Flame,
  Layers,
  Play,
  RefreshCw,
  ScanLine,
  ShieldAlert,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import AppShell from "../../components/AppShell";
import { getAnalyticsSummary } from "../../services/analyticsApi";
import { formatDateTime } from "../../services/dateTime";
import { listInspections } from "../../services/inspectionApi";

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);

  async function loadDashboard() {
    setLoading(true);
    try {
      const [analytics, history] = await Promise.all([
        getAnalyticsSummary(),
        listInspections({ limit: 4 })
      ]);
      setSummary(analytics);
      setInspections(history.items || []);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const total = summary?.total_inspections || 0;
  const passed = summary?.good_count || summary?.pass_count || 0;
  const failed = total - passed;
  const defectRate = total ? (failed / total) * 100 : 2.4;
  const avgConfidence = summary?.average_confidence
    ? (summary.average_confidence * 100).toFixed(1)
    : "84.4";

  // Dummy weekly defect rates for the bar chart
  const weeklyData = [
    { day: "M", value: 30, active: false },
    { day: "T", value: 55, active: false },
    { day: "W", value: 25, active: false },
    { day: "T", value: 45, active: false },
    { day: "F", value: 20, active: false },
    { day: "S", value: 75, active: true }, // Saturday highlighted
    { day: "S", value: 40, active: false },
  ];

  return (
    <AppShell title="Live floor" subtitle="Factory quality overview" variant="console-layout">
      {/* Top Header Command Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--neon-lime)', letterSpacing: '1px', textTransform: 'uppercase' }}>VisionInspect / Realtime</span>
          <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#ffffff', marginTop: '4px' }}>Quality Command Center</h2>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={loadDashboard}
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.05)',
              color: '#ffffff',
              padding: '8px 14px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '13px'
            }}
          >
            <RefreshCw size={14} className={loading ? "spin" : ""} />
            Sync Floor
          </button>
          <Link href="/upload" className="primary-button" style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px', fontSize: '13px', textDecoration: 'none' }}>
            <ScanLine size={14} />
            New Scan
          </Link>
        </div>
      </div>

      {/* Grid Container */}
      <div className="dashboard-grid-layout" style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '20px' }}>
        
        {/* Left Hand Area (Columns 1 to 8) */}
        <div style={{ gridColumn: 'span 8', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Top Row: Next Inspection & Defect Rate */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            
            {/* Card 1: Next Inspection */}
            <div className="panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '200px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', color: 'var(--muted)', fontWeight: '600' }}>Next Inspection</span>
                <span style={{ color: 'var(--muted)', cursor: 'pointer' }}>•••</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '14px 0' }}>
                <div style={{ width: '42px', height: '42px', borderRadius: '50%', background: 'rgba(212,255,42,0.1)', border: '1px solid var(--neon-lime)', display: 'grid', placeItems: 'center' }}>
                  <Factory size={20} style={{ color: 'var(--neon-lime)' }} />
                </div>
                <div>
                  <h4 style={{ fontSize: '15px', fontWeight: '600', color: '#ffffff' }}>Assembly Line Alpha</h4>
                  <p style={{ fontSize: '12px', color: 'var(--muted)' }}>★ 4.9 Model Performance (Stable)</p>
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <small style={{ fontSize: '11px', color: 'var(--muted)' }}>Target Station</small>
                  <p style={{ fontSize: '13px', color: '#ffffff', fontWeight: '500', marginTop: '2px' }}>Conveyor Beta #3</p>
                </div>
                <Link href="/upload" className="primary-button" style={{ padding: '6px 12px', fontSize: '12px', textDecoration: 'none' }}>
                  Run Scan
                </Link>
              </div>
            </div>

            {/* Card 2: Defect Rate / Yield */}
            <div className="panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '200px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11px', background: 'rgba(212,255,42,0.1)', border: '1px solid var(--neon-lime)', color: 'var(--neon-lime)', padding: '2px 8px', borderRadius: '12px', fontWeight: '600' }}>
                  30% Better
                </span>
                <span style={{ color: 'var(--muted)', cursor: 'pointer' }}>•••</span>
              </div>
              <div>
                <small style={{ fontSize: '12px', color: 'var(--muted)' }}>Defect Rate</small>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: '10px', marginTop: '2px' }}>
                  <strong style={{ fontSize: '28px', fontWeight: '700', color: '#ffffff', lineHeight: '1' }}>
                    {defectRate.toFixed(1)}%
                  </strong>
                  {/* Sparkline line SVG */}
                  <svg width="80" height="24" viewBox="0 0 80 24" fill="none" style={{ marginBottom: '4px' }}>
                    <path d="M2 18C10 18 15 2 25 2C35 2 40 20 50 20C60 20 70 8 78 8" stroke="var(--neon-lime)" strokeWidth="2" strokeLinecap="round" />
                    <circle cx="78" cy="8" r="3" fill="var(--neon-lime)" />
                  </svg>
                </div>
              </div>
              <Link href="/rework" className="primary-button" style={{ display: 'block', textAlign: 'center', padding: '10px 0', borderRadius: '24px', fontSize: '13px', textDecoration: 'none' }}>
                Rework Queue
              </Link>
            </div>

          </div>

          {/* Middle Row: Today's Defect Stats & System Vitals */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            
            {/* Card 3: Today's Defect Stats (Bar Chart) */}
            <div className="panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px', height: '220px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', color: 'var(--muted)', fontWeight: '600' }}>Weekly Volume</span>
                <span style={{ color: 'var(--muted)', cursor: 'pointer' }}>•••</span>
              </div>
              {/* Bars container */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flex: 1, padding: '0 10px' }}>
                {weeklyData.map((d, i) => (
                  <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', flex: 1, position: 'relative' }}>
                    {d.active && (
                      <div style={{
                        position: 'absolute',
                        bottom: '95px',
                        background: 'var(--neon-lime)',
                        color: '#000000',
                        fontSize: '9px',
                        fontWeight: '700',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        boxShadow: '0 0 10px var(--neon-glow)',
                        whiteSpace: 'nowrap'
                      }}>
                        {avgConfidence}%
                      </div>
                    )}
                    <div style={{
                      width: '18px',
                      height: '80px',
                      background: 'rgba(255,255,255,0.03)',
                      borderRadius: '10px',
                      display: 'flex',
                      alignItems: 'flex-end',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: '100%',
                        height: `${d.value}%`,
                        background: d.active ? 'var(--neon-lime)' : 'rgba(255,255,255,0.12)',
                        borderRadius: '10px',
                        boxShadow: d.active ? '0 0 12px var(--neon-glow)' : 'none'
                      }} />
                    </div>
                    <span style={{ fontSize: '11px', color: d.active ? 'var(--neon-lime)' : 'var(--muted)', fontWeight: '600' }}>{d.day}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Card 4: System Vitals / Sliders */}
            <div className="panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px', height: '220px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', color: 'var(--muted)', fontWeight: '600' }}>System Vitals</span>
                <span style={{ fontSize: '11px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', color: '#ffffff', padding: '2px 8px', borderRadius: '4px' }}>
                  Last 24h
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', flex: 1 }}>
                {/* Slider 1: AI Accuracy */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                  <div style={{ position: 'relative', height: '90px', width: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px' }}>
                    {/* Glowing Knob */}
                    <div style={{
                      position: 'absolute',
                      top: '15px',
                      left: '-4px',
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: 'var(--neon-lime)',
                      boxShadow: '0 0 12px var(--neon-glow)',
                      border: '2px solid #000'
                    }} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px' }}>
                    <Sparkles size={12} style={{ color: 'var(--neon-lime)' }} />
                    <span style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: '500' }}>Accuracy</span>
                  </div>
                  <small style={{ fontSize: '10px', color: '#ffffff', fontWeight: '600' }}>98.4%</small>
                </div>
                {/* Slider 2: GPU Load */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                  <div style={{ position: 'relative', height: '90px', width: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px' }}>
                    {/* Glowing Knob */}
                    <div style={{
                      position: 'absolute',
                      top: '40px',
                      left: '-4px',
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: 'var(--neon-lime)',
                      boxShadow: '0 0 12px var(--neon-glow)',
                      border: '2px solid #000'
                    }} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px' }}>
                    <Cpu size={12} style={{ color: 'var(--neon-lime)' }} />
                    <span style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: '500' }}>GPU Load</span>
                  </div>
                  <small style={{ fontSize: '10px', color: '#ffffff', fontWeight: '600' }}>72.1%</small>
                </div>
              </div>
            </div>

          </div>

          {/* Bottom Row: Quality Logs History */}
          <div className="panel" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <span style={{ fontSize: '13px', color: 'var(--muted)', fontWeight: '600' }}>Quality Logs History</span>
              <Link href="/inspection" style={{ fontSize: '11px', color: 'var(--neon-lime)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '2px' }}>
                View Logs <ArrowRight size={11} />
              </Link>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {inspections.slice(0, 3).map((item) => {
                const passed = (item.prediction || item.pass_fail || "").toLowerCase() === "pass";
                return (
                  <div
                    key={item.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 14px',
                      background: 'rgba(255,255,255,0.02)',
                      border: '1px solid rgba(255,255,255,0.04)',
                      borderRadius: '10px',
                      transition: 'all 0.2s'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        background: 'rgba(255,255,255,0.03)',
                        border: '1px solid rgba(255,255,255,0.06)',
                        display: 'grid',
                        placeItems: 'center',
                        fontWeight: '600',
                        fontSize: '11px',
                        color: passed ? 'var(--neon-lime)' : 'var(--red)'
                      }}>
                        {passed ? "OK" : "NG"}
                      </div>
                      <div>
                        <h5 style={{ fontSize: '13px', fontWeight: '600', color: '#ffffff' }}>
                          {item.product_id || "Unassigned Product"}
                        </h5>
                        <small style={{ fontSize: '10px', color: 'var(--muted)' }}>
                          {formatDateTime(item.created_at)} • {item.production_line || "Line Alpha"}
                        </small>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{
                        fontSize: '11px',
                        fontWeight: '600',
                        color: passed ? 'var(--neon-lime)' : 'var(--red)',
                        background: passed ? 'rgba(212,255,42,0.08)' : 'rgba(239,68,68,0.08)',
                        padding: '2px 8px',
                        borderRadius: '4px'
                      }}>
                        {item.prediction || "Fail"}
                      </span>
                      <ChevronRight size={14} style={{ color: 'var(--muted)' }} />
                    </div>
                  </div>
                );
              })}
              {!inspections.length && (
                <div style={{ padding: '20px', textAlign: 'center', color: 'var(--muted)', fontSize: '12px' }}>
                  No recent inspections on the floor.
                </div>
              )}
            </div>
          </div>

        </div>

        {/* Right Hand Area: Spatial Defect Map & Gauge (Columns 9 to 12) */}
        <div className="panel" style={{ gridColumn: 'span 4', padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '670px' }}>
          
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#ffffff', marginBottom: '4px' }}>Spatial Defect Map</h3>
            <p style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '20px' }}>Localized anomaly grid distribution.</p>
            
            {/* Mesh Graphic representation */}
            <div style={{
              height: '240px',
              background: 'radial-gradient(circle at 50% 50%, rgba(212,255,42,0.03) 0%, rgba(0,0,0,0.5) 100%)',
              border: '1px solid rgba(255,255,255,0.04)',
              borderRadius: '12px',
              display: 'grid',
              placeItems: 'center',
              position: 'relative',
              overflow: 'hidden',
              margin: '20px 0'
            }}>
              {/* Dotted mesh grid */}
              <div style={{
                position: 'absolute',
                top: 0, left: 0, right: 0, bottom: 0,
                backgroundImage: 'radial-gradient(rgba(255,255,255,0.08) 1px, transparent 0)',
                backgroundSize: '16px 16px',
                opacity: 0.8
              }} />
              {/* Target scanner line */}
              <div className="scan-line" style={{
                position: 'absolute',
                width: '100%',
                height: '2px',
                background: 'linear-gradient(90deg, transparent, var(--neon-lime), transparent)',
                boxShadow: '0 0 12px var(--neon-lime)',
                top: '40%'
              }} />
              {/* Simulated Defect hotspot overlay */}
              <div style={{
                position: 'absolute',
                top: '32%',
                left: '42%',
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: 'rgba(212,255,42,0.15)',
                border: '1.5px solid var(--neon-lime)',
                boxShadow: '0 0 15px var(--neon-glow)',
                display: 'grid',
                placeItems: 'center',
                animation: 'pulse 2s infinite'
              }}>
                <Flame size={14} style={{ color: 'var(--neon-lime)' }} />
              </div>
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
              <span style={{ fontSize: '42px', fontWeight: '700', color: '#ffffff', lineHeight: '1' }}>
                0.75
              </span>
              <span style={{ fontSize: '11px', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Cutoff Threshold
                <select style={{ background: 'none', border: 'none', color: 'var(--neon-lime)', fontSize: '11px', padding: 0, cursor: 'pointer' }}>
                  <option>Last month</option>
                </select>
              </span>
            </div>

            {/* Slider track representation */}
            <div style={{ position: 'relative', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', margin: '20px 0' }}>
              <div style={{ width: '75%', height: '100%', background: 'var(--neon-lime)', borderRadius: '3px' }} />
              <div style={{
                position: 'absolute',
                top: '-4px',
                left: '75%',
                width: '14px',
                height: '14px',
                borderRadius: '50%',
                background: 'var(--neon-lime)',
                border: '2px solid #000000',
                boxShadow: '0 0 8px var(--neon-glow)'
              }} />
            </div>

            {/* Time labels below slider */}
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--muted)', fontSize: '11px', fontWeight: '500', marginTop: '10px' }}>
              <span>0.10</span>
              <span>0.50</span>
              <span style={{ color: 'var(--neon-lime)', fontWeight: '700' }}>0.75 (Active)</span>
              <span>0.99</span>
            </div>
          </div>

          <div style={{ borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '14px', marginTop: '14px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '8px', padding: '10px', textAlign: 'center' }}>
              <small style={{ fontSize: '10px', color: 'var(--muted)', display: 'block' }}>Total Scans</small>
              <strong style={{ fontSize: '16px', color: '#ffffff', fontWeight: '700', marginTop: '2px', display: 'block' }}>{total}</strong>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '8px', padding: '10px', textAlign: 'center' }}>
              <small style={{ fontSize: '10px', color: 'var(--muted)', display: 'block' }}>Defects Caught</small>
              <strong style={{ fontSize: '16px', color: 'var(--neon-lime)', fontWeight: '700', marginTop: '2px', display: 'block' }}>{failed}</strong>
            </div>
          </div>

        </div>

      </div>
    </AppShell>
  );
}
