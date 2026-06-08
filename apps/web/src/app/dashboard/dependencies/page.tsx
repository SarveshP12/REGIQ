"use client";

import { useCallback, useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from "reactflow";
import "reactflow/dist/style.css";
import { apiFetch } from "@/lib/api-client";

interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties?: Record<string, unknown>;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
}

const TYPE_COLUMNS: Record<string, number> = {
  BusinessProcess: 0,
  Table: 1,
  Component: 2,
  Workflow: 3,
  Integration: 4,
  TestCase: 5,
  Defect: 6,
  Release: 7,
};

const TYPE_COLORS: Record<string, string> = {
  BusinessProcess: "#e0e7ff",
  Table: "#fef3c7",
  Component: "#ffe4e6",
  Workflow: "#d1fae5",
  Integration: "#fce7f3",
  TestCase: "#dbeafe",
  Defect: "#fee2e2",
  Release: "#f3e8ff",
};

function layoutNodes(nodes: GraphNode[]): Node[] {
  const rowByColumn: Record<number, number> = {};
  return nodes.map((n) => {
    const col = TYPE_COLUMNS[n.type] ?? 8;
    const row = rowByColumn[col] ?? 0;
    rowByColumn[col] = row + 1;
    const display =
      (n.properties?.name as string) ||
      (n.properties?.title as string) ||
      n.label ||
      n.id;
    return {
      id: n.id,
      position: { x: col * 260, y: row * 110 },
      data: {
        label: (
          <div className="text-xs">
            <div className="font-semibold text-slate-700">{n.type}</div>
            <div className="text-slate-900 mt-1">{display}</div>
          </div>
        ),
      },
      style: {
        background: TYPE_COLORS[n.type] ?? "#f8fafc",
        border: "1px solid #94a3b8",
        borderRadius: 8,
        padding: 10,
        width: 200,
      },
    };
  });
}

export default function DependencyGraphExplorer() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<{ nodes: number; relationships: number } | null>(null);
  const [rebuilding, setRebuilding] = useState(false);

  const accessToken = (session as { accessToken?: string } | null)?.accessToken;

  const loadHealth = useCallback(async () => {
    const res = await apiFetch("/api/v1/dependencies/health");
    if (res.ok) {
      const data = await res.json();
      setStats({ nodes: data.nodes ?? 0, relationships: data.relationships ?? 0 });
      return data.neo4j === true;
    }
    return false;
  }, []);

  const loadGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const healthy = await loadHealth();
      if (!healthy) {
        setError("Neo4j is not reachable. Run: docker compose up neo4j");
        setNodes([]);
        setEdges([]);
        return;
      }

      const res = await apiFetch(
        "/api/v1/dependencies/graph",
        {},
        accessToken
      );

      if (res.status === 404) {
        setError("Graph is empty. Click “Rebuild demo graph” to seed Incident Management.");
        setNodes([]);
        setEdges([]);
        return;
      }

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Failed to load graph (${res.status})`);
      }

      const data = await res.json();
      const graphNodes: GraphNode[] = data.nodes ?? [];
      const graphEdges: GraphEdge[] = data.edges ?? [];

      setNodes(layoutNodes(graphNodes));
      setEdges(
        graphEdges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.type,
          animated: e.type === "TESTS" || e.type === "COVERS" || e.type === "VALIDATES",
        })) as Edge[]
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load dependency graph");
    } finally {
      setLoading(false);
    }
  }, [accessToken, loadHealth, setNodes, setEdges]);

  const handleRebuild = async () => {
    setRebuilding(true);
    setError(null);
    try {
      const res = await apiFetch(
        "/api/v1/dependencies/rebuild",
        { method: "POST" },
        accessToken
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Rebuild failed");
      }
      await loadGraph();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Rebuild failed");
    } finally {
      setRebuilding(false);
    }
  };

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
      return;
    }
    if (status === "authenticated") {
      loadGraph();
    }
  }, [status, router, loadGraph]);

  return (
    <div className="min-h-screen bg-slate-50 p-6 flex flex-col">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div>
          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="text-sm text-indigo-600 hover:underline mb-2"
          >
            ← Back to dashboard
          </button>
          <h1 className="text-2xl font-bold text-slate-900">Dependency Graph Explorer</h1>
          <p className="text-sm text-slate-600 mt-1">
            Neo4j dependency map — Incident Management module (TESTS / COVERS / VALIDATES)
          </p>
        </div>
        <div className="flex items-center gap-3">
          {stats && (
            <span className="text-sm text-slate-600 bg-white border rounded-lg px-3 py-2">
              {stats.nodes} nodes · {stats.relationships} edges
            </span>
          )}
          <button
            type="button"
            onClick={() => loadGraph()}
            disabled={loading}
            className="px-4 py-2 rounded-lg border border-slate-300 bg-white text-sm font-medium hover:bg-slate-100 disabled:opacity-50"
          >
            Refresh
          </button>
          <button
            type="button"
            onClick={handleRebuild}
            disabled={rebuilding || !accessToken}
            className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
          >
            {rebuilding ? "Rebuilding…" : "Rebuild demo graph"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 text-amber-900 px-4 py-3 text-sm">
          {error}
        </div>
      )}

      <div className="flex-1 min-h-[700px] bg-white border border-slate-200 rounded-xl shadow-sm">
        {loading ? (
          <div className="flex items-center justify-center h-full text-slate-500">Loading graph…</div>
        ) : nodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-3">
            <p>No graph data to display.</p>
            <button
              type="button"
              onClick={handleRebuild}
              className="text-indigo-600 font-medium hover:underline"
            >
              Seed Incident Management demo graph
            </button>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
          >
            <MiniMap />
            <Controls />
            <Background />
          </ReactFlow>
        )}
      </div>
    </div>
  );
}
