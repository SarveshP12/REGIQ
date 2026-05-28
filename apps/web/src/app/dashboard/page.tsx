'use client';
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

  if (status === "loading") {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* Sidebar placeholder */}
      <div className="w-64 bg-white shadow-md flex-shrink-0 flex flex-col">
        <div className="p-4 border-b">
          <h1 className="text-xl font-bold text-indigo-600">REGIQ Admin</h1>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          <button className="w-full text-left bg-gray-100 px-4 py-2 rounded text-indigo-700 font-medium">Dashboard</button>
          <button className="w-full text-left px-4 py-2 rounded text-gray-700 hover:bg-gray-100" onClick={() => router.push('/tests')}>Test Repository</button>
          <button className="w-full text-left px-4 py-2 rounded text-gray-700 hover:bg-gray-100">ServiceNow Sync</button>
        </nav>
      </div>

      <div className="flex-1 flex flex-col">
        <nav className="bg-white shadow h-16 flex justify-end items-center px-8">
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">
              {session?.user?.name} ({session?.user?.role})
            </span>
            <button
              onClick={() => signOut()}
              className="rounded bg-gray-200 px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-300"
            >
              Log Out
            </button>
          </div>
        </nav>

        <main className="p-8">
          <h1 className="text-2xl font-bold mb-6">Dashboard Overview</h1>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6 border-t-4 border-indigo-500">
              <h3 className="text-gray-500 text-sm font-semibold mb-2">Total Test Cases</h3>
              <p className="text-3xl font-bold text-gray-800">1,245</p>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6 border-t-4 border-green-500">
              <h3 className="text-gray-500 text-sm font-semibold mb-2">ServiceNow Sync Status</h3>
              <p className="text-3xl font-bold text-gray-800 flex items-center">
                <span className="w-4 h-4 rounded-full bg-green-500 mr-2"></span>
                Healthy
              </p>
              <p className="text-sm text-gray-400 mt-2">Last Sync: 15 mins ago</p>
            </div>

            <div className="bg-white rounded-lg shadow p-6 border-t-4 border-purple-500">
              <h3 className="text-gray-500 text-sm font-semibold mb-2">Active Users</h3>
              <p className="text-3xl font-bold text-gray-800">12</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-bold mb-4">Recent Sync Activity</h3>
              <div className="text-sm text-gray-500">
                <ul className="space-y-3">
                  <li className="flex justify-between items-center border-b pb-2"><span className="font-medium">Incident Management</span> <span className="text-green-600">Success</span></li>
                  <li className="flex justify-between items-center border-b pb-2"><span className="font-medium">Change Request</span> <span className="text-green-600">Success</span></li>
                  <li className="flex justify-between items-center pb-2"><span className="font-medium">Catalog Items</span> <span className="text-yellow-600">Parsed with warnings</span></li>
                </ul>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-bold mb-4">Test Quality Overview</h3>
              <div className="text-sm text-gray-500 h-32 flex items-center justify-center border-2 border-dashed border-gray-200 rounded">
                Placeholder for Chart
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
