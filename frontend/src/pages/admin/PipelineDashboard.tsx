/**
 * Pipeline Dashboard - Visualizes the discussion generation pipeline steps
 * Route: /admin/discussion-pipeline
 */
import { useState, useRef } from 'react';
import { Play, RefreshCw, ChevronDown, ChevronRight, CheckCircle, XCircle, Clock, AlertCircle, Upload, FileText, Download } from 'lucide-react';
import { AGENTS } from '../../constants/agents';
import { ANNOTATION_TYPES } from '../../constants/annotation';

// Annotation type → agent color mapping
const getAnnotationTypeColor = (type: string) => {
  const config = ANNOTATION_TYPES[type as keyof typeof ANNOTATION_TYPES];
  if (!config) return { bg: 'bg-gray-100', text: 'text-gray-600' };
  switch (config.stance) {
    case 'instrumental': return { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' };
    case 'critical': return { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' };
    case 'aesthetic': return { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' };
    default: return { bg: 'bg-gray-100', text: 'text-gray-600', border: 'border-gray-200' };
  }
};

// Pipeline step status
type StepStatus = 'pending' | 'running' | 'complete' | 'error';

interface Annotation {
  type: string;
  text: string;
  sectionTitle: string;
  reasoning: string;
}

interface Seed {
  seedId: string;
  tensionPoint: string;
  discussionType: string;
  snippetText: string;
  sectionTitle: string;
  relevantAgents: string[];
  keywords: string[];
}

// TODO: Enable for memory-based discussions
// interface MessageAction {
//   type: string;
//   query?: string;
//   sectionId?: string;
//   annotationId?: string;
// }

interface Message {
  messageId: string;
  author: string;
  content: string;
  // action?: MessageAction;  // TODO: Enable for memory-based discussions
  annotationType?: string;
}

interface ThreadResult {
  threadId: string;
  threadType: string;
  tensionPoint: string;
  participants: string[];
  messageCount: number;
  messages?: Message[];
}

interface PhaseData {
  duration?: number;
}

interface PipelinePhase {
  name: string;
  status: StepStatus;
  startTime?: string;
  endTime?: string;
  data?: PhaseData;
  error?: string;
}

interface PipelineState {
  status: 'idle' | 'running' | 'complete' | 'error';
  currentPhase: number;
  phases: PipelinePhase[];
  annotations: Record<string, Annotation[]>;
  seeds: Seed[];
  threads: ThreadResult[];
}

interface DocumentInfo {
  documentId: string;
  title: string;
  sectionCount: number;
}

const API_BASE = 'http://localhost:8000';

// JSON 다운로드 유틸리티
const downloadJson = (data: unknown, filename: string) => {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

export function PipelineDashboard() {
  const [pipeline, setPipeline] = useState<PipelineState>({
    status: 'idle',
    currentPhase: 0,
    phases: [
      { name: 'Phase 1: Agent Annotations', status: 'pending' },
      { name: 'Phase 2: Seed Formation', status: 'pending' },
      { name: 'Phase 3-4: Thread Generation', status: 'pending' },
    ],
    annotations: {},
    seeds: [],
    threads: [],
  });

  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    annotations: true,
    seeds: true,
    threads: true,
  });

  // Track which agents have expanded annotations
  const [expandedAgents, setExpandedAgents] = useState<Record<string, boolean>>({});

  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Document state
  const [dataSource, setDataSource] = useState<'mock' | 'upload'>('mock');
  const [uploadedDocument, setUploadedDocument] = useState<DocumentInfo | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', 'pipeline_test_user');

    try {
      const response = await fetch(`${API_BASE}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Upload failed: ${response.status}`);
      }

      const data = await response.json();
      setUploadedDocument({
        documentId: data.documentId,
        title: data.title || file.name,
        sectionCount: data.parsedContent?.sections?.length || 0,
      });
      setDataSource('upload');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const runPipeline = async () => {
    setIsRunning(true);
    setError(null);

    const startTime = new Date().toISOString();

    // Reset state
    setPipeline({
      status: 'running',
      currentPhase: 1,
      phases: [
        { name: 'Phase 1: Agent Annotations', status: 'running', startTime },
        { name: 'Phase 2: Seed Formation', status: 'pending' },
        { name: 'Phase 3-4: Thread Generation', status: 'pending' },
      ],
      annotations: {},
      seeds: [],
      threads: [],
    });

    try {
      let endpoint: string;
      let options: RequestInit;

      if (dataSource === 'mock') {
        // Use mock data endpoint
        endpoint = `${API_BASE}/api/pipeline/test-with-logging`;
        options = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        };
      } else if (uploadedDocument) {
        // Use real document endpoint
        endpoint = `${API_BASE}/api/pipeline/documents/${uploadedDocument.documentId}/generate-with-logging`;
        options = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            maxAnnotationsPerAgent: 8,
            targetSeeds: 4,
            turnsPerDiscussion: 3,
          }),
        };
      } else {
        throw new Error('No document selected');
      }

      const response = await fetch(endpoint, options);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API Error: ${response.status}`);
      }

      const data = await response.json();

      // Update state with full response
      const endTime = new Date().toISOString();
      const timings = data.timings || {};

      setPipeline({
        status: 'complete',
        currentPhase: 3,
        phases: [
          {
            name: 'Phase 1: Agent Annotations',
            status: 'complete',
            startTime,
            endTime,
            data: { duration: timings.phase1 },
          },
          {
            name: 'Phase 2: Seed Formation',
            status: 'complete',
            startTime,
            endTime,
            data: { duration: timings.phase2 },
          },
          {
            name: 'Phase 3-4: Thread Generation',
            status: 'complete',
            startTime,
            endTime,
            data: { duration: timings.phase3_4 },
          },
        ],
        annotations: data.annotations || {},
        seeds: data.seeds || [],
        threads: data.threads || [],
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setPipeline((prev) => ({
        ...prev,
        status: 'error',
        phases: prev.phases.map((p) =>
          p.status === 'running' ? { ...p, status: 'error', error: 'Pipeline failed' } : p
        ),
      }));
    } finally {
      setIsRunning(false);
    }
  };

  const getStatusIcon = (status: StepStatus) => {
    switch (status) {
      case 'pending':
        return <Clock size={16} className="text-gray-400" />;
      case 'running':
        return <RefreshCw size={16} className="text-blue-500 animate-spin" />;
      case 'complete':
        return <CheckCircle size={16} className="text-green-500" />;
      case 'error':
        return <XCircle size={16} className="text-red-500" />;
    }
  };

  const getAgentColor = (agentId: string) => {
    return AGENTS[agentId as keyof typeof AGENTS]?.color || '#6B7280';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Pipeline Dashboard</h1>
            <p className="text-sm text-gray-500 mt-1">Discussion Generation Pipeline Debugger</p>
          </div>
          <div className="flex items-center gap-2">
            {pipeline.status === 'complete' && (
              <button
                onClick={() => downloadJson({
                  annotations: pipeline.annotations,
                  seeds: pipeline.seeds,
                  threads: pipeline.threads,
                  exportedAt: new Date().toISOString(),
                }, `pipeline-results-${Date.now()}.json`)}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                <Download size={16} />
                Export All
              </button>
            )}
            <button
              onClick={runPipeline}
              disabled={isRunning || (dataSource === 'upload' && !uploadedDocument)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRunning ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play size={16} />
                  Run Pipeline
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto p-6 space-y-6">
        {/* Data Source Selection */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Data Source</h2>

          <div className="flex gap-4 mb-4">
            <button
              onClick={() => setDataSource('mock')}
              className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                dataSource === 'mock'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-3">
                <FileText size={24} className={dataSource === 'mock' ? 'text-blue-500' : 'text-gray-400'} />
                <div className="text-left">
                  <p className="font-medium text-gray-900">Mock Data</p>
                  <p className="text-sm text-gray-500">Use built-in test document</p>
                </div>
              </div>
            </button>

            <button
              onClick={() => setDataSource('upload')}
              className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                dataSource === 'upload'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-3">
                <Upload size={24} className={dataSource === 'upload' ? 'text-blue-500' : 'text-gray-400'} />
                <div className="text-left">
                  <p className="font-medium text-gray-900">Upload PDF</p>
                  <p className="text-sm text-gray-500">Test with your own document</p>
                </div>
              </div>
            </button>
          </div>

          {/* Upload Area */}
          {dataSource === 'upload' && (
            <div className="border-t border-gray-200 pt-4 mt-4">
              {uploadedDocument ? (
                <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-3">
                    <CheckCircle size={20} className="text-green-500" />
                    <div>
                      <p className="font-medium text-gray-900">{uploadedDocument.title}</p>
                      <p className="text-sm text-gray-500">
                        {uploadedDocument.sectionCount} sections · ID: {uploadedDocument.documentId}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Change
                  </button>
                </div>
              ) : (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-gray-400 transition-colors"
                >
                  {isUploading ? (
                    <div className="flex flex-col items-center gap-2">
                      <RefreshCw size={32} className="text-gray-400 animate-spin" />
                      <p className="text-gray-600">Uploading and parsing...</p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-2">
                      <Upload size={32} className="text-gray-400" />
                      <p className="text-gray-600">Click to upload PDF</p>
                      <p className="text-sm text-gray-400">or drag and drop</p>
                    </div>
                  )}
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                className="hidden"
              />
            </div>
          )}
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle size={20} className="text-red-500 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-800">Pipeline Error</p>
              <p className="text-sm text-red-600 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Pipeline Progress */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Pipeline Progress</h2>
          <div className="space-y-3">
            {pipeline.phases.map((phase, index) => (
              <div
                key={index}
                className={`flex items-center gap-3 p-3 rounded-lg ${
                  phase.status === 'running' ? 'bg-blue-50' : phase.status === 'complete' ? 'bg-green-50' : 'bg-gray-50'
                }`}
              >
                {getStatusIcon(phase.status)}
                <span className="font-medium text-gray-900">{phase.name}</span>
                {(phase.status === 'running' || phase.data?.duration) && (
                  <span className="text-xs text-gray-500 ml-auto">
                    {phase.status === 'running' ? 'Running...' : `${phase.data?.duration}s`}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Phase 1: Annotations */}
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="flex items-center p-4">
            <button
              onClick={() => toggleSection('annotations')}
              className="flex items-center gap-2 flex-1 text-left hover:bg-gray-50 -m-2 p-2 rounded"
            >
              {expandedSections.annotations ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
              <span className="font-medium text-gray-900">Phase 1: Agent Annotations</span>
            </button>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">
                {Object.values(pipeline.annotations).flat().length} annotations
              </span>
              {Object.keys(pipeline.annotations).length > 0 && (
                <button
                  onClick={() => downloadJson(pipeline.annotations, `annotations-${Date.now()}.json`)}
                  className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                  title="Download annotations"
                >
                  <Download size={16} />
                </button>
              )}
            </div>
          </div>

          {expandedSections.annotations && Object.keys(pipeline.annotations).length > 0 && (
            <div className="border-t border-gray-200 p-4 space-y-4">
              {Object.entries(pipeline.annotations).map(([agentId, annotations]) => (
                <div key={agentId}>
                  <div className="flex items-center gap-2 mb-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getAgentColor(agentId) }}
                    />
                    <span className="font-medium text-gray-900 capitalize">{agentId}</span>
                    <span className="text-sm text-gray-500">({annotations.length} annotations)</span>
                  </div>
                  <div className="ml-5 space-y-2">
                    {(expandedAgents[agentId] ? annotations : annotations.slice(0, 3)).map((ann, i) => (
                      <div key={i} className="text-sm p-2 bg-gray-50 rounded border border-gray-100">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getAnnotationTypeColor(ann.type).bg} ${getAnnotationTypeColor(ann.type).text}`}>
                            {ann.type}
                          </span>
                          <span className="text-gray-500">{ann.sectionTitle}</span>
                        </div>
                        <p className="text-gray-700 italic">"{ann.text?.slice(0, 150)}..."</p>
                        <p className="text-gray-600 mt-1">{ann.reasoning}</p>
                      </div>
                    ))}
                    {annotations.length > 3 && (
                      <button
                        onClick={() => setExpandedAgents(prev => ({ ...prev, [agentId]: !prev[agentId] }))}
                        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                      >
                        {expandedAgents[agentId]
                          ? 'Show less'
                          : `Show all ${annotations.length} annotations`}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Phase 2: Seeds */}
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="flex items-center p-4">
            <button
              onClick={() => toggleSection('seeds')}
              className="flex items-center gap-2 flex-1 text-left hover:bg-gray-50 -m-2 p-2 rounded"
            >
              {expandedSections.seeds ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
              <span className="font-medium text-gray-900">Phase 2: Discussion Seeds</span>
            </button>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">{pipeline.seeds.length} seeds</span>
              {pipeline.seeds.length > 0 && (
                <button
                  onClick={() => downloadJson(pipeline.seeds, `seeds-${Date.now()}.json`)}
                  className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                  title="Download seeds"
                >
                  <Download size={16} />
                </button>
              )}
            </div>
          </div>

          {expandedSections.seeds && pipeline.seeds.length > 0 && (
            <div className="border-t border-gray-200 p-4 space-y-3">
              {pipeline.seeds.map((seed, i) => (
                <div key={seed.seedId || i} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                      {seed.discussionType}
                    </span>
                    <span className="text-gray-500 text-sm">{seed.sectionTitle}</span>
                    <div className="flex gap-1 ml-auto">
                      {seed.relevantAgents?.map((agentId) => (
                        <div
                          key={agentId}
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: getAgentColor(agentId) }}
                          title={agentId}
                        />
                      ))}
                    </div>
                  </div>
                  <p className="font-medium text-gray-900">{seed.tensionPoint}</p>
                  <p className="text-sm text-gray-600 italic mt-1">"{seed.snippetText?.slice(0, 150)}..."</p>
                  <div className="flex gap-1 mt-2">
                    {seed.keywords?.map((kw) => (
                      <span key={kw} className="px-2 py-0.5 bg-gray-200 rounded text-xs text-gray-600">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Phase 3-4: Threads */}
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="flex items-center p-4">
            <button
              onClick={() => toggleSection('threads')}
              className="flex items-center gap-2 flex-1 text-left hover:bg-gray-50 -m-2 p-2 rounded"
            >
              {expandedSections.threads ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
              <span className="font-medium text-gray-900">Phase 3-4: Generated Threads</span>
            </button>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">{pipeline.threads.length} threads</span>
              {pipeline.threads.length > 0 && (
                <button
                  onClick={() => downloadJson(pipeline.threads, `threads-${Date.now()}.json`)}
                  className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                  title="Download threads"
                >
                  <Download size={16} />
                </button>
              )}
            </div>
          </div>

          {expandedSections.threads && pipeline.threads.length > 0 && (
            <div className="border-t border-gray-200 p-4 space-y-4">
              {pipeline.threads.map((thread) => (
                <div key={thread.threadId} className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                  <div className="flex items-center gap-2 mb-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        thread.threadType === 'discussion'
                          ? 'bg-purple-100 text-purple-700'
                          : 'bg-gray-200 text-gray-700'
                      }`}
                    >
                      {thread.threadType}
                    </span>
                    <div className="flex gap-1">
                      {thread.participants?.map((agentId) => (
                        <div
                          key={agentId}
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: getAgentColor(agentId) }}
                          title={agentId}
                        />
                      ))}
                    </div>
                    <span className="text-sm text-gray-500 ml-auto">{thread.messageCount} messages</span>
                  </div>
                  <p className="font-medium text-gray-900 mb-3">{thread.tensionPoint}</p>

                  {/* Messages */}
                  {thread.messages && thread.messages.length > 0 && (
                    <div className="space-y-2 mt-3 pt-3 border-t border-gray-200">
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Messages</p>
                      {thread.messages.map((msg, idx) => (
                        <div
                          key={msg.messageId || idx}
                          className="flex gap-3 p-2 bg-white rounded border border-gray-100"
                        >
                          <div
                            className="w-2 h-2 rounded-full shrink-0 mt-2"
                            style={{ backgroundColor: getAgentColor(msg.author) }}
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <p className="text-xs font-medium text-gray-500 capitalize">{msg.author}</p>
                              {msg.annotationType && (
                                <span className={`px-1.5 py-0.5 rounded text-xs ${getAnnotationTypeColor(msg.annotationType).bg} ${getAnnotationTypeColor(msg.annotationType).text}`}>
                                  {msg.annotationType}
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-700">{msg.content}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
