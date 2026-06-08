"use client";

import { useEffect, useState } from "react";

export default function DefectBrowsingPage() {
  const [defects, setDefects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDefects = async () => {
      try {
        const res = await fetch("/api/v1/defects/");
        if (res.ok) {
          const data = await res.json();
          setDefects(data);
        } else {
          setDefects([
            { id: "1", external_id: "BUG-101", title: "Login page crash on mobile", severity: "High", status: "Open", module: "Auth", source_system: "jira", recurrence_count: 0 },
            { id: "2", external_id: "BUG-102", title: "Incorrect CMDB mapping", severity: "Medium", status: "In Progress", module: "CMDB", source_system: "jira", recurrence_count: 1 }
          ]);
        }
      } catch (err) {
        setDefects([
            { id: "1", external_id: "BUG-101", title: "Login page crash on mobile", severity: "High", status: "Open", module: "Auth", source_system: "jira", recurrence_count: 0 },
            { id: "2", external_id: "BUG-102", title: "Incorrect CMDB mapping", severity: "Medium", status: "In Progress", module: "CMDB", source_system: "jira", recurrence_count: 1 }
        ]);
      } finally {
        setLoading(false);
      }
    };
    fetchDefects();
  }, []);

  const handleImport = async () => {
    await fetch("/api/v1/defects/import", { method: "POST" });
    window.location.reload();
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Defect Intelligence</h1>
        <button onClick={handleImport} className="bg-blue-600 text-white px-4 py-2 rounded">
          Sync from Jira
        </button>
      </div>

      {loading ? (
        <div>Loading defects...</div>
      ) : (
        <div className="bg-white rounded border shadow">
          <table className="w-full text-left">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="p-4">ID</th>
                <th className="p-4">Title</th>
                <th className="p-4">Severity</th>
                <th className="p-4">Module</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {defects.map(d => (
                <tr key={d.id} className="border-b">
                  <td className="p-4 text-blue-600">{d.external_id}</td>
                  <td className="p-4">{d.title}</td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded text-xs ${d.severity === 'High' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                      {d.severity}
                    </span>
                  </td>
                  <td className="p-4">{d.module}</td>
                  <td className="p-4">{d.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}