import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  GraduationCap,
  BookOpen,
  FileSpreadsheet,
  ShieldAlert,
  Sparkles,
  FileCheck,
  BarChart3,
  LogOut,
  School as SchoolIcon,
  CheckCircle,
  Layers,
  FileText,
} from 'lucide-react';

export const DashboardLayout: React.FC = () => {
  const { user, school, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <div className="flex h-screen bg-slate-50 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col border-r border-slate-800">
        {/* Brand header */}
        <div className="p-5 border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              M
            </div>
            <div>
              <h1 className="font-bold text-white text-lg tracking-tight">Mind</h1>
              <p className="text-xs text-slate-400">Better Learning</p>
            </div>
          </div>
          {school ? (
            <div className="mt-3.5 px-2.5 py-1.5 rounded bg-slate-800/70 border border-slate-700/60 flex items-center text-xs text-slate-300">
              <SchoolIcon className="w-3.5 h-3.5 mr-1.5 text-indigo-400 flex-shrink-0" />
              <span className="truncate">{school.name}</span>
            </div>
          ) : (
            <div className="mt-3.5 px-2.5 py-1.5 rounded bg-purple-950/50 border border-purple-700/60 flex items-center text-xs text-purple-200">
              <span className="truncate font-medium">Platform Administration (Global)</span>
            </div>
          )}
        </div>

        {/* Navigation list */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {/* Platform Admin Navigation */}
          {user.role === 'platform_admin' && (
            <>
              <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
                Platform Console
              </div>
              <NavLink
                to="/admin/dashboard"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <LayoutDashboard className="w-4 h-4 mr-3" />
                Overview
              </NavLink>
              <NavLink
                to="/admin/academic-setup"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <GraduationCap className="w-4 h-4 mr-3" />
                Schools & Structure
              </NavLink>
              <NavLink
                to="/admin/audit"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <ShieldAlert className="w-4 h-4 mr-3" />
                Platform Audit
              </NavLink>
            </>
          )}

          {/* Academic Coordinator Navigation */}
          {user.role === 'academic_coordinator' && (
            <>
              <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
                Band Coordination
              </div>
              <NavLink
                to="/coordinator/dashboard"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <LayoutDashboard className="w-4 h-4 mr-3" />
                Band Overview
              </NavLink>
              <NavLink
                to="/coordinator/assignments"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <Layers className="w-4 h-4 mr-3" />
                Assignment Matrix
              </NavLink>
              <NavLink
                to="/admin/bulk-import"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <FileSpreadsheet className="w-4 h-4 mr-3" />
                Bulk Import
              </NavLink>
            </>
          )}

          {/* School Admin Navigation */}
          {(user.role === 'admin' || user.role === 'school_admin') && (
            <>
              <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
                Administration
              </div>
              <NavLink
                to="/admin/dashboard"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <LayoutDashboard className="w-4 h-4 mr-3" />
                Overview
              </NavLink>
              <NavLink
                to="/admin/academic-setup"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <GraduationCap className="w-4 h-4 mr-3" />
                Academic Setup
              </NavLink>
              <NavLink
                to="/coordinator/assignments"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <Layers className="w-4 h-4 mr-3" />
                Assignment Matrix
              </NavLink>
              <NavLink
                to="/admin/bulk-import"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <FileSpreadsheet className="w-4 h-4 mr-3" />
                Bulk Excel / CSV
              </NavLink>
              <NavLink
                to="/admin/audit"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <ShieldAlert className="w-4 h-4 mr-3" />
                Audit Logs
              </NavLink>
            </>
          )}

          {/* Teacher Navigation */}
          {user.role === 'teacher' && (
            <>
              <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
                Teacher Workspace
              </div>
              <NavLink
                to="/teacher/dashboard"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <LayoutDashboard className="w-4 h-4 mr-3" />
                Dashboard
              </NavLink>
              <NavLink
                to="/teacher/classes"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <BookOpen className="w-4 h-4 mr-3" />
                My Classes
              </NavLink>
              <NavLink
                to="/teacher/materials"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <FileText className="w-4 h-4 mr-3" />
                Materials & PDFs
              </NavLink>
              <NavLink
                to="/teacher/ai-studio"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <Sparkles className="w-4 h-4 mr-3 text-indigo-400" />
                AI Studio
              </NavLink>
              <NavLink
                to="/teacher/assessments"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <FileCheck className="w-4 h-4 mr-3" />
                Assessments
              </NavLink>
              <NavLink
                to="/teacher/evaluations"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <CheckCircle className="w-4 h-4 mr-3" />
                Evaluation Queue
              </NavLink>
              <NavLink
                to="/teacher/analytics"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <BarChart3 className="w-4 h-4 mr-3" />
                Analytics
              </NavLink>
            </>
          )}

          {/* Student Navigation */}
          {user.role === 'student' && (
            <>
              <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
                Student Learning
              </div>
              <NavLink
                to="/student/dashboard"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <LayoutDashboard className="w-4 h-4 mr-3" />
                Dashboard
              </NavLink>
              <NavLink
                to="/student/my-learning"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <BookOpen className="w-4 h-4 mr-3" />
                My Learning
              </NavLink>
              <NavLink
                to="/student/assessments"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <FileCheck className="w-4 h-4 mr-3" />
                Upcoming Tests
              </NavLink>
              <NavLink
                to="/student/results"
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                <BarChart3 className="w-4 h-4 mr-3" />
                Results & Feedback
              </NavLink>
            </>
          )}
        </nav>

        {/* User footer & logout */}
        <div className="p-3 border-t border-slate-800">
          <div className="flex items-center justify-between p-2 rounded-lg bg-slate-800/40">
            <div className="overflow-hidden">
              <p className="text-sm font-medium text-white truncate">{user.full_name}</p>
              <p className="text-xs text-slate-400 capitalize truncate">
                {user.designation || user.role}
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-md transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-sm text-slate-500">
            <span>School:</span>
            <span className="font-semibold text-slate-800">{school?.name}</span>
          </div>
          <div className="flex items-center space-x-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 capitalize border border-indigo-100">
              {user.role} workspace
            </span>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
