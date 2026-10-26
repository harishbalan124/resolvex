import React, { useEffect, useState } from 'react';
import { fetchComplaints, createComplaintApi, updateComplaintStatusApi } from '../api/complaints';
import { fetchCustomers } from '../api/customers';
import { Complaint } from '../types/complaint';
import { Customer } from '../types/customer';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { formatDate } from '../utils/formatters';
import { Plus, LifeBuoy, Clock, CheckCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { canManageComplaints } from '../utils/permissions';

export const ComplaintsPage: React.FC = () => {
  const { role } = useAuth();
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  // New Complaint Modal state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [customerId, setCustomerId] = useState<number | ''>('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Billing');
  const [priority, setPriority] = useState('MEDIUM');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Status update modal state
  const [statusModalComplaint, setStatusModalComplaint] = useState<Complaint | null>(null);
  const [newStatus, setNewStatus] = useState('');
  const [statusComment, setStatusComment] = useState('');

  const loadData = async () => {
    try {
      const [complaintsData, customersData] = await Promise.all([
        fetchComplaints({ limit: 100 }),
        fetchCustomers({ limit: 100 }),
      ]);
      setComplaints(complaintsData);
      setCustomers(customersData);
      if (customersData.length > 0 && customerId === '') {
        setCustomerId(customersData[0].id);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateComplaint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerId) return;
    setIsSubmitting(true);
    try {
      await createComplaintApi({
        customer_id: Number(customerId),
        title,
        description,
        category,
        priority,
      });
      setIsCreateOpen(false);
      setTitle('');
      setDescription('');
      await loadData();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!statusModalComplaint || !newStatus) return;
    setIsSubmitting(true);
    try {
      await updateComplaintStatusApi(statusModalComplaint.id, newStatus, statusComment);
      setStatusModalComplaint(null);
      setStatusComment('');
      await loadData();
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading customer service complaints and ticket timelines..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Customer Complaints</h1>
          <p className="text-sm text-slate-500 mt-1">
            Track customer inquiries, billing dispute grievances, and SLA status transitions.
          </p>
        </div>

        {canManageComplaints(role || undefined) && (
          <Button
            variant="primary"
            onClick={() => setIsCreateOpen(true)}
            icon={<Plus className="w-4 h-4" />}
          >
            Log New Ticket
          </Button>
        )}
      </div>

      {/* Complaints Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/75 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <th className="px-6 py-3.5">Ticket</th>
                <th className="px-6 py-3.5">Title & Summary</th>
                <th className="px-6 py-3.5">Category</th>
                <th className="px-6 py-3.5">Priority</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Logged Date</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {complaints.length > 0 ? (
                complaints.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4 font-mono font-semibold text-xs text-slate-900">
                      {c.ticket_number}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-semibold text-xs text-slate-900">{c.title}</div>
                      <div className="text-xs text-slate-500 max-w-sm truncate">{c.description}</div>
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant="neutral" size="sm">
                        {c.category}
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <Badge
                        variant={
                          c.priority === 'CRITICAL' || c.priority === 'HIGH' ? 'danger' : 'neutral'
                        }
                        size="sm"
                      >
                        {c.priority}
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <Badge
                        variant={
                          c.status === 'RESOLVED' || c.status === 'CLOSED'
                            ? 'success'
                            : c.status === 'OPEN'
                            ? 'primary'
                            : 'warning'
                        }
                        size="sm"
                      >
                        {c.status.replace(/_/g, ' ')}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500">{formatDate(c.created_at)}</td>
                    <td className="px-6 py-4 text-right">
                      {canManageComplaints(role || undefined) && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setStatusModalComplaint(c);
                            setNewStatus(c.status);
                          }}
                        >
                          Update Status
                        </Button>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400 text-xs">
                    No complaints found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Log Complaint Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Log Customer Complaint">
        <form onSubmit={handleCreateComplaint} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">
              Select Customer
            </label>
            <select
              value={customerId}
              onChange={(e) => setCustomerId(Number(e.target.value))}
              required
              className="w-full text-sm rounded-lg border border-slate-300 p-2.5 focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white"
            >
              {customers.map((cust) => (
                <option key={cust.id} value={cust.id}>
                  {cust.name} ({cust.external_id})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">
              Ticket Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="e.g. Unrecognized recurring invoice debit"
              className="w-full text-sm rounded-lg border border-slate-300 p-2.5 focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full text-sm rounded-lg border border-slate-300 p-2.5 bg-white"
              >
                <option value="Billing">Billing & Debits</option>
                <option value="Dispute">Transaction Dispute</option>
                <option value="Service Outage">Service Outage</option>
                <option value="Account Access">Account Access</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full text-sm rounded-lg border border-slate-300 p-2.5 bg-white"
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">
              Detailed Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              required
              placeholder="Describe customer issue, statements questioned, and customer contact timeline..."
              className="w-full text-sm rounded-lg border border-slate-300 p-2.5 focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
            <Button variant="outline" type="button" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={isSubmitting}>
              Create Ticket
            </Button>
          </div>
        </form>
      </Modal>

      {/* Update Status Modal */}
      <Modal
        isOpen={!!statusModalComplaint}
        onClose={() => setStatusModalComplaint(null)}
        title={`Update Ticket: ${statusModalComplaint?.ticket_number}`}
      >
        <form onSubmit={handleUpdateStatus} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">
              New Status
            </label>
            <select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
              required
              className="w-full text-sm rounded-lg border border-slate-300 p-2.5 bg-white"
            >
              <option value="OPEN">Open</option>
              <option value="IN_INVESTIGATION">In Investigation</option>
              <option value="PENDING_APPROVAL">Pending Approval</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">
              Transition Comment / Audit Note
            </label>
            <textarea
              value={statusComment}
              onChange={(e) => setStatusComment(e.target.value)}
              rows={3}
              placeholder="Record explanation for changing complaint status..."
              className="w-full text-sm rounded-lg border border-slate-300 p-2.5 focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
            <Button variant="outline" type="button" onClick={() => setStatusModalComplaint(null)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={isSubmitting}>
              Save Transition
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
