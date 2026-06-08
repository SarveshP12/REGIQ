'use client';

import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

// Mock types
interface UserRecord {
  id: string;
  name: string;
  email: string;
  role: string;
  status: 'Active' | 'Inactive';
}

interface ConnectionRecord {
  id: string;
  name: string;
  url: string;
  env: 'dev' | 'test' | 'uat' | 'prod';
  status: 'connected' | 'unhealthy' | 'syncing';
  lastSync: string;
}

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  // Component states
  const [activeTab, setActiveTab] = useState<'dashboard' | 'sync' | 'users'>('dashboard');
  
  // Connection states
  const [connections, setConnections] = useState<ConnectionRecord[]>([
    { id: '1', name: 'ServiceNow Dev Instance', url: 'https://dev98432.service-now.com', env: 'dev', status: 'connected', lastSync: '12 mins ago' },
    { id: '2', name: 'ServiceNow UAT Instance', url: 'https://regiquat.service-now.com', env: 'uat', status: 'unhealthy', lastSync: 'Yesterday' }
  ]);

  // User management states
  const [users, setUsers] = useState<UserRecord[]>([
    { id: '1', name: 'Sarvesh Patil', email: 'sarvesh@regiq.io', role: 'super_admin', status: 'Active' },
    { id: '2', name: 'Aileen Mottern', email: 'aileen.mottern@regiq.io', role: 'test_manager', status: 'Active' },
    { id: '3', name: 'Jane Doe', email: 'jane.doe@regiq.io', role: 'qa_engineer', status: 'Active' },
    { id: '4', name: 'John Smith', email: 'john.smith@regiq.io', role: 'viewer', status: 'Active' },
    { id: '5', name: 'CI/CD Service Account', email: 'service-cicd@regiq.io', role: 'api_service', status: 'Active' },
    { id: '6', name: 'Local Administrator', email: 'admin@regiq.io', role: 'tenant_admin', status: 'Active' }
  ]);

  // Sync log activity feed
  const [activities, setActivities] = useState([
    { id: '1', type: 'sync', title: 'Delta sync completed', detail: 'ServiceNow Dev — Synced 12 components.', time: '12 mins ago', status: 'success' },
    { id: '2', type: 'user', title: 'Role updated', detail: 'Aileen Mottern set to Test Manager.', time: '2 hours ago', status: 'info' },
    { id: '3', type: 'webhook', title: 'Update set promoted', detail: 'Dev to Test promotion webhook received.', time: '4 hours ago', status: 'success' },
    { id: '4', type: 'security', title: 'API Key generated', detail: 'CI/CD runner key registered.', time: '1 day ago', status: 'warning' }
  ]);

  const [atfMessage, setAtfMessage] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState<string | null>(null);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  // Trigger manual sync simulation
  const handleSyncTrigger = (id: string) => {
    setIsSyncing(id);
    setConnections(prev => prev.map(c => c.id === id ? { ...c, status: 'syncing' } : c));
    
    setTimeout(() => {
      setConnections(prev => prev.map(c => c.id === id ? { ...c, status: 'connected', lastSync: 'Just now' } : c));
      setIsSyncing(null);
      // Append activity
      const targetConn = connections.find(c => c.id === id);
      setActivities(prev => [
        {
          id: String(Date.now()),
          type: 'sync',
          title: 'Manual Sync Completed',
          detail: `${targetConn?.name} fully updated.`,
          time: 'Just now',
          status: 'success'
        },
        ...prev
      ]);
    }, 2000);
  };

  // Run ServiceNow connection health test
  const handleHealthCheck = (id: string) => {
    setConnections(prev => prev.map(c => c.id === id ? { ...c, status: 'syncing' } : c));
    setTimeout(() => {
      setConnections(prev => prev.map(c => c.id === id ? { ...c, status: 'connected' } : c));
    }, 1500);
  };

  // ATF Test case import simulation
  const handleImportATF = () => {
    setAtfMessage("Connecting to ServiceNow ATF Registry...");
    setTimeout(() => {
      setAtfMessage("Found 2 pending ATF test cases. Processing mapper transformations...");
      setTimeout(() => {
        setAtfMessage("Successfully imported 2 ATF cases to local SQL Test Repository!");
        setActivities(prev => [
          {
            id: String(Date.now()),
            type: 'sync',
            title: 'ATF Import Completed',
            detail: 'Imported Incident and Change Risk Assessment ATF cases.',
            time: 'Just now',
            status: 'success'
          },
          ...prev
        ]);
        setTimeout(() => setAtfMessage(null), 3000);
      }, 1500);
    }, 1500);
  };

  // Role update handler
  const handleRoleChange = (userId: string, newRole: string) => {
    setUsers(prev => prev.map(u => u.id === userId ? { ...u, role: newRole } : u));
    const targetUser = users.find(u => u.id === userId);
    setActivities(prev => [
      {
        id: String(Date.now()),
        type: 'user',
        title: 'User Role Modified',
        detail: `Updated role for ${targetUser?.name} to ${newRole.toUpperCase()}.`,
        time: 'Just now',
        status: 'warning'
      },
      ...prev
    ]);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans">
      
      {/* ── Sidebar Component ───────────────────────────────── */}
      <aside className="w-72 bg-slate-900 border-r border-slate-800 flex flex-col flex-shrink-0">
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
              RQ
            </div>
            <div>
              <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">REGIQ</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">Regression Intelligence</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-6 space-y-2">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition duration-150 ${
              activeTab === 'dashboard'
                ? 'bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 font-medium'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            <span>📊</span>
            <span>Dashboard Hub</span>
          </button>
          
          <button
            onClick={() => router.push('/tests')}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition duration-150"
          >
            <span>📁</span>
            <span>Test Repository</span>
          </button>

          <button
            onClick={() => router.push('/dashboard/dependencies')}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition duration-150"
          >
            <span>🕸️</span>
            <span>Dependency Graph</span>
          </button>

          <button
            onClick={() => setActiveTab('sync')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition duration-150 ${
              activeTab === 'sync'
                ? 'bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 font-medium'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            <span>🔄</span>
            <span>ServiceNow Sync</span>
          </button>

          <button
            onClick={() => setActiveTab('users')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition duration-150 ${
              activeTab === 'users'
                ? 'bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 font-medium'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            }`}
          >
            <span>👥</span>
            <span>User & RBAC Panel</span>
          </button>
        </nav>

        <div className="p-6 border-t border-slate-800 bg-slate-900/50">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-indigo-400">
              {session?.user?.name ? session.user.name[0].toUpperCase() : 'U'}
            </div>
            <div className="truncate">
              <p className="text-sm font-medium text-slate-200 truncate">{session?.user?.name || 'Standard User'}</p>
              <p className="text-xs text-slate-500 truncate">{session?.user?.email || 'user@regiq.io'}</p>
            </div>
          </div>
          <button
            onClick={() => signOut()}
            className="w-full py-2.5 rounded-xl border border-slate-800 bg-slate-900 text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition duration-150"
          >
            Log Out
          </button>
        </div>
      </aside>

      {/* ── Main View Area ──────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <header className="h-20 bg-slate-900/50 backdrop-blur-md border-b border-slate-900 flex justify-between items-center px-8 sticky top-0 z-10">
          <div>
            <h2 className="text-lg font-bold text-slate-200">
              {activeTab === 'dashboard' && 'Systems Analytics & Repository Health'}
              {activeTab === 'sync' && 'ServiceNow Connectors & Sync Status'}
              {activeTab === 'users' && 'Access Management & Permissions Matrix'}
            </h2>
            <p className="text-xs text-slate-500">Tenant Workspace ID: regiq-corp-main</p>
          </div>
          <div className="flex items-center space-x-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span className="w-1.5 h-1.5 mr-1.5 rounded-full bg-emerald-400 animate-ping"></span>
              Secure Session (TLS 1.3)
            </span>
          </div>
        </header>

        {/* ── Tab View 1: Dashboard Hub ───────────────────────── */}
        {activeTab === 'dashboard' && (
          <main className="p-8 space-y-8 max-w-7xl">
            {/* Health Highlights Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
                <div className="absolute right-4 top-4 text-2xl text-slate-700">📋</div>
                <h3 className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">Total Test Cases</h3>
                <p className="text-4xl font-extrabold text-white">1,245</p>
                <div className="mt-4 flex items-center text-xs text-slate-500">
                  <span className="text-emerald-500 font-semibold mr-1.5">↑ 8%</span> vs last month
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
                <div className="absolute right-4 top-4 text-2xl text-slate-700">🔒</div>
                <h3 className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">Data Isolation</h3>
                <p className="text-4xl font-extrabold text-white">Active</p>
                <div className="mt-4 flex items-center text-xs text-slate-500">
                  <span className="text-indigo-400 font-semibold mr-1.5">PostgreSQL RLS</span> active at session
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
                <div className="absolute right-4 top-4 text-2xl text-slate-700">🔌</div>
                <h3 className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">ServiceNow Sync</h3>
                <p className="text-4xl font-extrabold text-emerald-400 flex items-center">
                  <span className="w-3.5 h-3.5 rounded-full bg-emerald-400 mr-2.5 shadow-lg shadow-emerald-400/20"></span>
                  Healthy
                </p>
                <div className="mt-4 flex items-center text-xs text-slate-500">
                  <span className="text-slate-400 font-semibold mr-1.5">Delta Sync</span> scheduled (15m interval)
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
                <div className="absolute right-4 top-4 text-2xl text-slate-700">🛡️</div>
                <h3 className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">Security Standard</h3>
                <p className="text-4xl font-extrabold text-indigo-400">AES-256</p>
                <div className="mt-4 flex items-center text-xs text-slate-500">
                  <span className="text-indigo-400 font-semibold mr-1.5">GCM Mode</span> for secret fields
                </div>
              </div>

            </div>

            {/* Test Repository Health & SVG charts */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 lg:col-span-2">
                <h3 className="text-md font-bold text-slate-200 mb-6 flex items-center">
                  <span className="mr-2">📈</span>
                  Test Repository Quality & Distribution
                </h3>
                
                {/* SVG Chart Visualization */}
                <div className="h-64 flex items-end justify-between px-4 pb-4 border-b border-slate-800">
                  <div className="flex flex-col items-center w-16">
                    <div className="bg-indigo-500 w-8 rounded-t-lg transition-all duration-500" style={{ height: '140px' }}></div>
                    <span className="text-[10px] text-slate-500 mt-2 font-semibold uppercase">Approved (62%)</span>
                  </div>
                  <div className="flex flex-col items-center w-16">
                    <div className="bg-amber-500 w-8 rounded-t-lg transition-all duration-500" style={{ height: '70px' }}></div>
                    <span className="text-[10px] text-slate-500 mt-2 font-semibold uppercase">Review (24%)</span>
                  </div>
                  <div className="flex flex-col items-center w-16">
                    <div className="bg-slate-600 w-8 rounded-t-lg transition-all duration-500" style={{ height: '40px' }}></div>
                    <span className="text-[10px] text-slate-500 mt-2 font-semibold uppercase">Draft (14%)</span>
                  </div>
                  <div className="flex flex-col items-center w-16">
                    <div className="bg-red-500 w-8 rounded-t-lg transition-all duration-500" style={{ height: '25px' }}></div>
                    <span className="text-[10px] text-slate-500 mt-2 font-semibold uppercase">Stale (3%)</span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mt-6 text-center">
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <p className="text-[10px] text-slate-500 font-semibold uppercase">Critical Tests</p>
                    <p className="text-lg font-bold text-red-400">342</p>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <p className="text-[10px] text-slate-500 font-semibold uppercase">Automated</p>
                    <p className="text-lg font-bold text-indigo-400">712</p>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <p className="text-[10px] text-slate-500 font-semibold uppercase">Unmapped</p>
                    <p className="text-lg font-bold text-amber-500">18</p>
                  </div>
                </div>
              </div>

              {/* User Activity Feed */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col">
                <h3 className="text-md font-bold text-slate-200 mb-6 flex items-center">
                  <span className="mr-2">🔔</span>
                  Live User Activity Feed
                </h3>
                
                <div className="flex-1 space-y-4 overflow-y-auto max-h-[300px] pr-2 scrollbar-thin">
                  {activities.map((act) => (
                    <div key={act.id} className="flex space-x-3 p-3 rounded-xl bg-slate-950 border border-slate-900 hover:border-slate-800 transition duration-150">
                      <div className="text-lg mt-0.5">
                        {act.type === 'sync' && '🔄'}
                        {act.type === 'user' && '👥'}
                        {act.type === 'webhook' && '🪝'}
                        {act.type === 'security' && '🔑'}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-start">
                          <h4 className="text-xs font-bold text-slate-200 truncate">{act.title}</h4>
                          <span className="text-[9px] text-slate-500 font-semibold whitespace-nowrap ml-2">{act.time}</span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-1">{act.detail}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </main>
        )}

        {/* ── Tab View 2: ServiceNow Sync Panel ────────────────── */}
        {activeTab === 'sync' && (
          <main className="p-8 space-y-8 max-w-7xl">
            {/* Alert / Progress indicator */}
            {atfMessage && (
              <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-sm flex items-center space-x-3 animate-pulse">
                <span>⚡</span>
                <span className="font-semibold">{atfMessage}</span>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              
              {/* Connection Cards */}
              <div className="lg:col-span-2 space-y-6">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-md font-bold text-slate-200">Registered Instances</h3>
                  <button 
                    onClick={handleImportATF}
                    className="bg-indigo-600 hover:bg-indigo-700 text-xs font-semibold px-4 py-2.5 rounded-xl text-white shadow-lg shadow-indigo-500/20 transition duration-150 flex items-center space-x-2"
                  >
                    <span>⚡</span>
                    <span>Import ATF Test Cases</span>
                  </button>
                </div>

                {connections.map((conn) => (
                  <div key={conn.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition duration-150">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      
                      <div className="flex items-start space-x-4">
                        <div className="text-3xl mt-1">🔌</div>
                        <div>
                          <div className="flex items-center space-x-2.5">
                            <h4 className="font-bold text-slate-200">{conn.name}</h4>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              conn.env === 'prod' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-slate-800 text-slate-400'
                            }`}>
                              {conn.env}
                            </span>
                          </div>
                          <p className="text-xs text-indigo-400 mt-1">{conn.url}</p>
                          <div className="mt-3 flex items-center space-x-4 text-[11px] text-slate-500">
                            <span>Last Synced: <strong className="text-slate-400">{conn.lastSync}</strong></span>
                            <span>•</span>
                            <span>Credentials: <strong className="text-indigo-400">AES-256 Encrypted</strong></span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 self-end md:self-center">
                        <div className="flex items-center mr-3">
                          <span className={`w-2 h-2 rounded-full mr-2 ${
                            conn.status === 'connected' ? 'bg-emerald-400 animate-pulse' : conn.status === 'syncing' ? 'bg-indigo-400 animate-spin' : 'bg-rose-400 animate-ping'
                          }`}></span>
                          <span className="text-xs text-slate-400 capitalize font-medium">{conn.status}</span>
                        </div>
                        
                        <button
                          onClick={() => handleHealthCheck(conn.id)}
                          className="px-3 py-1.5 rounded-lg border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 text-xs font-semibold transition"
                        >
                          Check Health
                        </button>
                        
                        <button
                          onClick={() => handleSyncTrigger(conn.id)}
                          disabled={isSyncing !== null}
                          className="px-3 py-1.5 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-700 text-indigo-400 text-xs font-semibold transition"
                        >
                          Sync Now
                        </button>
                      </div>

                    </div>
                  </div>
                ))}
              </div>

              {/* Technical configurations */}
              <div className="space-y-6">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                  <h3 className="text-sm font-bold text-slate-200 mb-4">Sync Engine Fallback & Schedules</h3>
                  <div className="space-y-4 text-xs">
                    <div className="p-3 bg-slate-950 rounded-xl border border-slate-900">
                      <p className="font-bold text-slate-300">Delta polling fallback</p>
                      <p className="text-slate-500 mt-1">If ServiceNow webhook events fail to deliver, the Celery daemon falls back to 15-minute scheduled API polling.</p>
                    </div>
                    <div className="p-3 bg-slate-950 rounded-xl border border-slate-900">
                      <p className="font-bold text-slate-300">Nightly full sync job</p>
                      <p className="text-slate-500 mt-1">Triggers at 02:00 AM UTC daily to perform full metadata schema snapshots and rebuild regression impact indexes.</p>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </main>
        )}

        {/* ── Tab View 3: User & RBAC Management ───────────────── */}
        {activeTab === 'users' && (
          <main className="p-8 space-y-8 max-w-7xl">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 overflow-hidden">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-md font-bold text-slate-200">Active Tenant Users</h3>
                <span className="text-xs text-slate-500 font-medium">Showing 6 accounts assigned with enterprise RBAC roles</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-850 text-xs text-slate-400 font-bold uppercase">
                      <th className="pb-3 pt-2 pl-3">Name</th>
                      <th className="pb-3 pt-2">Email</th>
                      <th className="pb-3 pt-2">Role Authority</th>
                      <th className="pb-3 pt-2">Account Status</th>
                      <th className="pb-3 pt-2 pr-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850 text-sm">
                    {users.map((u) => (
                      <tr key={u.id} className="hover:bg-slate-900/50 transition">
                        <td className="py-4 pl-3 font-semibold text-slate-200">{u.name}</td>
                        <td className="py-4 text-slate-400">{u.email}</td>
                        <td className="py-4">
                          <select
                            value={u.role}
                            onChange={(e) => handleRoleChange(u.id, e.target.value)}
                            className="bg-slate-950 border border-slate-800 rounded-lg text-xs font-semibold text-indigo-400 py-1.5 px-3 focus:outline-none focus:border-indigo-500"
                          >
                            <option value="super_admin">Super Admin (All Access)</option>
                            <option value="tenant_admin">Tenant Admin</option>
                            <option value="test_manager">Test Manager</option>
                            <option value="qa_engineer">QA Engineer</option>
                            <option value="viewer">Viewer (Read-Only)</option>
                            <option value="api_service">API Service Account</option>
                          </select>
                        </td>
                        <td className="py-4">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            {u.status}
                          </span>
                        </td>
                        <td className="py-4 pr-3 text-right text-xs">
                          <button className="text-slate-500 hover:text-white transition font-medium mr-3">Edit</button>
                          <button className="text-rose-500/75 hover:text-rose-500 transition font-medium">Deactivate</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </main>
        )}

      </div>
    </div>
  );
}
