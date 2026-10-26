import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchDisputes } from '../api/disputes';
import { fetchRecommendations } from '../api/recommendations';
import { fetchComplaints } from '../api/complaints';
import { fetchCustomers } from '../api/customers';
import { fetchEngineStatus } from '../api/analytics';
import { Dispute } from '../types/dispute';
import { Recommendation } from '../types/recommendation';
import { Complaint } from '../types/complaint';
import { Customer } from '../types/customer';
import { EngineStatus } from '../types/analytics';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { formatCurrency, formatRuleName } from '../utils/formatters';
import {
  Users,
  AlertOctagon,
  Clock,
  LifeBuoy,
  Cpu,
  ArrowRight,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

export const DashboardPage: React.FC = () => {
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [engineStatus, setEngineStatus] = useState<EngineStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [disputesData, recsData, complaintsData, customersData, statusData] =
          await Promise.all([
            fetchDisputes({ limit: 100 }),
            fetchRecommendations({ limit: 100 }),
            fetchComplaints({ limit: 100 }),
            fetchCustomers({ limit: 100 }),
            fetchEngineStatus().catch(() => null),
          ]);

        setDisputes(disputesData);
        setRecommendations(recsData);
        setComplaints(complaintsData);
        setCustomers(customersData);
        setEngineStatus(statusData);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  if (loading) {
    return <LoadingSpinner label="Compiling live enterprise metrics from database..." />;
  }

  // Calculate live metrics without hardcoding (Rule 1)
  const pendingRecommendations = recommendations.filter((r) => r.status === 'PENDING');
  const openComplaints = complaints.filter((c) => c.status !== 'RESOLVED' && c.status !== 'CLOSED');

  // Rule breakdown for chart
  const ruleCounts = disputes.reduce((acc, d) => {
    const formatted = formatRuleName(d.rule_triggered);
    acc[formatted] = (acc[formatted] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const ruleChartData = Object.entries(ruleCounts).map(([name, count]) => ({
    name,
    count,
  }));

  // Customer tier distribution
  const tierCounts = customers.reduce((acc, c) => {
    acc[c.tier] = (acc[c.tier] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const tierChartData = Object.entries(tierCounts).map(([name, value]) => ({
    name,
    value,
  }));

  const COLORS = ['#0284c7', '#8b5cf6', '#10b981', '#f59e0b'];

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Intelligence Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time customer metrics, rule-based dispute anomalies, and autonomous recommendations.
          </p>
        </div>
        {engineStatus && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border border-slate-200 shadow-sm">
            <Cpu className="w-4 h-4 text-purple-600" />
            <span className="text-xs font-semibold text-slate-700">LexIntel AI Engine:</span>
            <Badge variant={engineStatus.sentiment_model.trained ? 'success' : 'warning'} size="sm">
              {engineStatus.sentiment_model.trained ? 'Models Active' : 'Model Not Trained'}
            </Badge>
          </div>
        )}
      </div>

      {/* Urgent Pending Human Review Alert */}
      {pendingRecommendations.length > 0 && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-amber-500 text-white rounded-lg shadow-sm">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-amber-900">
                {pendingRecommendations.length} Autonomous Resolution{pendingRecommendations.length > 1 ? 's' : ''} Awaiting Human Review
              </h2>
              <p className="text-xs text-amber-700 mt-0.5">
                LexIntel AI has evaluated incoming disputes. Human approval is required before issuing credits or merchant actions.
              </p>
            </div>
          </div>
          <Link to="/disputes">
            <Button variant="primary" size="sm" icon={<ArrowRight className="w-4 h-4" />}>
              Review Queue
            </Button>
          </Link>
        </div>
      )}

      {/* Key Metric Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-medium uppercase tracking-wider">Active Customers</span>
            <Users className="w-4 h-4 text-sky-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{customers.length}</div>
          <div className="text-xs text-slate-400 mt-1">Live from database</div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-medium uppercase tracking-wider">Flagged Disputes</span>
            <AlertOctagon className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{disputes.length}</div>
          <div className="text-xs text-slate-400 mt-1">Explainable rule detections</div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-medium uppercase tracking-wider">Pending Reviews</span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-600 mt-2">
            {pendingRecommendations.length}
          </div>
          <div className="text-xs text-slate-400 mt-1">Human-in-the-loop pending</div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-medium uppercase tracking-wider">Open Complaints</span>
            <LifeBuoy className="w-4 h-4 text-purple-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{openComplaints.length}</div>
          <div className="text-xs text-slate-400 mt-1">Under investigation</div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Dispute Anomaly Rules Chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900 tracking-tight mb-1">
            Dispute Detection Rules Distribution
          </h2>
          <p className="text-xs text-slate-500 mb-6">
            Autonomous rule detections triggering explainable dispute cases.
          </p>
          <div className="h-64">
            {ruleChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={ruleChartData}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#0284c7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                No dispute anomalies recorded yet.
              </div>
            )}
          </div>
        </div>

        {/* Customer Portfolio Tiers Chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900 tracking-tight mb-1">
            Customer Account Tier Distribution
          </h2>
          <p className="text-xs text-slate-500 mb-6">
            Portfolio customer breakdown by SLA tier and account type.
          </p>
          <div className="h-64 flex items-center justify-center">
            {tierChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={tierChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {tierChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-slate-400">No customer records found.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
