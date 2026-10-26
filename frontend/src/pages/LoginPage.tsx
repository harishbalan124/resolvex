import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Button } from '../components/common/Button';
import { ShieldAlert, Lock, Mail, ArrowRight } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('admin@resolvex.internal');
  const [password, setPassword] = useState('AdminSecure123!');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail || 'Authentication failed. Please verify your email and password.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-slate-800/10 p-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="w-12 h-12 bg-sky-600 rounded-xl mx-auto flex items-center justify-center text-white font-bold text-2xl shadow-lg shadow-sky-500/20 mb-3">
          R
        </div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">ResolveX</h1>
        <p className="text-xs text-slate-500 mt-1">
          Enterprise Customer Intelligence & Autonomous Dispute Resolution
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            Work Email
          </label>
          <div className="relative">
            <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full text-sm rounded-lg border border-slate-300 pl-10 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white"
              placeholder="agent@company.com"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">
            Password
          </label>
          <div className="relative">
            <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full text-sm rounded-lg border border-slate-300 pl-10 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-sky-500 bg-white"
              placeholder="••••••••"
            />
          </div>
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full mt-2"
          isLoading={isLoading}
          icon={<ArrowRight className="w-4 h-4" />}
        >
          Sign In to Portal
        </Button>
      </form>

      {/* Quick Demo Credentials helper */}
      <div className="mt-6 pt-6 border-t border-slate-100 text-center">
        <span className="text-[11px] text-slate-400 block mb-2">Seeded Local Administrator Credentials:</span>
        <button
          type="button"
          onClick={() => {
            setEmail('admin@resolvex.internal');
            setPassword('AdminSecure123!');
          }}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-sky-600 hover:text-sky-700 bg-sky-50 hover:bg-sky-100 px-3 py-1.5 rounded-lg border border-sky-100 transition-colors"
        >
          <span>Use admin@resolvex.internal</span>
        </button>
      </div>
    </div>
  );
};
