import React, { useEffect, useState } from 'react';
import { fetchCustomers, fetchCustomerDetail } from '../api/customers';
import { Customer, CustomerDetail } from '../types/customer';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { getRiskColor, getSentimentBadge, formatDate } from '../utils/formatters';
import { Search, Eye, Users, ShieldAlert } from 'lucide-react';

export const CustomersPage: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState('');

  // Drilldown modal state
  const [selectedDetail, setSelectedDetail] = useState<CustomerDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadCustomers = async () => {
    try {
      const data = await fetchCustomers({
        search: search.trim() || undefined,
        tier: tierFilter || undefined,
        limit: 100,
      });
      setCustomers(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, [tierFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadCustomers();
  };

  const handleOpenDetail = async (id: number) => {
    setDetailLoading(true);
    try {
      const detail = await fetchCustomerDetail(id);
      setSelectedDetail(detail);
    } finally {
      setDetailLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading customer directory..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Customer Portfolio</h1>
        <p className="text-sm text-slate-500 mt-1">
          Review customer health scores, sentiment history, and predictive churn risk indicators.
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, ID, or email..."
              className="w-full text-sm rounded-lg border border-slate-300 pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
          <Button variant="outline" size="md" type="submit">
            Search
          </Button>
        </form>

        <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
          <span className="text-xs font-semibold text-slate-500 uppercase">Tier:</span>
          <select
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value)}
            className="text-xs font-medium rounded-lg border border-slate-300 p-2 bg-white"
          >
            <option value="">All Tiers</option>
            <option value="Standard">Standard</option>
            <option value="Silver">Silver</option>
            <option value="Gold">Gold</option>
            <option value="Platinum">Platinum</option>
          </select>
        </div>
      </div>

      {/* Customers Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <th className="px-6 py-3.5">Customer ID</th>
                <th className="px-6 py-3.5">Name</th>
                <th className="px-6 py-3.5">Email</th>
                <th className="px-6 py-3.5">Tier</th>
                <th className="px-6 py-3.5">Churn Risk</th>
                <th className="px-6 py-3.5">Sentiment</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {customers.length > 0 ? (
                customers.map((c) => {
                  const riskInfo = c.churn_risk_score !== null && c.churn_risk_score !== undefined
                    ? getRiskColor(c.churn_risk_score)
                    : null;
                  const sentimentInfo = c.sentiment_score !== null && c.sentiment_score !== undefined
                    ? getSentimentBadge(
                        c.sentiment_score > 0.2 ? 'positive' : c.sentiment_score < -0.2 ? 'negative' : 'neutral'
                      )
                    : null;

                  return (
                    <tr key={c.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-4 font-mono font-semibold text-xs text-slate-900">
                        {c.external_id}
                      </td>
                      <td className="px-6 py-4 font-semibold text-xs text-slate-800">{c.name}</td>
                      <td className="px-6 py-4 text-xs text-slate-500">{c.email}</td>
                      <td className="px-6 py-4">
                        <Badge variant="purple" size="sm">
                          {c.tier}
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        {riskInfo ? (
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-semibold ${riskInfo.bg} ${riskInfo.text}`}
                          >
                            {((c.churn_risk_score || 0) * 100).toFixed(0)}% {riskInfo.label}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">Unscored</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {sentimentInfo ? (
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-semibold ${sentimentInfo.bg} ${sentimentInfo.text}`}
                          >
                            {sentimentInfo.label}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">Unscored</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenDetail(c.id)}
                          icon={<Eye className="w-3.5 h-3.5" />}
                        >
                          Profile
                        </Button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400 text-xs">
                    No customers match the filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Customer Detail Modal */}
      <Modal
        isOpen={!!selectedDetail}
        onClose={() => setSelectedDetail(null)}
        title={`Customer Profile: ${selectedDetail?.name} (${selectedDetail?.external_id})`}
      >
        {selectedDetail && (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200 text-xs">
              <div>
                <span className="font-semibold text-slate-500 block">Email Address:</span>
                <span className="text-slate-800">{selectedDetail.email}</span>
              </div>
              <div>
                <span className="font-semibold text-slate-500 block">Phone Number:</span>
                <span className="text-slate-800">{selectedDetail.phone || '—'}</span>
              </div>
              <div>
                <span className="font-semibold text-slate-500 block">SLA Service Tier:</span>
                <Badge variant="purple" size="sm">
                  {selectedDetail.tier}
                </Badge>
              </div>
              <div>
                <span className="font-semibold text-slate-500 block">Customer Since:</span>
                <span className="text-slate-800">{formatDate(selectedDetail.created_at)}</span>
              </div>
            </div>

            {/* Relation Counters */}
            <div className="grid grid-cols-4 gap-3 text-center">
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <div className="text-lg font-bold text-slate-900">{selectedDetail.transactions_count}</div>
                <div className="text-[10px] text-slate-500 uppercase font-medium">Transactions</div>
              </div>
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <div className="text-lg font-bold text-slate-900">{selectedDetail.interactions_count}</div>
                <div className="text-[10px] text-slate-500 uppercase font-medium">Interactions</div>
              </div>
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <div className="text-lg font-bold text-slate-900">{selectedDetail.complaints_count}</div>
                <div className="text-[10px] text-slate-500 uppercase font-medium">Complaints</div>
              </div>
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <div className="text-lg font-bold text-slate-900">{selectedDetail.disputes_count}</div>
                <div className="text-[10px] text-slate-500 uppercase font-medium">Disputes</div>
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-100">
              <Button variant="outline" size="sm" onClick={() => setSelectedDetail(null)}>
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
