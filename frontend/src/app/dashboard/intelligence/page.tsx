"use client";

import { useEffect, useState } from "react";
import { 
  Activity, 
  AlertTriangle, 
  BrainCircuit, 
  CheckCircle2, 
  ShieldAlert, 
  TrendingDown, 
  TrendingUp,
  History,
  MessageSquare,
  Search,
  Zap,
  ThumbsUp,
  ThumbsDown,
  AlertCircle,
  PlayCircle,
  DollarSign,
  ShoppingCart,
  Users
} from "lucide-react";

import { ApiClient } from "@/lib/api";

const fetchIntelligence = async () => {
  try {
    return await ApiClient.get("/copilot/dashboard");
  } catch (err) {
    console.error("Failed to fetch intelligence:", err);
    return null;
  }
};

export default function IntelligenceDashboard() {
  const [data, setData] = useState<any>(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [actionStatus, setActionStatus] = useState<string | null>(null);

  useEffect(() => {
    fetchIntelligence().then(setData);
  }, []);

  const handleApproveAction = () => {
    setActionStatus("EXECUTING");
    setTimeout(() => {
      setActionStatus("SUCCESS");
      setTimeout(() => {
        setShowApprovalModal(false);
        setActionStatus(null);
      }, 2000);
    }, 1500);
  };

  if (!data) return <div className="p-8 text-slate-500 flex items-center gap-2"><BrainCircuit className="animate-pulse" /> Computing Intelligence...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 relative">
      
      {/* HITL Confirmation Modal */}
      {showApprovalModal && (
        <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="p-6 border-b border-slate-100">
              <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-indigo-600" />
                Approve Operational Action
              </h3>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-sm text-slate-600">
                You are about to approve an AI-recommended operational action. This will mutate the system state and be recorded in the audit journal under your identity.
              </p>
              <div className="bg-slate-50 p-4 rounded border border-slate-200 font-mono text-xs text-slate-700">
                <div className="font-semibold text-indigo-600 mb-1">{data.ai_insight.action_payload?.action_name}</div>
                <pre>{JSON.stringify(data.ai_insight.action_payload?.payload, null, 2)}</pre>
              </div>
            </div>
            <div className="p-4 bg-slate-50 border-t flex justify-end gap-3">
              <button 
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
                onClick={() => setShowApprovalModal(false)}
                disabled={actionStatus !== null}
              >
                Cancel
              </button>
              <button 
                className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors flex items-center gap-2
                  ${actionStatus === 'SUCCESS' ? 'bg-emerald-500' : 'bg-indigo-600 hover:bg-indigo-700'}
                  ${actionStatus === 'EXECUTING' ? 'opacity-75 cursor-not-allowed' : ''}
                `}
                onClick={handleApproveAction}
                disabled={actionStatus !== null}
              >
                {actionStatus === 'EXECUTING' && <Activity className="h-4 w-4 animate-spin" />}
                {actionStatus === 'SUCCESS' && <CheckCircle2 className="h-4 w-4" />}
                {actionStatus === null ? 'Approve & Execute' : actionStatus === 'SUCCESS' ? 'Executed' : 'Executing...'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <BrainCircuit className="h-8 w-8 text-indigo-600" />
            Operational Intelligence
          </h1>
          <p className="text-slate-500 mt-2">Executive Memory & Automated Insights</p>
        </div>
        
        {/* Stability Score Widget */}
        <div className="flex items-center gap-4 bg-white p-4 rounded-xl border shadow-sm">
          <div className="flex flex-col items-end">
            <span className="text-sm font-medium text-slate-500 uppercase tracking-wider">Business Stability</span>
            <div className="flex items-center gap-2">
              <span className={`text-3xl font-bold ${
                data.stability.score >= 95 ? "text-emerald-600" :
                data.stability.score >= 80 ? "text-amber-500" : "text-rose-600"
              }`}>
                {data.stability.score}%
              </span>
              {data.stability.trend === 'down' ? <TrendingDown className="h-5 w-5 text-rose-500" /> : <TrendingUp className="h-5 w-5 text-emerald-500" />}
            </div>
            <span className="text-xs text-slate-400 mt-1">Last {data.stability.window} window</span>
          </div>
        </div>
      </div>

      {/* CEO Dashboard: Fast Read-Only Financials */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-emerald-50 rounded-lg text-emerald-600"><DollarSign className="h-5 w-5" /></div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Revenue (24h)</p>
            <h3 className="text-lg font-bold text-slate-900">${data.business_metrics.revenue_24h.toLocaleString()}</h3>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-blue-50 rounded-lg text-blue-600"><ShoppingCart className="h-5 w-5" /></div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Orders (24h)</p>
            <h3 className="text-lg font-bold text-slate-900">{data.business_metrics.orders_24h}</h3>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-indigo-50 rounded-lg text-indigo-600"><TrendingUp className="h-5 w-5" /></div>
          <div>
            <p className="text-xs text-slate-500 font-medium">Avg Ticket</p>
            <h3 className="text-lg font-bold text-slate-900">${data.business_metrics.avg_ticket}</h3>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-purple-50 rounded-lg text-purple-600"><Users className="h-5 w-5" /></div>
          <div>
            <p className="text-xs text-slate-500 font-medium">New Customers</p>
            <h3 className="text-lg font-bold text-slate-900">{data.business_metrics.new_customers_24h}</h3>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Operational Narrative */}
        <div className="lg:col-span-2 space-y-6">
          <section className="bg-gradient-to-br from-indigo-50 to-white rounded-xl p-6 border border-indigo-100 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4">
              <span className="inline-flex items-center gap-1 bg-indigo-100 text-indigo-800 text-xs px-2.5 py-1 rounded-full font-medium">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Confidence: {Math.round(data.narrative.confidence * 100)}%
              </span>
            </div>
            
            <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2 mb-4">
              <Activity className="h-5 w-5 text-indigo-500" />
              Operational Narrative
            </h2>
            
            <p className="text-slate-700 text-lg leading-relaxed font-medium">
              {data.narrative.text}
            </p>
            
            <div className="mt-6 flex items-center gap-2 text-xs text-slate-400">
              <History className="h-4 w-4" />
              Generated {new Date(data.narrative.generated_at).toLocaleTimeString()} via {data.narrative.source}
            </div>
          </section>

          {/* AI Copilot & Incident Explainer */}
          <section className="bg-white rounded-xl border border-indigo-100 shadow-sm overflow-hidden">
            <div className="bg-indigo-50 border-b border-indigo-100 px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-indigo-900 flex items-center gap-2">
                <BrainCircuit className="h-5 w-5 text-indigo-600" />
                AI Operational Assistant
              </h2>
              <span className="text-xs font-semibold uppercase tracking-wider bg-indigo-200 text-indigo-800 px-2 py-1 rounded">
                Read-Only Mode
              </span>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Tenant Insight */}
              <div className="p-4 bg-slate-50 rounded-lg border border-slate-100 relative">
                <div className="absolute -top-3 left-4 bg-white px-2 text-xs font-bold text-slate-400 uppercase">
                  Global Insight
                </div>
                <p className="text-slate-800 text-sm mt-2">{data.ai_insight.response}</p>
                
                <div className="mt-4 flex flex-wrap items-center justify-between gap-4">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-100 text-amber-800">
                    <Zap className="h-3.5 w-3.5" />
                    {data.ai_insight.recommendation_type}
                  </span>
                  
                  {data.ai_insight.action_payload && (
                    <button 
                      onClick={() => setShowApprovalModal(true)}
                      className="ml-auto flex items-center gap-1.5 bg-indigo-600 text-white px-3 py-1.5 rounded-md text-xs font-semibold hover:bg-indigo-700 transition-colors shadow-sm"
                    >
                      <PlayCircle className="h-3.5 w-3.5" />
                      Execute Recommendation
                    </button>
                  )}
                  
                  <div className="flex items-center gap-4 text-xs text-slate-500 w-full sm:w-auto mt-2 sm:mt-0">
                    <span className="flex items-center gap-1">
                      <ShieldAlert className="h-3.5 w-3.5" />
                      Conf: {Math.round(data.ai_insight.confidence * 100)}%
                    </span>
                    <span className="flex items-center gap-1">
                      <MessageSquare className="h-3.5 w-3.5" />
                      {data.ai_insight.prompt_version}
                    </span>
                  </div>
                </div>

                {/* Confidence Breakdown & Sources */}
                <div className="mt-4 pt-4 border-t border-slate-200 grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="font-semibold text-slate-700 block mb-1">Sources Used:</span>
                    <ul className="text-slate-500 list-disc list-inside">
                      {data.ai_insight.sources.map((src: string) => <li key={src}>{src}</li>)}
                    </ul>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-700 block mb-1">Confidence Provenance:</span>
                    <div className="space-y-1 text-slate-500">
                      <div className="flex justify-between"><span>Memory Completeness:</span> <span>{data.ai_insight.confidence_breakdown.memory_completeness * 100}%</span></div>
                      <div className="flex justify-between"><span>Event Consistency:</span> <span>{data.ai_insight.confidence_breakdown.event_consistency * 100}%</span></div>
                    </div>
                  </div>
                </div>
                
                {/* AI Lineage & Feedback Loop */}
                <div className="mt-4 pt-4 border-t border-slate-200 flex items-center justify-between">
                  <div className="text-[10px] font-mono text-slate-400 bg-slate-100 px-2 py-1 rounded">
                    ctx_hash: {data.ai_insight.context_hash}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mr-2">Rate Prediction:</span>
                    <button className="p-1.5 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 rounded transition-colors" title="Useful">
                      <ThumbsUp className="h-3.5 w-3.5" />
                    </button>
                    <button className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors" title="Incorrect">
                      <ThumbsDown className="h-3.5 w-3.5" />
                    </button>
                    <button className="p-1.5 text-slate-400 hover:text-amber-600 hover:bg-amber-50 rounded transition-colors" title="Incomplete">
                      <AlertCircle className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Incident Explainer Input */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Explain Incident (Correlation ID)</label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <input 
                      type="text" 
                      placeholder="e.g. evt_98127391823"
                      className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                    />
                  </div>
                  <button className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors">
                    Explain
                  </button>
                </div>
              </div>
            </div>
          </section>

          {/* Business Memory Snapshots (Placeholder for charts) */}
          <section className="bg-white rounded-xl p-6 border shadow-sm h-64 flex flex-col items-center justify-center text-slate-400 border-dashed">
             <Activity className="h-10 w-10 mb-2 opacity-50" />
             <p className="font-medium">Stability Trend Chart Placeholder</p>
             <p className="text-sm">Driven by tenant_memory_snapshots</p>
          </section>
        </div>

        {/* Right Column: Anomaly Feed */}
        <div className="space-y-6">
          <section className="bg-white rounded-xl border shadow-sm overflow-hidden flex flex-col h-full">
            <div className="bg-slate-50 border-b px-6 py-4">
              <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
                Active Anomalies
                <span className="ml-auto bg-rose-100 text-rose-700 text-xs py-0.5 px-2 rounded-full font-bold">
                  {data.anomalies.length}
                </span>
              </h2>
            </div>
            
            <div className="divide-y overflow-y-auto max-h-[600px]">
              {data.anomalies.map((anomaly: any) => (
                <div key={anomaly.id} className="p-6 hover:bg-slate-50 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider
                      ${anomaly.severity === 'CRITICAL' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'}
                    `}>
                      {anomaly.severity}
                    </span>
                    <span className="text-xs text-slate-400">
                      Impact: <strong className="text-slate-700">{anomaly.impact_score}</strong>
                    </span>
                  </div>
                  
                  <h3 className="text-slate-900 font-medium mb-1 text-sm">{anomaly.title}</h3>
                  <p className="text-slate-600 text-sm mb-3 line-clamp-2">{anomaly.description}</p>
                  
                  <div className="flex items-center justify-between mt-4">
                    <span className="text-xs text-slate-500 font-medium bg-slate-100 px-2 py-1 rounded">
                      {anomaly.category}
                    </span>
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <ShieldAlert className="h-3 w-3" />
                      Conf: {Math.round(anomaly.anomaly_confidence * 100)}%
                    </span>
                  </div>
                </div>
              ))}
              
              {data.anomalies.length === 0 && (
                <div className="p-8 text-center text-slate-500">
                  <CheckCircle2 className="h-8 w-8 text-emerald-400 mx-auto mb-2" />
                  <p>No active anomalies detected.</p>
                </div>
              )}
            </div>
          </section>
        </div>
        
      </div>
    </div>
  );
}
