'use client';

import { useRouter } from "next/navigation";
import { useState } from "react";

// Types
interface TestStep {
  id: string;
  step_number: number;
  action: string;
  expected_result: string;
}

interface TestCase {
  id: string;
  title: string;
  description: string;
  preconditions: string;
  expected_results: string;
  format_type: 'structured' | 'bdd';
  status: 'draft' | 'review' | 'approved' | 'archived';
  criticality: 'low' | 'medium' | 'high';
  type_tags: string[];
  automation_flag: 'manual' | 'automated' | 'hybrid';
  steps: TestStep[];
  bdd_script?: string;
  version: number;
}

export default function TestRepositoryPage() {
  const router = useRouter();

  // Primary state: Test Cases list
  const [testCases, setTestCases] = useState<TestCase[]>([
    {
      id: 'TC-1001',
      title: 'Verify Incident Creation with SLA triggers',
      description: 'Ensure P1 incidents accurately register SLA countdown timers in ServiceNow.',
      preconditions: 'User authenticated, ServiceNow incident catalog active.',
      expected_results: 'P1 incident created and SLA clock begins counting down.',
      format_type: 'structured',
      status: 'approved',
      criticality: 'high',
      type_tags: ['incident', 'sla'],
      automation_flag: 'automated',
      steps: [
        { id: '1', step_number: 1, action: 'Open "Create Incident" form', expected_result: 'Form loaded with Caller pre-populated' },
        { id: '2', step_number: 2, action: 'Select Impact=1 and Urgency=1', expected_result: 'Priority field updates to P1' },
        { id: '3', step_number: 3, action: 'Submit form', expected_result: 'Incident registered and SLA countdown visible' }
      ],
      version: 2
    },
    {
      id: 'TC-1002',
      title: 'Given assessment questions, verify Change Risk calculations',
      description: 'Verify risk level upgrades to Moderate on high answers.',
      preconditions: 'Standard Change Form open in Assess state.',
      expected_results: 'Risk score recalculated as Moderate after saving form responses.',
      format_type: 'bdd',
      status: 'review',
      criticality: 'medium',
      type_tags: ['change', 'risk-assessment'],
      automation_flag: 'manual',
      steps: [],
      bdd_script: 'Feature: Change Risk Assessment\nScenario: High response risk evaluation\n  Given a user has opened the Standard Change Form\n  When the user answers the risk questions with high values\n  Then the system risk field should update to "Moderate"',
      version: 1
    }
  ]);

  // Search and filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Modal controls
  const [editorOpen, setEditorOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);

  // Editor states
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editPre, setEditPre] = useState("");
  const [editExp, setEditExp] = useState("");
  const [editFormat, setEditFormat] = useState<'structured' | 'bdd'>('structured');
  const [editStatus, setEditStatus] = useState<'draft' | 'review' | 'approved'>('draft');
  const [editCrit, setEditCrit] = useState<'low' | 'medium' | 'high'>('medium');
  const [editAuto, setEditAuto] = useState<'manual' | 'automated' | 'hybrid'>('manual');
  const [editSteps, setEditSteps] = useState<TestStep[]>([]);
  const [editBddScript, setEditBddScript] = useState("");
  const [editTagsStr, setEditTagsStr] = useState("");

  // Import Wizard states
  const [importStep, setImportStep] = useState(1);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fieldMappings, setFieldMappings] = useState({
    title: 'name',
    description: 'description',
    steps: 'steps_json',
    criticality: 'criticality'
  });
  const [importPreview, setImportPreview] = useState([
    { row: 1, title: 'Verify User Session Lock', status: 'valid', reason: 'Passed checks' },
    { row: 2, title: '', status: 'invalid', reason: 'Missing mandatory Title field' },
    { row: 3, title: 'Check REST Endpoint Auth', status: 'valid', reason: 'Passed checks' }
  ]);
  const [isImporting, setIsImporting] = useState(false);

  // Export States
  const [exportFormat, setExportFormat] = useState<'xlsx' | 'csv' | 'pdf'>('xlsx');
  const [exportStatus, setExportStatus] = useState<'all' | 'approved'>('all');
  const [isExporting, setIsExporting] = useState(false);

  // Open editor for a new/existing case
  const openEditor = (tc: TestCase | null = null) => {
    if (tc) {
      setEditingId(tc.id);
      setEditTitle(tc.title);
      setEditDesc(tc.description);
      setEditPre(tc.preconditions);
      setEditExp(tc.expected_results);
      setEditFormat(tc.format_type);
      setEditStatus(tc.status as any);
      setEditCrit(tc.criticality);
      setEditAuto(tc.automation_flag);
      setEditSteps(tc.steps);
      setEditBddScript(tc.bdd_script || "");
      setEditTagsStr(tc.type_tags.join(", "));
    } else {
      setEditingId(null);
      setEditTitle("");
      setEditDesc("");
      setEditPre("");
      setEditExp("");
      setEditFormat('structured');
      setEditStatus('draft');
      setEditCrit('medium');
      setEditAuto('manual');
      setEditSteps([
        { id: '1', step_number: 1, action: '', expected_result: '' }
      ]);
      setEditBddScript("Feature: \nScenario: \n  Given \n  When \n  Then ");
      setEditTagsStr("");
    }
    setEditorOpen(true);
  };

  // Save/Add Test Case
  const handleSaveTestCase = () => {
    if (!editTitle) return alert("Title is required!");

    const tags = editTagsStr.split(",").map(t => t.trim()).filter(Boolean);

    if (editingId) {
      // Edit
      setTestCases(prev => prev.map(tc => tc.id === editingId ? {
        ...tc,
        title: editTitle,
        description: editDesc,
        preconditions: editPre,
        expected_results: editExp,
        format_type: editFormat,
        status: editStatus as any,
        criticality: editCrit,
        automation_flag: editAuto,
        steps: editSteps,
        bdd_script: editBddScript,
        type_tags: tags,
        version: tc.version + 1
      } : tc));
    } else {
      // Create new
      const newId = `TC-${1000 + testCases.length + 1}`;
      const newTestCase: TestCase = {
        id: newId,
        title: editTitle,
        description: editDesc,
        preconditions: editPre,
        expected_results: editExp,
        format_type: editFormat,
        status: editStatus as any,
        criticality: editCrit,
        automation_flag: editAuto,
        steps: editSteps,
        bdd_script: editBddScript,
        type_tags: tags,
        version: 1
      };
      setTestCases(prev => [newTestCase, ...prev]);
    }
    setEditorOpen(false);
  };

  // Step editor actions
  const addStep = () => {
    setEditSteps(prev => [
      ...prev,
      { id: String(prev.length + 1), step_number: prev.length + 1, action: '', expected_result: '' }
    ]);
  };

  const updateStep = (index: number, field: 'action' | 'expected_result', value: string) => {
    setEditSteps(prev => prev.map((s, idx) => idx === index ? { ...s, [field]: value } : s));
  };

  const removeStep = (index: number) => {
    setEditSteps(prev => prev.filter((_, idx) => idx !== index).map((s, idx) => ({ ...s, step_number: idx + 1 })));
  };

  // Import flow trigger
  const runBulkImport = () => {
    setIsImporting(true);
    setTimeout(() => {
      // Simulating bulk injection of 524 test cases!
      const mockImportedCases: TestCase[] = Array.from({ length: 5 }, (_, i) => ({
        id: `TC-${2000 + i + 1}`,
        title: `ServiceNow ATF Ingested Case #${i + 1}`,
        description: `Bulk imported automated regression case covering ITSM process variables.`,
        preconditions: 'Imported from Excel file data parser validation.',
        expected_results: 'All matching steps transition successfully.',
        format_type: 'structured',
        status: 'approved',
        criticality: 'medium',
        type_tags: ['imported', 'excel-bulk'],
        automation_flag: 'automated',
        steps: [
          { id: '1', step_number: 1, action: 'Read record update set template', expected_result: 'Template parsed' },
          { id: '2', step_number: 2, action: 'Save to test suite', expected_result: 'Case updated' }
        ],
        version: 1
      }));

      setTestCases(prev => [...mockImportedCases, ...prev]);
      setIsImporting(false);
      setImportOpen(false);
      alert("Ingestion Complete: Successfully verified and imported 524 test cases into local database schema!");
    }, 2000);
  };

  // Export flow builder
  const runExport = () => {
    setIsExporting(true);
    setTimeout(() => {
      setIsExporting(false);
      setExportOpen(false);
      alert(`Export Successful: Downloaded test repository reports (${exportFormat.toUpperCase()}) successfully!`);
    }, 1500);
  };

  // Filter list
  const filteredCases = testCases.filter(tc => {
    const matchSearch = tc.title.toLowerCase().includes(search.toLowerCase()) || 
                        tc.description.toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'all' || tc.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans">
      
      {/* ── Sidebar ─────────────────────────────────────────── */}
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
            onClick={() => router.push('/dashboard')}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition duration-150"
          >
            <span>📊</span>
            <span>Dashboard Hub</span>
          </button>
          
          <button
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 font-medium transition duration-150"
          >
            <span>📁</span>
            <span>Test Repository</span>
          </button>
        </nav>
      </aside>

      {/* ── Workspace Area ──────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        
        <header className="h-20 bg-slate-900/50 backdrop-blur-md border-b border-slate-900 flex justify-between items-center px-8 sticky top-0 z-10">
          <div>
            <h2 className="text-lg font-bold text-slate-200">Test Cases Registry</h2>
            <p className="text-xs text-slate-500">Enterprise workspace repository for all structured & BDD test validations.</p>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setImportOpen(true)}
              className="px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-xl text-xs font-semibold text-slate-300 transition duration-150"
            >
              📥 Import Excel/CSV
            </button>
            <button
              onClick={() => setExportOpen(true)}
              className="px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-xl text-xs font-semibold text-slate-300 transition duration-150"
            >
              📤 Bulk Export
            </button>
            <button
              onClick={() => openEditor(null)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-xl text-xs font-semibold text-white transition duration-150 flex items-center space-x-1.5 shadow-lg shadow-indigo-500/20"
            >
              <span>+</span>
              <span>New Test Case</span>
            </button>
          </div>
        </header>

        {/* ── Central Repository Grid ────────────────────────── */}
        <main className="p-8 space-y-6 max-w-7xl">
          
          {/* Action grid filters */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row md:items-center gap-4">
            <div className="flex-1 relative">
              <input 
                type="text" 
                placeholder="Search by title, description or tag..." 
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 focus:outline-none rounded-xl text-xs py-3 px-4 placeholder-slate-600 text-slate-100"
              />
            </div>
            
            <div className="flex items-center space-x-3">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-xl text-xs py-3 px-4 focus:outline-none focus:border-indigo-500 font-semibold text-slate-400"
              >
                <option value="all">All Lifecycle Statuses</option>
                <option value="approved">Approved</option>
                <option value="review">Under Review</option>
                <option value="draft">Draft</option>
              </select>
            </div>
          </div>

          {/* Test cases list browser */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-850 text-xs text-slate-400 font-bold uppercase">
                    <th className="pb-3 pt-4 pl-6">ID</th>
                    <th className="pb-3 pt-4">Test Title</th>
                    <th className="pb-3 pt-4">Lifecycle</th>
                    <th className="pb-3 pt-4">Criticality</th>
                    <th className="pb-3 pt-4">Automation</th>
                    <th className="pb-3 pt-4">Format</th>
                    <th className="pb-3 pt-4 pr-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850 text-sm">
                  {filteredCases.map((tc) => (
                    <tr key={tc.id} className="hover:bg-slate-900/50 transition">
                      <td className="py-4 pl-6 font-bold text-indigo-400">{tc.id}</td>
                      <td className="py-4 max-w-sm">
                        <div className="truncate font-semibold text-slate-200">{tc.title}</div>
                        <div className="text-[11px] text-slate-500 truncate mt-0.5">{tc.description}</div>
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {tc.type_tags.map(t => (
                            <span key={t} className="text-[9px] font-semibold bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
                              {t}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          tc.status === 'approved' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                          tc.status === 'review' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-slate-800 text-slate-400'
                        }`}>
                          {tc.status}
                        </span>
                      </td>
                      <td className="py-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          tc.criticality === 'high' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-slate-850 text-slate-400'
                        }`}>
                          {tc.criticality}
                        </span>
                      </td>
                      <td className="py-4">
                        <span className="text-xs text-slate-300 font-medium capitalize">{tc.automation_flag}</span>
                      </td>
                      <td className="py-4">
                        <span className="text-xs text-slate-400 uppercase font-semibold">{tc.format_type}</span>
                      </td>
                      <td className="py-4 pr-6 text-right">
                        <button 
                          onClick={() => openEditor(tc)}
                          className="px-3 py-1.5 bg-slate-950 border border-slate-850 hover:bg-slate-800 text-xs font-semibold text-indigo-400 rounded-lg transition"
                        >
                          Open Editor
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>

        {/* ── Test Case Editor Modal ─────────────────────────── */}
        {editorOpen && (
          <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col">
              
              <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                <div>
                  <h3 className="text-lg font-bold text-slate-200">
                    {editingId ? `Edit Test Case (${editingId})` : 'Create Test Case'}
                  </h3>
                  <p className="text-xs text-slate-500">Provide structured parameters or Gherkin scripts below.</p>
                </div>
                
                {/* Gherkin Toggle Switch */}
                <div className="flex items-center space-x-3 bg-slate-950 p-1.5 rounded-xl border border-slate-850">
                  <button
                    onClick={() => setEditFormat('structured')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition duration-150 ${
                      editFormat === 'structured' ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    Structured Steps
                  </button>
                  <button
                    onClick={() => setEditFormat('bdd')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition duration-150 ${
                      editFormat === 'bdd' ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    Gherkin BDD
                  </button>
                </div>
              </div>

              {/* Editor Form */}
              <div className="p-8 space-y-6 flex-1">
                
                {/* Meta Row */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="md:col-span-2 space-y-1.5">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Test Case Title</label>
                    <input 
                      type="text" 
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      placeholder="e.g. Verify Change Request Approval Routing"
                      className="w-full bg-slate-950 border border-slate-850 focus:border-indigo-500 focus:outline-none rounded-xl text-xs py-3 px-4 text-slate-200"
                    />
                  </div>
                  
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Criticality</label>
                    <select
                      value={editCrit}
                      onChange={(e: any) => setEditCrit(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 focus:border-indigo-500 focus:outline-none rounded-xl text-xs py-3 px-4 font-semibold text-slate-400"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Lifecycle Status</label>
                    <select
                      value={editStatus}
                      onChange={(e: any) => setEditStatus(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 focus:border-indigo-500 focus:outline-none rounded-xl text-xs py-3 px-4 font-semibold text-slate-400"
                    >
                      <option value="draft">Draft</option>
                      <option value="review">Review</option>
                      <option value="approved">Approved</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Automation Flag</label>
                    <select
                      value={editAuto}
                      onChange={(e: any) => setEditAuto(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 focus:border-indigo-500 focus:outline-none rounded-xl text-xs py-3 px-4 font-semibold text-slate-400"
                    >
                      <option value="manual">Manual</option>
                      <option value="automated">Automated</option>
                      <option value="hybrid">Hybrid</option>
                    </select>
                  </div>
                </div>

                {/* Description & preconditions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Description</label>
                    <textarea 
                      rows={3}
                      value={editDesc}
                      onChange={(e) => setEditDesc(e.target.value)}
                      placeholder="Explain what regression capabilities this covers."
                      className="w-full bg-slate-950 border border-slate-850 focus:border-indigo-500 focus:outline-none rounded-xl text-xs py-3 px-4 text-slate-200"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Preconditions</label>
                    <textarea 
                      rows={3}
                      value={editPre}
                      onChange={(e) => setEditPre(e.target.value)}
                      placeholder="e.g. Change application scope active, credentials set."
                      className="w-full bg-slate-950 border border-slate-850 focus:border-indigo-500 focus:outline-none rounded-xl text-xs py-3 px-4 text-slate-200"
                    />
                  </div>
                </div>

                {/* Conditional steps view */}
                {editFormat === 'structured' ? (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Test Steps Editor</label>
                      <button
                        onClick={addStep}
                        className="text-xs font-bold text-indigo-400 hover:text-indigo-300"
                      >
                        + Add Step Row
                      </button>
                    </div>

                    <div className="space-y-3">
                      {editSteps.map((step, index) => (
                        <div key={step.id} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-start p-3 bg-slate-950 rounded-xl border border-slate-850">
                          <div className="md:col-span-1 font-bold text-xs text-slate-500 text-center pt-2.5">
                            #{step.step_number}
                          </div>
                          <div className="md:col-span-5">
                            <input 
                              type="text" 
                              value={step.action}
                              onChange={(e) => updateStep(index, 'action', e.target.value)}
                              placeholder="Action text..."
                              className="w-full bg-slate-900 border border-slate-800 rounded-lg text-xs py-2 px-3 text-slate-200"
                            />
                          </div>
                          <div className="md:col-span-5">
                            <input 
                              type="text" 
                              value={step.expected_result}
                              onChange={(e) => updateStep(index, 'expected_result', e.target.value)}
                              placeholder="Expected validation result..."
                              className="w-full bg-slate-900 border border-slate-800 rounded-lg text-xs py-2 px-3 text-slate-200"
                            />
                          </div>
                          <div className="md:col-span-1 text-center pt-1.5">
                            <button 
                              onClick={() => removeStep(index)}
                              className="text-rose-500 hover:text-rose-400 text-xs"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Gherkin BDD Script</label>
                    <textarea 
                      rows={6}
                      value={editBddScript}
                      onChange={(e) => setEditBddScript(e.target.value)}
                      placeholder="Feature: ...&#10;Scenario: ...&#10;  Given ...&#10;  When ...&#10;  Then ..."
                      className="w-full bg-slate-950 border border-slate-850 focus:border-indigo-500 focus:outline-none rounded-xl text-xs py-3 px-4 font-mono text-emerald-400"
                    />
                  </div>
                )}

                {/* General results & tags */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Expected Results Summary</label>
                    <input 
                      type="text" 
                      value={editExp}
                      onChange={(e) => setEditExp(e.target.value)}
                      placeholder="Primary validation goal."
                      className="w-full bg-slate-950 border border-slate-850 focus:border-indigo-500 focus:outline-none rounded-xl text-xs py-3 px-4 text-slate-200"
                    />
                  </div>
                  
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Tags (comma separated)</label>
                    <input 
                      type="text" 
                      value={editTagsStr}
                      onChange={(e) => setEditTagsStr(e.target.value)}
                      placeholder="e.g. servicenow, change-mgt, draft"
                      className="w-full bg-slate-950 border border-slate-850 focus:border-indigo-500 focus:outline-none rounded-xl text-xs py-3 px-4 text-slate-200"
                    />
                  </div>
                </div>

              </div>

              <div className="p-6 border-t border-slate-800 bg-slate-900/50 flex justify-end space-x-3">
                <button
                  onClick={() => setEditorOpen(false)}
                  className="px-4 py-2 border border-slate-800 hover:bg-slate-800 text-xs font-semibold rounded-xl text-slate-400 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveTestCase}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-xs font-semibold text-white rounded-xl shadow-lg shadow-indigo-500/20 transition"
                >
                  Save Test Case
                </button>
              </div>

            </div>
          </div>
        )}

        {/* ── Import Wizard Modal ────────────────────────────── */}
        {importOpen && (
          <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl flex flex-col overflow-hidden">
              
              <div className="p-6 border-b border-slate-800 bg-slate-900/50">
                <h3 className="text-lg font-bold text-slate-200">Bulk Ingestion Wizard</h3>
                
                {/* Steps progress indicator */}
                <div className="flex items-center space-x-2 mt-4 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  <span className={importStep >= 1 ? 'text-indigo-400' : ''}>1. Upload</span>
                  <span>→</span>
                  <span className={importStep >= 2 ? 'text-indigo-400' : ''}>2. Field Map</span>
                  <span>→</span>
                  <span className={importStep >= 3 ? 'text-indigo-400' : ''}>3. Validation Preview</span>
                  <span>→</span>
                  <span className={importStep >= 4 ? 'text-indigo-400' : ''}>4. Confirm</span>
                </div>
              </div>

              {/* Wizard Content */}
              <div className="p-8 flex-1">
                
                {/* Step 1: Upload */}
                {importStep === 1 && (
                  <div className="space-y-4">
                    <p className="text-xs text-slate-400">Select an Excel (.xlsx) or CSV worksheet containing test schemas to ingest into REGIQ database.</p>
                    
                    <div 
                      onClick={() => setSelectedFile('regiq_test_matrix_bulk.xlsx')}
                      className="border-2 border-dashed border-slate-800 hover:border-indigo-500 hover:bg-indigo-500/5 cursor-pointer rounded-2xl p-8 text-center transition"
                    >
                      <div className="text-4xl mb-3">📄</div>
                      {selectedFile ? (
                        <div>
                          <p className="text-xs font-bold text-slate-200">{selectedFile}</p>
                          <p className="text-[10px] text-slate-500 mt-1">Excel Spreadsheet — 524 Rows Found</p>
                        </div>
                      ) : (
                        <div>
                          <p className="text-xs font-semibold text-slate-300">Click to pick workbook sheet or drop file</p>
                          <p className="text-[10px] text-slate-500 mt-1">Supports standard Excel and CSV logs</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Step 2: Field Mapping */}
                {importStep === 2 && (
                  <div className="space-y-4">
                    <p className="text-xs text-slate-400">Map your Excel header columns to target REGIQ Database schema attributes.</p>
                    
                    <div className="space-y-3">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-semibold text-slate-400">Title Field</span>
                        <select className="bg-slate-950 border border-slate-800 rounded-lg py-1.5 px-3 text-slate-300">
                          <option value="name">name (mapped)</option>
                          <option value="title">title</option>
                        </select>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-semibold text-slate-400">Steps JSON</span>
                        <select className="bg-slate-950 border border-slate-800 rounded-lg py-1.5 px-3 text-slate-300">
                          <option value="steps_json">steps_json (mapped)</option>
                          <option value="steps">steps</option>
                        </select>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-semibold text-slate-400">Criticality</span>
                        <select className="bg-slate-950 border border-slate-800 rounded-lg py-1.5 px-3 text-slate-300">
                          <option value="criticality">criticality (mapped)</option>
                          <option value="priority">priority</option>
                        </select>
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 3: Validation Preview */}
                {importStep === 3 && (
                  <div className="space-y-4">
                    <p className="text-xs text-slate-400">Review validation checks on imported rows. Invalid cells will be skipped or corrected before saving.</p>
                    
                    <div className="space-y-3 max-h-[220px] overflow-y-auto pr-2 text-xs">
                      {importPreview.map((p) => (
                        <div key={p.row} className={`p-3 rounded-xl border flex justify-between items-center ${
                          p.status === 'valid' ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-400' : 'bg-rose-500/5 border-rose-500/20 text-rose-400'
                        }`}>
                          <div>
                            <span className="font-bold">Row {p.row}:</span>
                            <span className="ml-2 text-slate-300">{p.title || 'Blank Title'}</span>
                          </div>
                          <span className="text-[10px] font-semibold">{p.reason}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Step 4: Confirm */}
                {importStep === 4 && (
                  <div className="space-y-4 text-center">
                    <div className="text-5xl animate-bounce mb-4">🚀</div>
                    <p className="text-sm font-bold text-slate-200">Database Schema Ready!</p>
                    <p className="text-xs text-slate-400">Validated 524 valid rows from Excel file. Confirm to execute bulk transactional inserts into Postgres test_cases and motor.test_case_versions tables.</p>
                  </div>
                )}

              </div>

              <div className="p-6 border-t border-slate-800 bg-slate-900/50 flex justify-between">
                <button
                  onClick={() => {
                    if (importStep > 1) setImportStep(prev => prev - 1);
                    else setImportOpen(false);
                  }}
                  className="px-4 py-2 border border-slate-800 hover:bg-slate-800 text-xs font-semibold rounded-xl text-slate-400 transition"
                >
                  {importStep === 1 ? 'Cancel' : 'Back'}
                </button>
                
                <button
                  onClick={() => {
                    if (importStep === 1 && !selectedFile) return alert("Select a file first!");
                    if (importStep < 4) setImportStep(prev => prev + 1);
                    else runBulkImport();
                  }}
                  disabled={isImporting}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-xs font-semibold text-white rounded-xl shadow-lg shadow-indigo-500/20 transition disabled:opacity-50"
                >
                  {isImporting ? 'Ingesting...' : importStep === 4 ? 'Confirm & Ingest' : 'Next Step'}
                </button>
              </div>

            </div>
          </div>
        )}

        {/* ── Export Dialog Modal ────────────────────────────── */}
        {exportOpen && (
          <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md shadow-2xl flex flex-col overflow-hidden">
              
              <div className="p-6 border-b border-slate-800 bg-slate-900/50">
                <h3 className="text-md font-bold text-slate-200">Export Report Engine</h3>
                <p className="text-xs text-slate-500">Configure report variables and export formatting.</p>
              </div>

              <div className="p-8 space-y-6">
                
                {/* Format selection */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Target Format</label>
                  <div className="grid grid-cols-3 gap-3">
                    <button
                      onClick={() => setExportFormat('xlsx')}
                      className={`p-4 rounded-xl border text-center transition duration-150 ${
                        exportFormat === 'xlsx' ? 'bg-indigo-600/10 border-indigo-500 text-indigo-400 font-semibold' : 'border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <div className="text-2xl mb-1.5">📊</div>
                      <span className="text-[10px]">Excel (.xlsx)</span>
                    </button>
                    <button
                      onClick={() => setExportFormat('csv')}
                      className={`p-4 rounded-xl border text-center transition duration-150 ${
                        exportFormat === 'csv' ? 'bg-indigo-600/10 border-indigo-500 text-indigo-400 font-semibold' : 'border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <div className="text-2xl mb-1.5">📄</div>
                      <span className="text-[10px]">CSV Text</span>
                    </button>
                    <button
                      onClick={() => setExportFormat('pdf')}
                      className={`p-4 rounded-xl border text-center transition duration-150 ${
                        exportFormat === 'pdf' ? 'bg-indigo-600/10 border-indigo-500 text-indigo-400 font-semibold' : 'border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <div className="text-2xl mb-1.5">📕</div>
                      <span className="text-[10px]">PDF Document</span>
                    </button>
                  </div>
                </div>

                {/* Filters */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Filter Scope</label>
                  <select
                    value={exportStatus}
                    onChange={(e: any) => setExportStatus(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-850 focus:border-indigo-500 focus:outline-none rounded-xl text-xs py-3 px-4 font-semibold text-slate-400"
                  >
                    <option value="all">All Lifecycle Test Cases</option>
                    <option value="approved">Approved Active Test Cases Only</option>
                  </select>
                </div>

              </div>

              <div className="p-6 border-t border-slate-800 bg-slate-900/50 flex justify-end space-x-3">
                <button
                  onClick={() => setExportOpen(false)}
                  className="px-4 py-2 border border-slate-800 hover:bg-slate-800 text-xs font-semibold rounded-xl text-slate-400 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={runExport}
                  disabled={isExporting}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-xs font-semibold text-white rounded-xl shadow-lg shadow-indigo-500/20 transition disabled:opacity-50"
                >
                  {isExporting ? 'Building PDF/Excel...' : 'Export Reports'}
                </button>
              </div>

            </div>
          </div>
        )}

      </div>
    </div>
  );
}
