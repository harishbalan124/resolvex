import React from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Badge } from '../common/Badge';
import { getRoleBadgeClass } from '../../utils/permissions';
import { ShieldCheck, LogOut, Cpu } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-sm">
      <div className="flex items-center justify-between px-6 py-3">
        {/* Brand & AI Engine Pill */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-sky-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              R
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-slate-900">Resolve<span className="text-sky-600">X</span></span>
              <span className="hidden sm:inline-block ml-2 text-xs font-medium text-slate-400 border-l border-slate-200 pl-2">
                Enterprise CX Intelligence
              </span>
            </div>
          </div>

          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-xs font-medium text-slate-600">
            <Cpu className="w-3.5 h-3.5 text-purple-600" />
            <span>LexIntel AI:</span>
            <span className="text-emerald-600 font-semibold">Active</span>
          </div>
        </div>

        {/* User Profile & Actions */}
        <div className="flex items-center gap-3">
          {user && (
            <div className="flex items-center gap-3 text-right">
              <div>
                <div className="text-xs font-semibold text-slate-900">{user.full_name}</div>
                <div className="text-[11px] text-slate-500">{user.email}</div>
              </div>
              <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${getRoleBadgeClass(user.role)}`}>
                {user.role.replace('_', ' ')}
              </span>
            </div>
          )}

          <div className="h-6 w-px bg-slate-200" />

          <button
            onClick={logout}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors border border-transparent hover:border-rose-100"
            title="Log out"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Exit</span>
          </button>
        </div>
      </div>
    </header>
  );
};
