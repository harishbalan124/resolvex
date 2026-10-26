import React, { useEffect, useState } from 'react';
import { fetchAuditLogs } from '../api/audit';
import { AuditLog } from '../types/audit';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Badge } from '../components/common/Badge';
import { formatDate } from '../utils/formatters';
import { ShieldCheck, ScrollText, Filter } from 'lucide-react';

export const AuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');

  const loadAuditLogs = async () => {
    try {
      const data = await fetchAuditLogs({
        action: actionFilter || undefined,
        entity_type: entityFilter || undefined,
        limit: 100,
      });
      setLogs(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, [actionFilter, entityFilter]);

  if (loading) {
    return <LoadingSpinner label="Loading compliance audit trail..." />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <ScrollText className="w-6 h-6 text-slate-700" />
          <span>System & Governance Audit Trail</span>
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Immutable compliance ledger recording authentication, dispute creation, and human-in-the-loop review actions. Zero PII stored.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center gap-4">
        <Filter className="w-4 h-4 text-slate-400" />
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500 uppercase">Action:</span>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="text-xs font-medium rounded-lg border border-slate-300 p-2 bg-white"
          >
            <option value="">All Actions</option>
            <option value="AUTH_LOGIN_SUCCESS">AUTH_LOGIN_SUCCESS</option>
            <option value="DISPUTE_DETECTED">DISPUTE_DETECTED</option>
            <option value="RECOMMENDATION_GENERATED">RECOMMENDATION_GENERATED</option>
            <option value="RECOMMENDATION_APPROVED">RECOMMENDATION_APPROVED</option>
            <option value="RECOMMENDATION_REJECTED">RECOMMENDATION_REJECTED</option>
            <option value="COMPLAINT_CREATED">COMPLAINT_CREATED</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500 uppercase">Entity:</span>
          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            className="text-xs font-medium rounded-lg border border-slate-300 p-2 bg-white"
          >
            <option value="">All Entities</option>
            <option value="user">User</option>
            <option value="dispute">Dispute</option>
            <option value="recommendation">Recommendation</option>
            <option value="complaint">Complaint</option>
            <option value="interaction">Interaction</option>
          </select>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <th className="px-6 py-3.5">Timestamp</th>
                <th className="px-6 py-3.5">Action</th>
                <th className="px-6 py-3.5">Entity</th>
                <th className="px-6 py-3.5">Actor (User ID)</th>
                <th className="px-6 py-3.5">Sanitized Details</th>
                <th className="px-6 py-3.5 text-right">IP Address</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {logs.length > 0 ? (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-3.5 text-xs text-slate-500 font-mono">
                      {formatDate(log.created_at)}
                    </td>
                    <td className="px-6 py-3.5">
                      <Badge
                        variant={
                          log.action.includes('APPROVED')
                            ? 'success'
                            : log.action.includes('REJECTED')
                            ? 'danger'
                            : log.action.includes('DETECTED')
                            ? 'warning'
                            : 'neutral'
                        }
                        size="sm"
                      >
                        {log.action}
                      </Badge>
                    </td>
                    <td className="px-6 py-3.5 text-xs font-semibold text-slate-700">
                      {log.entity_type.toUpperCase()} #{log.entity_id || '—'}
                    </td>
                    <td className="px-6 py-3.5 text-xs text-slate-600">
                      {log.user_id ? `User #${log.user_id}` : 'System (CLI / Auto)'}
                    </td>
                    <td className="px-6 py-3.5 text-xs text-slate-600 max-w-md truncate" title={log.details || ''}>
                      {log.details || '—'}
                    </td>
                    <td className="px-6 py-3.5 text-right text-xs font-mono text-slate-400">
                      {log.ip_address || '—'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-slate-400 text-xs">
                    No audit records match the filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
