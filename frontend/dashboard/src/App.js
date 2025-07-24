import React, { useState, useEffect } from 'react';
import {
  Users,
  TrendingUp,
  Calendar,
  Building2,
  Mail,
  Play,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock,
  Eye,
  Download,
  Filter,
  Search,
  Star,
  ExternalLink,
  Loader2
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

// Mock data for development/demo
const mockDashboardStats = {
  total_leads: 47,
  qualified_leads: 23,
  events_processed: 8,
  companies_analyzed: 156,
  outreach_generated: 18,
  average_qualification_score: 0.78
};

const mockLeads = [
  {
    id: 'lead_1',
    company_name: 'Avery Dennison Graphics Solutions',
    contact_name: 'Laura Noll',
    contact_title: 'VP of Product Development',
    qualification_score: 0.89,
    industry_alignment: 'Large-format signage and vehicle wraps specialist',
    event_context: 'ISA Sign Expo 2025',
    has_outreach: true,
    company_size: 'Large (8B+ revenue)',
    created_at: '2025-07-23T10:30:00Z'
  },
  {
    id: 'lead_2',
    company_name: 'FastSigns International',
    contact_name: 'Mike Rodriguez',
    contact_title: 'Director of Operations',
    qualification_score: 0.82,
    industry_alignment: 'Franchise signage with 700+ locations',
    event_context: 'SGIA Expo 2025',
    has_outreach: true,
    company_size: 'Large (500M+ revenue)',
    created_at: '2025-07-23T09:15:00Z'
  },
  {
    id: 'lead_3',
    company_name: '3M Commercial Graphics',
    contact_name: 'Sarah Chen',
    contact_title: 'R&D Manager',
    qualification_score: 0.91,
    industry_alignment: 'Architectural films and protective graphics',
    event_context: 'Graphics of the Americas 2025',
    has_outreach: false,
    company_size: 'Enterprise (30B+ revenue)',
    created_at: '2025-07-23T08:45:00Z'
  }
];

const mockTaskStatus = {
  current_task: 'lead_generation',
  status: 'completed',
  progress: 100,
  message: 'Lead generation process completed successfully',
  results: {
    events_found: 8,
    companies_analyzed: 156,
    qualified_leads: 23,
    outreach_generated: 18
  }
};

const App = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboardStats, setDashboardStats] = useState(mockDashboardStats);
  const [leads, setLeads] = useState(mockLeads);
  const [taskStatus, setTaskStatus] = useState(mockTaskStatus);
  const [selectedLead, setSelectedLead] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [scoreFilter, setScoreFilter] = useState(0);
  const [sortBy, setSortBy] = useState('qualification_score');

  // API functions (with fallbacks to mock data)
  const fetchDashboardStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/dashboard`);
      if (response.ok) {
        const data = await response.json();
        setDashboardStats(data);
      }
    } catch (error) {
      console.log('Using mock dashboard data');
    }
  };

  const fetchLeads = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/leads?sort_by=${sortBy}&min_score=${scoreFilter}`);
      if (response.ok) {
        const data = await response.json();
        setLeads(data.leads || mockLeads);
      }
    } catch (error) {
      console.log('Using mock leads data');
    }
  };

  const fetchTaskStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/task-status`);
      if (response.ok) {
        const data = await response.json();
        setTaskStatus(data);
      }
    } catch (error) {
      console.log('Using mock task status');
    }
  };

  // const startLeadGeneration = async () => {
  //   setIsLoading(true);
  //   try {
  //     const response = await fetch(`${API_BASE}/api/generate-leads`, {
  //       method: 'POST',
  //       headers: { 'Content-Type': 'application/json' },
  //       body: JSON.stringify({
  //         target_industries: ['graphics', 'signage', 'printing'],
  //         max_leads: 50,
  //         include_outreach: true
  //       })
  //     });
  //     if (response.ok) {
  //       // Start polling for status updates
  //       const pollStatus = setInterval(async () => {
  //         await fetchTaskStatus();
  //         if (taskStatus.status === 'completed' || taskStatus.status === 'error') {
  //           clearInterval(pollStatus);
  //           setIsLoading(false);
  //           await fetchDashboardStats();
  //           await fetchLeads();
  //         }
  //       }, 2000);
  //     }
  //   } catch (error) {
  //     console.error('Error starting lead generation:', error);
  //     setIsLoading(false);
  //   }
  // };

  const startLeadGeneration = async () => {
  setIsLoading(true);
  try {
    const response = await fetch(`${API_BASE}/api/generate-leads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_industries: ['graphics', 'signage', 'printing'],
        max_leads: 50,
        include_outreach: true
      })
    });
    if (response.ok) {
      // Start polling for status updates
      const pollStatus = setInterval(async () => {
        try {
          const statusResponse = await fetch(`${API_BASE}/api/task-status`);
          if (statusResponse.ok) {
            const statusData = await statusResponse.json();
            setTaskStatus(statusData); // <-- update progress bar
            if (statusData.status === 'completed' || statusData.status === 'error') {
              clearInterval(pollStatus);
              setIsLoading(false);
              await fetchDashboardStats();
              await fetchLeads();
            }
          }
        } catch (error) {
          clearInterval(pollStatus);
          setIsLoading(false);
        }
      }, 2000);
    }
  } catch (error) {
    console.error('Error starting lead generation:', error);
    setIsLoading(false);
  }
};

  useEffect(() => {
    fetchDashboardStats();
    fetchLeads();
    fetchTaskStatus();
  }, [sortBy, scoreFilter]);

  // Filter leads based on search term
  const filteredLeads = leads.filter(lead =>
    lead.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (lead.contact_name && lead.contact_name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const StatCard = ({ title, value, subtitle, icon: Icon, trend, color = 'blue' }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-3xl font-bold text-${color}-600 mt-1`}>{value}</p>
          {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 bg-${color}-50 rounded-lg`}>
          <Icon className={`h-6 w-6 text-${color}-600`} />
        </div>
      </div>
      {trend && (
        <div className="flex items-center mt-4 text-sm">
          <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
          <span className="text-green-600 font-medium">{trend}</span>
        </div>
      )}
    </div>
  );

  const ProgressBar = ({ progress, status, message }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Pipeline Status</h3>
        <div className="flex items-center space-x-2">
          {status === 'running' && <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />}
          {status === 'completed' && <CheckCircle className="h-5 w-5 text-green-500" />}
          {status === 'error' && <AlertCircle className="h-5 w-5 text-red-500" />}
          <span className={`text-sm font-medium capitalize ${
            status === 'completed' ? 'text-green-600' :
            status === 'error' ? 'text-red-600' : 'text-blue-600'
          }`}>
            {status}
          </span>
        </div>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
        <div
          className={`h-3 rounded-full transition-all duration-500 ${
            status === 'completed' ? 'bg-green-500' :
            status === 'error' ? 'bg-red-500' : 'bg-blue-500'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="text-sm text-gray-600">{message}</p>
      {taskStatus.results && Object.keys(taskStatus.results).length > 0 && (
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Events Found:</span>
            <span className="font-medium">{taskStatus.results.events_found || 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Companies Analyzed:</span>
            <span className="font-medium">{taskStatus.results.companies_analyzed || 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Qualified Leads:</span>
            <span className="font-medium">{taskStatus.results.qualified_leads || 0}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Outreach Generated:</span>
            <span className="font-medium">{taskStatus.results.outreach_generated || 0}</span>
          </div>
        </div>
      )}
    </div>
  );

  const LeadCard = ({ lead, onClick }) => (
    <div
      className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-all cursor-pointer hover:border-blue-200"
      onClick={() => onClick(lead)}
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{lead.company_name}</h3>
          <p className="text-sm text-gray-600">{lead.industry_alignment}</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex items-center">
            <Star className="h-4 w-4 text-yellow-500 mr-1" />
            <span className="text-sm font-semibold text-gray-900">
              {(lead.qualification_score * 100).toFixed(0)}%
            </span>
          </div>
          {lead.has_outreach && (
            <div className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
              Outreach Ready
            </div>
          )}
        </div>
      </div>
      {lead.contact_name && (
        <div className="flex items-center text-sm text-gray-600 mb-2">
          <Users className="h-4 w-4 mr-2" />
          <span>{lead.contact_name} • {lead.contact_title}</span>
        </div>
      )}
      <div className="flex items-center text-sm text-gray-600 mb-2">
        <Calendar className="h-4 w-4 mr-2" />
        <span>{lead.event_context}</span>
      </div>
      <div className="flex items-center text-sm text-gray-600">
        <Building2 className="h-4 w-4 mr-2" />
        <span>{lead.company_size}</span>
      </div>
    </div>
  );

  const LeadDetailModal = ({ lead, onClose }) => {
    if (!lead) return null;

    const mockOutreach = {
      subject_line: `Enhancing durability for ${lead.company_name}'s graphics`,
      primary_message: `Hi ${lead.contact_name},\n\nI came across ${lead.company_name} at ${lead.event_context} and was impressed by your leadership in the graphics industry.\n\nAt DuPont, our Tedlar protective films help companies like yours extend outdoor graphic lifespan by up to 5 years while reducing replacement costs through superior weather resistance and UV protection.\n\nGiven your focus on ${lead.industry_alignment.split(' ')[0]} solutions, I'd love to share how Tedlar could enhance your current offerings.\n\nWould you be open to a brief 15-minute conversation next week?\n\nBest regards,\nDuPont Tedlar Team`,
      personalization_elements: {
        company_reference: lead.company_name,
        role_relevance: lead.contact_title,
        event_mention: lead.event_context,
        industry_context: lead.industry_alignment
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6 border-b border-gray-200">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{lead.company_name}</h2>
                <p className="text-gray-600 mt-1">{lead.industry_alignment}</p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 text-2xl font-light"
              >
                ×
              </button>
            </div>
          </div>
          <div className="p-6 space-y-6">
            {/* Lead Score */}
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-blue-900 font-semibold">Qualification Score</span>
                <div className="flex items-center">
                  <Star className="h-5 w-5 text-yellow-500 mr-2" />
                  <span className="text-2xl font-bold text-blue-900">
                    {(lead.qualification_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Contact Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Contact Information</h3>
                <div className="space-y-2">
                  <div className="flex items-center">
                    <Users className="h-4 w-4 text-gray-500 mr-2" />
                    <span>{lead.contact_name || 'Contact name pending'}</span>
                  </div>
                  {/* <div className="flex items-center">
                    <span className="text-gray-500 mr-2">Role:</span>
                    <span>{lead.contact_title || 'Title pending'}</span>
                  </div>
                  <div className="flex items-center">
                    <ExternalLink className="h-4 w-4 text-gray-500 mr-2" />
                    <span className="text-blue-600">LinkedIn Profile Available</span>
                  </div> */}
                  <div className="flex items-center">
                    <ExternalLink className="h-4 w-4 text-gray-500 mr-2" />
                    {lead.contact_linkedin ? (
                      <a
                        href={lead.contact_linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 underline"
                      >
                        {lead.contact_name || 'View LinkedIn'}
                      </a>
                    ) : (
                      <span className="text-gray-600">LinkedIn not available</span>
                    )}
                  </div>
                </div>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Company Details</h3>
                <div className="space-y-2">
                  <div className="flex items-center">
                    <Building2 className="h-4 w-4 text-gray-500 mr-2" />
                    <span>{lead.company_size}</span>
                  </div>
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 text-gray-500 mr-2" />
                    <span>{lead.event_context}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Industry Alignment */}
            <div className="bg-blue-50 rounded-lg p-4 mb-6">
              <div className="flex items-center justify-between">
                <span className="text-blue-900 font-semibold">Qualification Score</span>
                <div className="flex items-center">
                  <Star className="h-5 w-5 text-yellow-500 mr-2" />
                  <span className="text-2xl font-bold text-blue-900">
                    {(lead.qualification_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              {lead.qualification_reasons && lead.qualification_reasons.length > 0 && (
                <div className="mt-4">
                  <span className="text-blue-900 font-semibold">Rationale:</span>
                  <ul className="list-disc ml-6 mt-2 text-blue-800 text-sm">
                    {lead.qualification_reasons.map((reason, idx) => (
                      <li key={idx}>{reason}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Outreach Message */}
            {lead.has_outreach && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Generated Outreach</h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Subject Line:</label>
                    <p className="mt-1 text-gray-900">{mockOutreach.subject_line}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Message:</label>
                    <div className="mt-1 whitespace-pre-wrap text-gray-900 bg-white rounded border p-3">
                      {mockOutreach.primary_message}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Personalization Elements:</label>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {Object.entries(mockOutreach.personalization_elements).map(([key, value]) => (
                        <span key={key} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                          {key.replace('_', ' ')}: {value}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          title="Total Leads"
          value={dashboardStats.total_leads}
          subtitle="Companies identified"
          icon={Users}
          color="blue"
        />
        <StatCard
          title="Qualified Leads"
          value={dashboardStats.qualified_leads}
          subtitle={`${((dashboardStats.qualified_leads / dashboardStats.total_leads) * 100).toFixed(0)}% qualification rate`}
          icon={CheckCircle}
          color="green"
        />
        <StatCard
          title="Avg. Score"
          value={`${(dashboardStats.average_qualification_score * 100).toFixed(0)}%`}
          subtitle="Lead quality"
          icon={Star}
          color="yellow"
        />
        <StatCard
          title="Events Processed"
          value={dashboardStats.events_processed}
          subtitle="Industry events scraped"
          icon={Calendar}
          color="purple"
        />
        <StatCard
          title="Companies Analyzed"
          value={dashboardStats.companies_analyzed}
          subtitle="Total companies reviewed"
          icon={Building2}
          color="indigo"
        />
        <StatCard
          title="Outreach Generated"
          value={dashboardStats.outreach_generated}
          subtitle="AI-personalized messages"
          icon={Mail}
          color="pink"
        />
      </div>

      {/* Pipeline Status */}
      <ProgressBar
        progress={taskStatus.progress}
        status={taskStatus.status}
        message={taskStatus.message}
      />

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <button
          onClick={startLeadGeneration}
          disabled={isLoading || taskStatus.status === 'running'}
          className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? (
            <Loader2 className="h-5 w-5 mr-2 animate-spin" />
          ) : (
            <Play className="h-5 w-5 mr-2" />
          )}
          {isLoading ? 'Processing...' : 'Start Lead Generation'}
        </button>
        <button
          onClick={() => {
            fetchDashboardStats();
            fetchLeads();
            fetchTaskStatus();
          }}
          className="flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          <RefreshCw className="h-5 w-5 mr-2" />
          Refresh Data
        </button>
      </div>
    </div>
  );

  const renderLeads = () => (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="h-5 w-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search leads..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <select
              value={scoreFilter}
              onChange={(e) => setScoreFilter(parseFloat(e.target.value))}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value={0}>All Scores</option>
              <option value={0.5}>50%+ Score</option>
              <option value={0.7}>70%+ Score</option>
              <option value={0.8}>80%+ Score</option>
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="qualification_score">Sort by Score</option>
              <option value="company_name">Sort by Company</option>
              <option value="created_at">Sort by Date</option>
            </select>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Filter className="h-4 w-4" />
            <span>{filteredLeads.length} leads found</span>
          </div>
        </div>
      </div>

      {/* Leads Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredLeads.map((lead) => (
          <LeadCard
            key={lead.id}
            lead={lead}
            onClick={setSelectedLead}
          />
        ))}
      </div>

      {filteredLeads.length === 0 && (
        <div className="text-center py-12">
          <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No leads found</h3>
          <p className="text-gray-600">Try adjusting your filters or start a new lead generation process.</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <TrendingUp className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-4">
                <h1 className="text-2xl font-bold text-gray-900">Instalily AI</h1>
                <p className="text-sm text-gray-600">Lead Generation & Outreach for DuPont Tedlar</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-900">
                <Download className="h-5 w-5 mr-2" />
                Export
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'dashboard'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('leads')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'leads'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Leads ({leads.length})
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'leads' && renderLeads()}
      </main>

      {/* Lead Detail Modal */}
      {selectedLead && (
        <LeadDetailModal
          lead={selectedLead}
          onClose={() => setSelectedLead(null)}
        />
      )}
    </div>
  );
};

export default App;