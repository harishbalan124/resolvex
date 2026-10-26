import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
  LayoutDashboard,
  AlertOctagon,
  LifeBuoy,
  BarChart3,
  Users,
  ScrollText,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { role } = useAuth();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Disputes & Reviews', href: '/disputes', icon: AlertOctagon },
    { name: 'Complaints', href: '/complaints', icon: LifeBuoy },
    { name: 'AI & Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'Customers', href: '/customers', icon: Users },
  ];

  if (role === 'ADMIN' || role === 'ANALYST') {
    navigation.push({ name: 'Audit Logs', href: '/audit-logs', icon: ScrollText });
  }

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between py-6 flex-shrink-0 min-h-[calc(100vh-57px)]">
      <div className="space-y-6 px-4">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 px-3 mb-2">
            Navigation
          </div>
          <nav className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-sky-600 text-white shadow-sm'
                        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Role Info Footer */}
      <div className="px-6 text-xs text-slate-500">
        <div className="font-semibold text-slate-400">ResolveX System</div>
        <div>Backend AI: LexIntel 1.0</div>
      </div>
    </aside>
  );
};
