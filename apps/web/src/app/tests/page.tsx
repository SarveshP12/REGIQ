export default function TestRepositoryPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Test Repository</h1>
      <div className="bg-white rounded shadow p-6">
        <div className="flex justify-between mb-4">
          <input 
            type="text" 
            placeholder="Search test cases..." 
            className="border p-2 rounded w-1/3"
          />
          <button className="bg-blue-600 text-white px-4 py-2 rounded">
            + New Test Case
          </button>
        </div>
        <table className="w-full text-left border-collapse">
          <thead>
            <tr>
              <th className="border-b p-2">ID</th>
              <th className="border-b p-2">Title</th>
              <th className="border-b p-2">Status</th>
              <th className="border-b p-2">Module</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="p-2 border-b">TC-1001</td>
              <td className="p-2 border-b">Verify User Login</td>
              <td className="p-2 border-b"><span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">Active</span></td>
              <td className="p-2 border-b">Authentication</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
