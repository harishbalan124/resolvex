import { UserRole } from '../types/auth';

export function canManageUsers(role?: UserRole): boolean {
  return role === 'ADMIN';
}

export function canReviewRecommendations(role?: UserRole): boolean {
  return role === 'ADMIN' || role === 'SUPPORT_AGENT';
}

export function canManageComplaints(role?: UserRole): boolean {
  return role === 'ADMIN' || role === 'SUPPORT_AGENT';
}

export function isAnalyst(role?: UserRole): boolean {
  return role === 'ANALYST';
}

export function getRoleBadgeClass(role?: UserRole): string {
  switch (role) {
    case 'ADMIN':
      return 'bg-purple-100 text-purple-800 border-purple-200';
    case 'SUPPORT_AGENT':
      return 'bg-blue-100 text-blue-800 border-blue-200';
    case 'ANALYST':
      return 'bg-amber-100 text-amber-800 border-amber-200';
    default:
      return 'bg-slate-100 text-slate-800 border-slate-200';
  }
}
