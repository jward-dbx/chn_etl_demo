import React, { useState } from 'react';
import { Send, Activity, Heart, Droplet, Weight, AlertTriangle, CheckCircle, Clock, FileText, TrendingUp, TrendingDown, User, Calendar } from 'lucide-react';

const ClinicalAssistant = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your Clinical Assistant for chronic care management. I can help you review patient vitals, assess risk scores, and recommend next best actions. How can I assist you today?',
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [input, setInput] = useState('');
  const [selectedPatient] = useState({
    id: 'P-2847',
    name: 'Sarah Martinez',
    age: 67,
    conditions: ['Type 2 Diabetes', 'Hypertension'],
    lastContact: '3 days ago',
    avatar: 'SM'
  });

  // Sample vitals data
  const vitals = [
    {
      type: 'Glucose',
      value: '156 mg/dL',
      status: 'warning',
      trend: 'up',
      icon: Droplet,
      lastReading: '2 hours ago',
      target: '80-130 mg/dL'
    },
    {
      type: 'Blood Pressure',
      value: '142/88 mmHg',
      status: 'warning',
      trend: 'up',
      icon: Heart,
      lastReading: '1 day ago',
      target: '<140/90 mmHg'
    },
    {
      type: 'Weight',
      value: '178 lbs',
      status: 'normal',
      trend: 'down',
      icon: Weight,
      lastReading: '1 day ago',
      target: '170-175 lbs'
    }
  ];

  // Risk scores
  const riskScore = {
    overall: 68,
    hospitalization: 'Medium-High',
    deterioration: 'Medium',
    lastUpdated: '6 hours ago'
  };

  // Next best actions
  const nextBestActions = [
    {
      action: 'Schedule Medication Review',
      priority: 'high',
      reason: 'Glucose trending above target for 5+ days',
      dueBy: 'Within 48 hours'
    },
    {
      action: 'Nutrition Consultation',
      priority: 'medium',
      reason: 'Recent dietary pattern changes detected',
      dueBy: 'Within 1 week'
    },
    {
      action: 'BP Monitoring Check-in',
      priority: 'medium',
      reason: 'Elevated readings in last 3 measurements',
      dueBy: 'Within 72 hours'
    }
  ];

  // Recent notes
  const recentNotes = [
    {
      date: '11/07/2025',
      type: 'Phone Follow-up',
      summary: 'Patient reports difficulty maintaining diet over holidays. Discussed carb counting strategies.'
    },
    {
      date: '11/01/2025',
      type: 'Device Review',
      summary: 'Reviewed glucose monitor data. Pattern shows morning spikes, adjusted insulin timing.'
    }
  ];

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages([...messages, userMessage]);
    setInput('');

    // Simulate assistant response
    setTimeout(() => {
      const assistantMessage = {
        role: 'assistant',
        content: generateResponse(input),
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, assistantMessage]);
    }, 1000);
  };

  const generateResponse = (query) => {
    const lowerQuery = query.toLowerCase();
    if (lowerQuery.includes('glucose') || lowerQuery.includes('sugar')) {
      return "I've analyzed Sarah's glucose readings from her connected monitor. Over the past 7 days, her average glucose is 164 mg/dL, which is above her target range of 80-130 mg/dL. The data shows consistent morning spikes between 180-210 mg/dL. The Risk Stratification model indicates this pattern increases her hospitalization risk by 15%. I recommend scheduling a medication review within 48 hours to adjust her insulin regimen.";
    } else if (lowerQuery.includes('risk') || lowerQuery.includes('score')) {
      return "Sarah's current risk score is 68/100 (Medium-High). The model considers her recent glucose trends, blood pressure elevation, and medication adherence patterns. Key risk factors include: sustained hyperglycemia (5+ days), BP above target in 3/4 recent readings, and one missed medication dose last week. The Next Best Action model recommends prioritizing the medication review and BP monitoring check-in.";
    } else if (lowerQuery.includes('summary') || lowerQuery.includes('overview')) {
      return "Here's Sarah's current status: She's a 67-year-old with Type 2 Diabetes and Hypertension. Recent vitals show glucose trending high (156 mg/dL, target 80-130), BP slightly elevated (142/88), but weight is improving. Her risk score is 68 (Medium-High). Top priority: medication review due to sustained high glucose. She was last contacted 3 days ago for dietary counseling. Connected devices are transmitting normally.";
    }
    return "I've processed your query using the clinical knowledge base and patient data. Could you be more specific about what aspect of Sarah's care you'd like to explore?";
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'normal': return 'text-green-600 bg-green-50 border-green-200';
      case 'warning': return 'text-amber-600 bg-amber-50 border-amber-200';
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-700 border-red-300';
      case 'medium': return 'bg-amber-100 text-amber-700 border-amber-300';
      case 'low': return 'bg-blue-100 text-blue-700 border-blue-300';
      default: return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar - Patient Info */}
      <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
        <div className="p-6 border-b border-gray-200 bg-gradient-to-br from-blue-50 to-indigo-50">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-14 h-14 rounded-full bg-indigo-600 flex items-center justify-center text-white font-semibold text-lg">
              {selectedPatient.avatar}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">{selectedPatient.name}</h2>
              <p className="text-sm text-gray-600">ID: {selectedPatient.id}</p>
            </div>
          </div>
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span className="flex items-center">
              <User className="w-4 h-4 mr-1" />
              {selectedPatient.age} years
            </span>
            <span className="flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              {selectedPatient.lastContact}
            </span>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {selectedPatient.conditions.map((condition, i) => (
              <span key={i} className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                {condition}
              </span>
            ))}
          </div>
        </div>

        {/* Vitals Section */}
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
            <Activity className="w-4 h-4 mr-2" />
            Connected Device Vitals
          </h3>
          <div className="space-y-3">
            {vitals.map((vital, i) => (
              <div key={i} className={`p-3 rounded-lg border ${getStatusColor(vital.status)}`}>
                <div className="flex items-start justify-between mb-1">
                  <div className="flex items-center">
                    <vital.icon className="w-4 h-4 mr-2" />
                    <span className="text-xs font-medium">{vital.type}</span>
                  </div>
                  {vital.trend === 'up' ? (
                    <TrendingUp className="w-4 h-4" />
                  ) : (
                    <TrendingDown className="w-4 h-4" />
                  )}
                </div>
                <div className="text-lg font-bold">{vital.value}</div>
                <div className="text-xs mt-1 opacity-75">
                  Target: {vital.target}
                </div>
                <div className="text-xs mt-1 opacity-60">{vital.lastReading}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Score Section */}
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
            <AlertTriangle className="w-4 h-4 mr-2" />
            Risk Stratification
          </h3>
          <div className="bg-gradient-to-br from-amber-50 to-orange-50 p-4 rounded-lg border border-amber-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Overall Risk Score</span>
              <span className="text-2xl font-bold text-amber-600">{riskScore.overall}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
              <div 
                className="bg-gradient-to-r from-amber-400 to-orange-500 h-2 rounded-full"
                style={{ width: `${riskScore.overall}%` }}
              />
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-600">Hospitalization Risk:</span>
                <span className="font-semibold text-gray-900">{riskScore.hospitalization}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Deterioration Risk:</span>
                <span className="font-semibold text-gray-900">{riskScore.deterioration}</span>
              </div>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              Updated {riskScore.lastUpdated}
            </div>
          </div>
        </div>

        {/* Recent Notes */}
        <div className="p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
            <FileText className="w-4 h-4 mr-2" />
            Recent Encounter Notes
          </h3>
          <div className="space-y-2">
            {recentNotes.map((note, i) => (
              <div key={i} className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors cursor-pointer">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-gray-900">{note.type}</span>
                  <span className="text-xs text-gray-500">{note.date}</span>
                </div>
                <p className="text-xs text-gray-600 line-clamp-2">{note.summary}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Clinical Assistant</h1>
              <p className="text-sm text-gray-600">Chronic Care Management • Powered by Databricks AI</p>
            </div>
            <div className="flex items-center space-x-2">
              <span className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                <CheckCircle className="w-3 h-3 mr-1" />
                Multi-Agent Active
              </span>
            </div>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message, i) => (
            <div key={i} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3xl ${message.role === 'user' ? 'order-2' : 'order-1'}`}>
                <div className={`rounded-lg p-4 ${
                  message.role === 'user' 
                    ? 'bg-indigo-600 text-white' 
                    : 'bg-white border border-gray-200 text-gray-900'
                }`}>
                  <p className="text-sm leading-relaxed">{message.content}</p>
                  <span className={`text-xs mt-2 block ${
                    message.role === 'user' ? 'text-indigo-200' : 'text-gray-500'
                  }`}>
                    {message.timestamp}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-end space-x-3">
              <div className="flex-1">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Ask about patient vitals, risk factors, care recommendations..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                  rows="3"
                />
                <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                  <span>Press Enter to send, Shift+Enter for new line</span>
                  <span>Connected to Genie Space</span>
                </div>
              </div>
              <button
                onClick={handleSend}
                className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center space-x-2 font-medium"
              >
                <Send className="w-4 h-4" />
                <span>Send</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Next Best Actions */}
      <div className="w-96 bg-white border-l border-gray-200 overflow-y-auto">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Next Best Actions</h3>
          <p className="text-sm text-gray-600 mb-4">AI-recommended care steps</p>
          
          <div className="space-y-3">
            {nextBestActions.map((action, i) => (
              <div key={i} className="p-4 bg-white rounded-lg border-2 border-gray-200 hover:border-indigo-300 transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <span className={`px-2 py-1 rounded text-xs font-semibold uppercase border ${getPriorityColor(action.priority)}`}>
                    {action.priority} Priority
                  </span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">{action.action}</h4>
                <p className="text-sm text-gray-600 mb-3">{action.reason}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500 flex items-center">
                    <Calendar className="w-3 h-3 mr-1" />
                    {action.dueBy}
                  </span>
                  <button className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
                    Schedule →
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="font-semibold text-blue-900 mb-2 text-sm">Model Insights</h4>
            <ul className="space-y-2 text-xs text-blue-800">
              <li className="flex items-start">
                <CheckCircle className="w-3 h-3 mr-2 mt-0.5 flex-shrink-0" />
                <span>Vitals aggregation analyzed 47 device readings</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-3 h-3 mr-2 mt-0.5 flex-shrink-0" />
                <span>Risk model processed 12 clinical indicators</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-3 h-3 mr-2 mt-0.5 flex-shrink-0" />
                <span>Knowledge base referenced 8 guidelines</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClinicalAssistant;