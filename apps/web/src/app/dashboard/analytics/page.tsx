"use client";

import { useEffect, useState } from "react";

export default function EnhancedAIDashboard() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    // Mocking the dashboards data
    setStats({
      coverage: [
        { module: "Incident", coverage: 85, critical: 10 },
        { module: "Change", coverage: 60, critical: 5 },
        { module: "CMDB", coverage: 95, critical: 15 },
      ],
      defects: {
        total: 142,
        highSeverity: 24,
        distribution: [
          { module: "Incident", count: 45 },
          { module: "Change", count: 20 },
          { module: "CMDB", count: 77 },
        ]
      },
      classification: {
        accuracy: "92.4%",
        needsReview: 14,
        distribution: {
          "Critical": 45,
          "High": 130,
          "Medium": 412,
          "Low": 210
        }
      }
    });
  }, []);

  if (!stats) return <div className="p-6">Loading dashboard...</div>;

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">AI Analytics Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Coverage Panel */}
        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Regression Coverage</h2>
          <div className="space-y-4">
            {stats.coverage.map((c: any) => (
              <div key={c.module}>
                <div className="flex justify-between text-sm mb-1">
                  <span>{c.module}</span>
                  <span>{c.coverage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className={`h-2 rounded-full ${c.coverage > 80 ? 'bg-green-500' : 'bg-yellow-500'}`} style={{ width: `${c.coverage}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Defect Intelligence Panel */}
        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Defect Intelligence</h2>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-blue-50 p-4 rounded text-center">
              <div className="text-2xl font-bold text-blue-700">{stats.defects.total}</div>
              <div className="text-xs text-slate-600">Total Defects</div>
            </div>
            <div className="bg-red-50 p-4 rounded text-center">
              <div className="text-2xl font-bold text-red-700">{stats.defects.highSeverity}</div>
              <div className="text-xs text-slate-600">High Severity</div>
            </div>
          </div>
          <div className="space-y-2">
            {stats.defects.distribution.map((d: any) => (
              <div key={d.module} className="flex justify-between text-sm">
                <span>{d.module}</span>
                <span className="font-semibold">{d.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* AI Classification Panel */}
        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <h2 className="text-lg font-semibold mb-4">AI Classification Status</h2>
          <div className="flex justify-between mb-4">
            <div>
              <div className="text-xs text-slate-500">Model Accuracy</div>
              <div className="text-xl font-bold text-green-600">{stats.classification.accuracy}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Review Queue</div>
              <div className="text-xl font-bold text-orange-500">{stats.classification.needsReview} pending</div>
            </div>
          </div>
          <div>
            <div className="text-xs font-semibold mb-2 text-slate-500">Criticality Distribution</div>
            {Object.entries(stats.classification.distribution).map(([k, v]) => (
              <div key={k} className="flex justify-between text-sm mb-1">
                <span>{k}</span>
                <span>{v as React.ReactNode}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}