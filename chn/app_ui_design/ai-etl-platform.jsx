import React, { useState } from 'react';
import { Activity, Bot, BookOpen, Shield, Database, Play, Pause, CheckCircle, AlertCircle, Settings, Search, Plus, Zap, GitBranch, Clock, TrendingUp, Users, FileText, Cloud, Server, AlertTriangle, ArrowRight } from 'lucide-react';

const AIETLPlatform = () => {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedSource, setSelectedSource] = useState(null);
  const [chatInput, setChatInput] = useState('');

  // Mock data - Healthcare focused
  const agents = [
    { 
      id: 1, 
      name: 'FHIR Data Ingestor', 
      status: 'active', 
      skills: ['fhir-connector', 'hl7-parser', 'delta-writer'],
      lastRun: '2 mins ago',
      successRate: 98.5,
      tasksCompleted: 1247,
      databricksFeature: 'Auto Loader + Delta Lake'
    },
    { 
      id: 2, 
      name: 'Clinical Analytics Pipeline', 
      status: 'active', 
      skills: ['omop-transform', 'quality-checks', 'workflows-orchestrate'],
      lastRun: '15 mins ago',
      successRate: 99.2,
      tasksCompleted: 892,
      databricksFeature: 'Databricks Workflows'
    },
    { 
      id: 3, 
      name: 'Patient Monitoring Agent', 
      status: 'idle', 
      skills: ['lakehouse-monitor', 'anomaly-detection', 'alerts'],
      lastRun: '1 hour ago',
      successRate: 97.8,
      tasksCompleted: 3421,
      databricksFeature: 'Lakehouse Monitoring'
    },
    { 
      id: 4, 
      name: 'Claims Processing Agent', 
      status: 'running', 
      skills: ['schema-evolution', 'unity-catalog-sync', 'sql-transform'],
      lastRun: 'running',
      successRate: 96.5,
      tasksCompleted: 654,
      databricksFeature: 'Unity Catalog + Databricks SQL'
    }
  ];

  // Federated sources with performance metrics
  const federatedSources = [
    {
      id: 1,
      name: 'Epic EHR (Snowflake)',
      type: 'Lakehouse Federation',
      platform: 'Snowflake',
      status: 'connected',
      queryCount: 12453,
      avgLatency: 2.3,
      costPerQuery: 0.08,
      dataVolume: '847 GB',
      recommendation: 'Consider materialization',
      hotTables: ['patient_encounters', 'lab_results', 'medications'],
      trend: 'increasing'
    },
    {
      id: 2,
      name: 'Cerner Claims DB',
      type: 'Lakehouse Federation',
      platform: 'PostgreSQL',
      status: 'connected',
      queryCount: 3421,
      avgLatency: 0.8,
      costPerQuery: 0.03,
      dataVolume: '234 GB',
      recommendation: 'Keep federated',
      hotTables: ['claims', 'payments'],
      trend: 'stable'
    },
    {
      id: 3,
      name: 'FHIR Server (Azure)',
      type: 'Lakehouse Federation',
      platform: 'Azure SQL',
      status: 'connected',
      queryCount: 8932,
      avgLatency: 4.1,
      costPerQuery: 0.15,
      dataVolume: '1.2 TB',
      recommendation: 'High priority - Materialize',
      hotTables: ['observations', 'conditions', 'patient'],
      trend: 'increasing'
    },
    {
      id: 4,
      name: 'Lab Results (LIMS)',
      type: 'Lakehouse Federation',
      platform: 'MySQL',
      status: 'warning',
      queryCount: 15621,
      avgLatency: 5.8,
      costPerQuery: 0.22,
      dataVolume: '456 GB',
      recommendation: 'Performance issues - Materialize now',
      hotTables: ['test_results', 'reference_ranges'],
      trend: 'increasing'
    },
    {
      id: 5,
      name: 'Patient Portal (MongoDB)',
      type: 'Lakehouse Federation',
      platform: 'MongoDB',
      status: 'connected',
      queryCount: 1823,
      avgLatency: 1.2,
      costPerQuery: 0.04,
      dataVolume: '89 GB',
      recommendation: 'Keep federated',
      hotTables: ['patient_messages', 'appointments'],
      trend: 'stable'
    },
    {
      id: 6,
      name: 'Radiology PACS',
      type: 'Materialized (Delta)',
      platform: 'Delta Lake',
      status: 'optimized',
      queryCount: 23412,
      avgLatency: 0.3,
      costPerQuery: 0.01,
      dataVolume: '3.4 TB',
      recommendation: 'Already optimized',
      hotTables: ['imaging_studies', 'reports'],
      trend: 'stable'
    }
  ];

  const skills = [
    { 
      id: 1, 
      name: 'fhir-connector', 
      category: 'Ingestion',
      description: 'Connect to FHIR APIs and ingest patient resources using Auto Loader',
      usedBy: 3,
      parameters: ['fhir_endpoint', 'resource_types', 'delta_table_path'],
      databricksFeature: 'Auto Loader, Delta Lake'
    },
    { 
      id: 2, 
      name: 'quality-checks', 
      category: 'Quality',
      description: 'Profile healthcare data and apply HEDIS/CMS quality measures',
      usedBy: 5,
      parameters: ['quality_measures', 'threshold', 'expectations_suite'],
      databricksFeature: 'Lakehouse Monitoring, Great Expectations'
    },
    { 
      id: 3, 
      name: 'omop-transform', 
      category: 'Transformation',
      description: 'Transform EHR data to OMOP Common Data Model format',
      usedBy: 4,
      parameters: ['source_cdm', 'omop_version', 'vocab_path'],
      databricksFeature: 'Databricks SQL, Delta Lake'
    },
    { 
      id: 4, 
      name: 'delta-writer', 
      category: 'Storage',
      description: 'Write optimized Delta tables with Z-ordering and partitioning',
      usedBy: 6,
      parameters: ['partition_columns', 'z_order_columns', 'optimize_schedule'],
      databricksFeature: 'Delta Lake, Liquid Clustering'
    },
    { 
      id: 5, 
      name: 'lakehouse-monitor', 
      category: 'Observability',
      description: 'Monitor data quality, drift, and pipeline health with alerts',
      usedBy: 3,
      parameters: ['metrics', 'baseline_table', 'alert_webhooks'],
      databricksFeature: 'Lakehouse Monitoring'
    },
    { 
      id: 6, 
      name: 'workflows-orchestrate', 
      category: 'Workflow',
      description: 'Orchestrate multi-step pipelines with Databricks Workflows',
      usedBy: 4,
      parameters: ['job_clusters', 'dependencies', 'retry_policy'],
      databricksFeature: 'Databricks Workflows'
    },
    { 
      id: 7, 
      name: 'unity-catalog-sync', 
      category: 'Governance',
      description: 'Sync metadata and apply governance policies via Unity Catalog',
      usedBy: 5,
      parameters: ['catalog', 'schema', 'access_controls'],
      databricksFeature: 'Unity Catalog'
    },
    { 
      id: 8, 
      name: 'hl7-parser', 
      category: 'Ingestion',
      description: 'Parse HL7v2 messages and extract clinical data',
      usedBy: 2,
      parameters: ['message_types', 'segment_extraction', 'error_handling'],
      databricksFeature: 'Spark Structured Streaming'
    },
    { 
      id: 9, 
      name: 'federation-query', 
      category: 'Data Access',
      description: 'Query external databases in-place using Lakehouse Federation',
      usedBy: 7,
      parameters: ['connection', 'tables', 'pushdown_predicates'],
      databricksFeature: 'Lakehouse Federation'
    }
  ];

  const recentActivity = [
    { id: 1, agent: 'FHIR Data Ingestor', action: 'Ingested 12.4K patient records from Epic', status: 'success', time: '2 mins ago' },
    { id: 2, agent: 'Claims Processing Agent', action: 'Detected schema change in claims.adjudication', status: 'warning', time: '5 mins ago' },
    { id: 3, agent: 'Clinical Analytics Pipeline', action: 'Built OMOP observation_period Silver table', status: 'success', time: '15 mins ago' },
    { id: 4, agent: 'Patient Monitoring Agent', action: 'Anomaly detected in lab result volumes', status: 'alert', time: '1 hour ago' }
  ];

  const policies = [
    { id: 1, name: 'PHI/PII Protection (HIPAA)', type: 'Security', status: 'active', rules: 8 },
    { id: 2, name: 'Compute Cost Controls', type: 'Resource', status: 'active', rules: 5 },
    { id: 3, name: 'Data Quality Standards', type: 'Quality', status: 'active', rules: 12 },
    { id: 4, name: 'FDA/CMS Compliance', type: 'Compliance', status: 'active', rules: 15 }
  ];

  // Navigation component
  const Sidebar = () => (
    <div className="w-64 bg-slate-900 text-white p-4 flex flex-col h-screen">
      <div className="mb-8">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Zap className="text-blue-400" />
          Healthcare AI ETL
        </h1>
        <p className="text-xs text-slate-400 mt-1">Databricks Lakehouse Platform</p>
      </div>
      
      <nav className="flex-1">
        <NavItem icon={<Activity />} label="Dashboard" page="dashboard" />
        <NavItem icon={<Bot />} label="Agents" page="agents" />
        <NavItem icon={<BookOpen />} label="Skills Library" page="skills" />
        <NavItem icon={<Cloud />} label="Federation" page="federation" />
        <NavItem icon={<Database />} label="Unity Catalog" page="catalog" />
        <NavItem icon={<GitBranch />} label="Pipelines" page="pipelines" />
        <NavItem icon={<Shield />} label="Governance" page="governance" />
        <NavItem icon={<Settings />} label="Settings" page="settings" />
      </nav>

      <div className="mt-auto pt-4 border-t border-slate-700">
        <div className="flex items-center gap-3 p-2">
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            JD
          </div>
          <div className="text-sm">
            <div className="font-medium">Justin</div>
            <div className="text-xs text-slate-400">Solutions Architect</div>
          </div>
        </div>
      </div>
    </div>
  );

  const NavItem = ({ icon, label, page }) => (
    <button
      onClick={() => setCurrentPage(page)}
      className={`w-full flex items-center gap-3 px-3 py-2 rounded mb-1 transition-colors ${
        currentPage === page 
          ? 'bg-blue-600 text-white' 
          : 'text-slate-300 hover:bg-slate-800'
      }`}
    >
      {icon}
      <span>{label}</span>
    </button>
  );

  // Dashboard Page
  const DashboardPage = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-1">Dashboard</h2>
        <p className="text-slate-600">Monitor your AI-driven data pipelines</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard icon={<Bot className="text-blue-500" />} label="Active Agents" value="4" change="+2 this week" />
        <StatCard icon={<Zap className="text-green-500" />} label="Tasks Today" value="1,247" change="+18% vs yesterday" />
        <StatCard icon={<CheckCircle className="text-emerald-500" />} label="Success Rate" value="98.5%" change="+0.3% this week" />
        <StatCard icon={<Clock className="text-purple-500" />} label="Avg. Time Saved" value="4.2 hrs" change="per pipeline" />
      </div>

      {/* Natural Language Interface */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Zap className="text-blue-600" />
          Create Pipeline with Natural Language
        </h3>
        <div className="flex gap-2">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="e.g., 'Ingest FHIR patient data from Epic and transform to OMOP' or 'Monitor lab results for anomalies'"
            className="flex-1 px-4 py-3 rounded-lg border border-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2">
            <Play size={18} />
            Execute
          </button>
        </div>
        <div className="mt-3 flex gap-2 flex-wrap">
          <button className="px-3 py-1 bg-white border border-blue-300 rounded-full text-sm hover:bg-blue-50">
            Ingest Epic EHR data
          </button>
          <button className="px-3 py-1 bg-white border border-blue-300 rounded-full text-sm hover:bg-blue-50">
            Transform to OMOP CDM
          </button>
          <button className="px-3 py-1 bg-white border border-blue-300 rounded-full text-sm hover:bg-blue-50">
            Check HEDIS quality measures
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Active Agents */}
        <div className="bg-white rounded-lg border border-slate-200 p-5">
          <h3 className="font-semibold mb-4 flex items-center justify-between">
            <span>Active Agents</span>
            <button className="text-sm text-blue-600 hover:text-blue-700">View All</button>
          </h3>
          <div className="space-y-3">
            {agents.slice(0, 3).map(agent => (
              <div key={agent.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    agent.status === 'active' ? 'bg-green-500' : 
                    agent.status === 'running' ? 'bg-blue-500 animate-pulse' : 
                    'bg-slate-400'
                  }`}></div>
                  <div>
                    <div className="font-medium text-sm">{agent.name}</div>
                    <div className="text-xs text-slate-500">{agent.skills.length} skills • {agent.lastRun}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-green-600">{agent.successRate}%</div>
                  <div className="text-xs text-slate-500">success</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg border border-slate-200 p-5">
          <h3 className="font-semibold mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {recentActivity.map(activity => (
              <div key={activity.id} className="flex items-start gap-3 pb-3 border-b border-slate-100 last:border-0">
                <div className={`mt-1 ${
                  activity.status === 'success' ? 'text-green-500' :
                  activity.status === 'warning' ? 'text-yellow-500' :
                  'text-red-500'
                }`}>
                  {activity.status === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium">{activity.action}</div>
                  <div className="text-xs text-slate-500">{activity.agent} • {activity.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  // Agents Page
  const AgentsPage = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold mb-1">AI Agents</h2>
          <p className="text-slate-600">Manage your intelligent data orchestration agents</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
          <Plus size={18} />
          Create Agent
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {agents.map(agent => (
          <div 
            key={agent.id}
            onClick={() => setSelectedAgent(agent)}
            className="bg-white rounded-lg border border-slate-200 p-5 hover:border-blue-300 cursor-pointer transition-all hover:shadow-md"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Bot className="text-blue-600" size={20} />
                </div>
                <div>
                  <h3 className="font-semibold">{agent.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <div className={`w-2 h-2 rounded-full ${
                      agent.status === 'active' ? 'bg-green-500' : 
                      agent.status === 'running' ? 'bg-blue-500 animate-pulse' : 
                      'bg-slate-400'
                    }`}></div>
                    <span className="text-xs text-slate-500 capitalize">{agent.status}</span>
                  </div>
                </div>
              </div>
              <button className="text-slate-400 hover:text-slate-600">
                <Settings size={18} />
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-600">Success Rate</span>
                <span className="font-semibold text-green-600">{agent.successRate}%</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-600">Tasks Completed</span>
                <span className="font-semibold">{agent.tasksCompleted.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-600">Last Run</span>
                <span className="font-semibold">{agent.lastRun}</span>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100">
              <div className="text-xs text-blue-600 mb-2 font-medium">
                🔷 {agent.databricksFeature}
              </div>
              <div className="text-xs text-slate-500 mb-2">Equipped Skills</div>
              <div className="flex flex-wrap gap-1">
                {agent.skills.map(skill => (
                  <span key={skill} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {selectedAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setSelectedAgent(null)}>
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold">{selectedAgent.name}</h3>
              <button onClick={() => setSelectedAgent(null)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-slate-50 p-4 rounded-lg">
                  <div className="text-sm text-slate-600 mb-1">Status</div>
                  <div className="font-semibold capitalize">{selectedAgent.status}</div>
                </div>
                <div className="bg-slate-50 p-4 rounded-lg">
                  <div className="text-sm text-slate-600 mb-1">Success Rate</div>
                  <div className="font-semibold text-green-600">{selectedAgent.successRate}%</div>
                </div>
                <div className="bg-slate-50 p-4 rounded-lg">
                  <div className="text-sm text-slate-600 mb-1">Tasks</div>
                  <div className="font-semibold">{selectedAgent.tasksCompleted.toLocaleString()}</div>
                </div>
              </div>
              <div>
                <div className="text-sm font-medium mb-2">Skills Configuration</div>
                <div className="space-y-2">
                  {selectedAgent.skills.map(skillId => {
                    const skill = skills.find(s => s.name === skillId);
                    return skill ? (
                      <div key={skillId} className="flex items-center justify-between p-3 bg-slate-50 rounded">
                        <span className="font-medium">{skill.name}</span>
                        <span className="text-sm text-slate-600">{skill.category}</span>
                      </div>
                    ) : null;
                  })}
                </div>
              </div>
              <div className="flex gap-2">
                <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Configure
                </button>
                <button className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50">
                  View Logs
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  // Skills Library Page
  const SkillsPage = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold mb-1">Skills Library</h2>
          <p className="text-slate-600">Reusable capabilities for your AI agents</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
          <Plus size={18} />
          Create Skill
        </button>
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Search skills..."
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        <select className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option>All Categories</option>
          <option>Ingestion</option>
          <option>Transformation</option>
          <option>Quality</option>
          <option>Observability</option>
          <option>Workflow</option>
        </select>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {skills.map(skill => (
          <div key={skill.id} className="bg-white rounded-lg border border-slate-200 p-5 hover:border-blue-300 cursor-pointer transition-all hover:shadow-md">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <BookOpen className="text-purple-600" size={16} />
                </div>
                <span className="text-xs px-2 py-1 bg-slate-100 rounded">{skill.category}</span>
              </div>
              <div className="text-xs text-slate-500">{skill.usedBy} agents</div>
            </div>
            <h4 className="font-semibold mb-2">{skill.name}</h4>
            <p className="text-sm text-slate-600 mb-2">{skill.description}</p>
            <div className="text-xs text-blue-600 mb-3 font-medium">
              🔷 {skill.databricksFeature}
            </div>
            <div className="pt-3 border-t border-slate-100">
              <div className="text-xs text-slate-500 mb-1">Parameters</div>
              <div className="flex flex-wrap gap-1">
                {skill.parameters.map(param => (
                  <span key={param} className="text-xs px-2 py-1 bg-slate-50 rounded">
                    {param}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // Governance Page
  const GovernancePage = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-1">Governance & Policies</h2>
        <p className="text-slate-600">HIPAA-compliant controls and guardrails for AI agent operations</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {policies.map(policy => (
          <div key={policy.id} className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex items-start justify-between mb-3">
              <Shield className={`${policy.status === 'active' ? 'text-green-500' : 'text-slate-400'}`} />
              <span className={`text-xs px-2 py-1 rounded ${
                policy.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600'
              }`}>
                {policy.status}
              </span>
            </div>
            <h4 className="font-semibold mb-1">{policy.name}</h4>
            <p className="text-sm text-slate-600 mb-3">{policy.type}</p>
            <div className="text-sm">
              <span className="font-medium">{policy.rules}</span>
              <span className="text-slate-500"> rules configured</span>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="font-semibold mb-4">Policy Rules Example: PHI/PII Protection (HIPAA)</h3>
        <div className="space-y-3">
          <div className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircle className="text-green-600" size={20} />
            <div className="flex-1">
              <div className="font-medium text-sm">Never send PHI to external LLM APIs</div>
              <div className="text-xs text-slate-600">All patient data must be de-identified before AI processing outside secure environment</div>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircle className="text-green-600" size={20} />
            <div className="flex-1">
              <div className="font-medium text-sm">Require approval for production writes to patient tables</div>
              <div className="text-xs text-slate-600">Agents must get human approval before modifying Unity Catalog production schemas with PHI</div>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircle className="text-green-600" size={20} />
            <div className="flex-1">
              <div className="font-medium text-sm">Audit all agent actions with Unity Catalog</div>
              <div className="text-xs text-slate-600">Complete audit logging of operations, HIPAA-compliant retention, user attribution</div>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircle className="text-green-600" size={20} />
            <div className="flex-1">
              <div className="font-medium text-sm">Enforce row/column-level security on patient data</div>
              <div className="text-xs text-slate-600">Unity Catalog access controls ensure agents only see authorized patient populations</div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="text-amber-600 mt-1" />
          <div>
            <div className="font-medium text-amber-900 mb-1">Compliance Reminder</div>
            <div className="text-sm text-amber-800">
              All data pipelines must comply with HIPAA Security Rule. Ensure encryption at rest (Delta Lake), 
              encryption in transit (TLS), and proper access controls through Unity Catalog before deployment.
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Federation Dashboard Page
  const FederationPage = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold mb-1">Lakehouse Federation</h2>
          <p className="text-slate-600">Monitor federated sources and optimize data access patterns</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
          <Plus size={18} />
          Add Federation Source
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-2">
            <Cloud className="text-blue-500" />
            <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">Federated</span>
          </div>
          <div className="text-2xl font-bold mb-1">5</div>
          <div className="text-sm text-slate-600">Active Connections</div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-2">
            <Server className="text-green-500" />
            <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">Materialized</span>
          </div>
          <div className="text-2xl font-bold mb-1">1</div>
          <div className="text-sm text-slate-600">Delta Tables</div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="text-purple-500" />
          </div>
          <div className="text-2xl font-bold mb-1">42.3K</div>
          <div className="text-sm text-slate-600">Queries Today</div>
        </div>
        <div className="bg-white rounded-lg border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-2">
            <AlertTriangle className="text-amber-500" />
          </div>
          <div className="text-2xl font-bold mb-1">2</div>
          <div className="text-sm text-slate-600">Need Attention</div>
        </div>
      </div>

      {/* AI Insights Banner */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-5">
        <div className="flex items-start gap-3">
          <Bot className="text-purple-600 mt-1" size={24} />
          <div className="flex-1">
            <div className="font-semibold text-purple-900 mb-2">AI Recommendations</div>
            <div className="text-sm text-purple-800 mb-3">
              Based on query patterns and performance analysis, we recommend materializing 2 high-traffic federated sources. 
              Expected improvements: <span className="font-semibold">65% faster queries</span>, <span className="font-semibold">$430/month cost savings</span>.
            </div>
            <button className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700">
              Review Recommendations
            </button>
          </div>
        </div>
      </div>

      {/* Federated Sources Table */}
      <div className="bg-white rounded-lg border border-slate-200">
        <div className="p-5 border-b border-slate-200">
          <h3 className="font-semibold mb-3">Data Sources Performance</h3>
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="text"
                placeholder="Search sources..."
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <select className="px-4 py-2 border border-slate-300 rounded-lg">
              <option>All Sources</option>
              <option>Federated Only</option>
              <option>Materialized Only</option>
              <option>Performance Issues</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr className="text-left text-sm text-slate-600">
                <th className="px-5 py-3 font-medium">Source</th>
                <th className="px-5 py-3 font-medium">Type</th>
                <th className="px-5 py-3 font-medium">Queries/Day</th>
                <th className="px-5 py-3 font-medium">Avg Latency</th>
                <th className="px-5 py-3 font-medium">Cost/Query</th>
                <th className="px-5 py-3 font-medium">Data Volume</th>
                <th className="px-5 py-3 font-medium">Recommendation</th>
                <th className="px-5 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {federatedSources.map(source => (
                <tr 
                  key={source.id} 
                  className="hover:bg-slate-50 cursor-pointer"
                  onClick={() => setSelectedSource(source)}
                >
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${
                        source.status === 'optimized' ? 'bg-green-500' :
                        source.status === 'connected' ? 'bg-blue-500' :
                        'bg-amber-500'
                      }`}></div>
                      <div>
                        <div className="font-medium">{source.name}</div>
                        <div className="text-xs text-slate-500">{source.platform}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <span className={`text-xs px-2 py-1 rounded ${
                      source.type === 'Materialized (Delta)' 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-blue-100 text-blue-700'
                    }`}>
                      {source.type === 'Materialized (Delta)' ? 'Delta Lake' : 'Federation'}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{source.queryCount.toLocaleString()}</span>
                      {source.trend === 'increasing' && (
                        <TrendingUp size={14} className="text-amber-500" />
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <span className={`font-medium ${
                      source.avgLatency > 4 ? 'text-red-600' :
                      source.avgLatency > 2 ? 'text-amber-600' :
                      'text-green-600'
                    }`}>
                      {source.avgLatency}s
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    <span className={`font-medium ${
                      source.costPerQuery > 0.15 ? 'text-red-600' :
                      source.costPerQuery > 0.08 ? 'text-amber-600' :
                      'text-green-600'
                    }`}>
                      ${source.costPerQuery}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-slate-700">{source.dataVolume}</td>
                  <td className="px-5 py-4">
                    <span className={`text-xs font-medium ${
                      source.recommendation.includes('High priority') || source.recommendation.includes('now') ? 'text-red-600' :
                      source.recommendation.includes('Consider') ? 'text-amber-600' :
                      source.recommendation.includes('optimized') ? 'text-green-600' :
                      'text-slate-600'
                    }`}>
                      {source.recommendation}
                    </span>
                  </td>
                  <td className="px-5 py-4">
                    {source.type === 'Lakehouse Federation' ? (
                      <button 
                        className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 flex items-center gap-1"
                        onClick={(e) => { e.stopPropagation(); }}
                      >
                        <ArrowRight size={14} />
                        Materialize
                      </button>
                    ) : (
                      <button className="px-3 py-1 border border-slate-300 rounded text-sm hover:bg-slate-50">
                        Optimize
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Source Detail Modal */}
      {selectedSource && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setSelectedSource(null)}>
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-xl font-bold mb-1">{selectedSource.name}</h3>
                <p className="text-sm text-slate-600">{selectedSource.platform} • {selectedSource.type}</p>
              </div>
              <button onClick={() => setSelectedSource(null)} className="text-slate-400 hover:text-slate-600 text-2xl">✕</button>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-slate-50 p-4 rounded-lg">
                <div className="text-sm text-slate-600 mb-1">Daily Queries</div>
                <div className="text-2xl font-bold">{selectedSource.queryCount.toLocaleString()}</div>
              </div>
              <div className="bg-slate-50 p-4 rounded-lg">
                <div className="text-sm text-slate-600 mb-1">Avg Latency</div>
                <div className={`text-2xl font-bold ${
                  selectedSource.avgLatency > 4 ? 'text-red-600' :
                  selectedSource.avgLatency > 2 ? 'text-amber-600' :
                  'text-green-600'
                }`}>
                  {selectedSource.avgLatency}s
                </div>
              </div>
              <div className="bg-slate-50 p-4 rounded-lg">
                <div className="text-sm text-slate-600 mb-1">Cost per Query</div>
                <div className="text-2xl font-bold">${selectedSource.costPerQuery}</div>
              </div>
            </div>

            <div className="mb-6">
              <h4 className="font-semibold mb-3">Hot Tables (Most Queried)</h4>
              <div className="space-y-2">
                {selectedSource.hotTables.map((table, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <span className="font-medium">{table}</span>
                    <span className="text-sm text-slate-600">Top {idx + 1}</span>
                  </div>
                ))}
              </div>
            </div>

            {selectedSource.type === 'Lakehouse Federation' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <div className="flex items-start gap-3">
                  <Bot className="text-blue-600 mt-1" />
                  <div className="flex-1">
                    <div className="font-semibold text-blue-900 mb-2">Materialization Analysis</div>
                    <div className="text-sm text-blue-800 mb-3">
                      Based on <strong>{selectedSource.queryCount.toLocaleString()} queries/day</strong> with <strong>{selectedSource.avgLatency}s avg latency</strong>:
                    </div>
                    <ul className="text-sm text-blue-800 space-y-1 mb-3">
                      <li>• Expected latency after materialization: <strong>0.3-0.5s</strong> (80-90% faster)</li>
                      <li>• Monthly cost savings: <strong>${(selectedSource.queryCount * selectedSource.costPerQuery * 30 * 0.7).toFixed(0)}</strong></li>
                      <li>• Storage cost (Delta): <strong>~$23/month</strong> for {selectedSource.dataVolume}</li>
                      <li>• Net monthly savings: <strong>${((selectedSource.queryCount * selectedSource.costPerQuery * 30 * 0.7) - 23).toFixed(0)}</strong></li>
                    </ul>
                    <div className="flex gap-2">
                      <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                        Create Materialization Pipeline
                      </button>
                      <button className="px-4 py-2 border border-blue-300 rounded-lg hover:bg-blue-50">
                        Schedule Analysis
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <button className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50">
                View Query History
              </button>
              <button className="flex-1 px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50">
                Connection Settings
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  // Pipelines Page
  const PipelinesPage = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-1">Active Pipelines</h2>
        <p className="text-slate-600">Monitor AI-generated and managed data pipelines</p>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="flex-1">
            <div className="text-sm text-slate-600 mb-1">Pipeline: Epic FHIR to OMOP Analytics</div>
            <div className="text-lg font-semibold">Patient Clinical Data Processing</div>
            <div className="text-xs text-slate-500 mt-1">Databricks Workflow • Auto Loader • Delta Lake</div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">Running</span>
            <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">AI-Generated</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex-1 flex items-center gap-4">
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-amber-100 rounded-lg flex items-center justify-center mb-2">
                <Database className="text-amber-600" />
              </div>
              <div className="text-xs text-center">Epic FHIR<br/>Bronze</div>
            </div>
            <div className="flex-1 h-1 bg-blue-200 relative">
              <div className="absolute inset-y-0 left-0 w-3/4 bg-blue-500"></div>
            </div>
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-slate-100 rounded-lg flex items-center justify-center mb-2">
                <Zap className="text-slate-600" />
              </div>
              <div className="text-xs text-center">Quality<br/>Checks</div>
            </div>
            <div className="flex-1 h-1 bg-slate-200"></div>
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-slate-100 rounded-lg flex items-center justify-center mb-2">
                <GitBranch className="text-slate-600" />
              </div>
              <div className="text-xs text-center">OMOP<br/>Transform</div>
            </div>
            <div className="flex-1 h-1 bg-slate-200"></div>
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-emerald-100 rounded-lg flex items-center justify-center mb-2">
                <TrendingUp className="text-emerald-600" />
              </div>
              <div className="text-xs text-center">Analytics<br/>Gold</div>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-slate-200 flex items-center justify-between">
          <div className="flex gap-4 text-sm">
            <div>
              <span className="text-slate-600">Runtime:</span>
              <span className="font-medium ml-1">8m 17s</span>
            </div>
            <div>
              <span className="text-slate-600">Patient Records:</span>
              <span className="font-medium ml-1">12,431</span>
            </div>
            <div>
              <span className="text-slate-600">DBUs Used:</span>
              <span className="font-medium ml-1">3.4</span>
            </div>
            <div>
              <span className="text-slate-600">Cost:</span>
              <span className="font-medium ml-1">$0.18</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="px-3 py-1 border border-slate-300 rounded hover:bg-slate-50 text-sm">
              View Logs
            </button>
            <button className="px-3 py-1 border border-slate-300 rounded hover:bg-slate-50 text-sm">
              <Pause size={14} />
            </button>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Bot className="text-blue-600 mt-1" />
          <div>
            <div className="font-medium text-blue-900 mb-1">AI Optimization Recommendation</div>
            <div className="text-sm text-blue-800">
              This pipeline could use Liquid Clustering instead of traditional partitioning on patient_id. 
              Estimated improvements: <span className="font-medium">$67/month savings</span> and <span className="font-medium">35% faster queries</span>.
            </div>
            <button className="mt-2 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
              Apply Optimization
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const StatCard = ({ icon, label, value, change }) => (
    <div className="bg-white rounded-lg border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-3">
        {icon}
        <span className="text-xs text-slate-500">{change}</span>
      </div>
      <div className="text-2xl font-bold mb-1">{value}</div>
      <div className="text-sm text-slate-600">{label}</div>
    </div>
  );

  return (
    <div className="flex h-screen bg-slate-50 font-sans">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {currentPage === 'dashboard' && <DashboardPage />}
          {currentPage === 'agents' && <AgentsPage />}
          {currentPage === 'skills' && <SkillsPage />}
          {currentPage === 'federation' && <FederationPage />}
          {currentPage === 'governance' && <GovernancePage />}
          {currentPage === 'pipelines' && <PipelinesPage />}
          {currentPage === 'catalog' && (
            <div className="text-center py-20">
              <Database className="mx-auto mb-4 text-slate-400" size={48} />
              <h3 className="text-xl font-semibold mb-2">Unity Catalog</h3>
              <p className="text-slate-600">Unified governance for data and AI assets</p>
              <p className="text-sm text-slate-500 mt-2">Catalog browser, lineage, and access controls would go here</p>
            </div>
          )}
          {currentPage === 'settings' && (
            <div className="text-center py-20">
              <Settings className="mx-auto mb-4 text-slate-400" size={48} />
              <h3 className="text-xl font-semibold mb-2">Settings</h3>
              <p className="text-slate-600">Workspace configuration and preferences</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIETLPlatform;