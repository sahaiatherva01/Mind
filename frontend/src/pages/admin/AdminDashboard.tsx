import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { Link } from 'react-router-dom';
import { GraduationCap, Users, BookOpen, FileSpreadsheet, ShieldAlert, ArrowRight } from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const { school } = useAuth();
  const [classes, setClasses] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [cList, sList, uList] = await Promise.all([
          apiRequest<any[]>('/classes'),
          apiRequest<any[]>('/subjects'),
          apiRequest<any[]>('/users?limit=200'),
        ]);
        setClasses(cList);
        setSubjects(sList);
        setUsers(uList);
      } catch (err) {
        console.error('Failed to load admin stats', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const teachers = users.filter((u) => u.role === 'teacher');
  const students = users.filter((u) => u.role === 'student');

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Institution Administration</h2>
        <p className="text-sm text-slate-500 mt-1">
          Configure academic structures, teacher assignments, and user records for {school?.name}.
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <GraduationCap className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{isLoading ? '...' : classes.length}</div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Classes Configured</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{isLoading ? '...' : subjects.length}</div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Subjects Active</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{isLoading ? '...' : teachers.length}</div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Teachers Assigned</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{isLoading ? '...' : students.length}</div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Students Enrolled</div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900 flex items-center">
            <GraduationCap className="w-5 h-5 mr-2 text-indigo-600" />
            Academic Setup
          </h3>
          <p className="text-xs text-slate-500 mt-2">
            Create academic years, classes, sections (e.g. 11E, 12A, 12D), and curriculum subjects.
          </p>
          <Link
            to="/admin/academic-setup"
            className="mt-4 inline-flex items-center text-xs font-semibold text-indigo-600 hover:text-indigo-800"
          >
            Manage Setup <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900 flex items-center">
            <FileSpreadsheet className="w-5 h-5 mr-2 text-emerald-600" />
            Bulk Excel / CSV Import
          </h3>
          <p className="text-xs text-slate-500 mt-2">
            Import teachers, coordinators, students, class enrollments, and teacher assignments via spreadsheet.
          </p>
          <Link
            to="/admin/bulk-import"
            className="mt-4 inline-flex items-center text-xs font-semibold text-emerald-600 hover:text-emerald-800"
          >
            Upload File <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-base font-semibold text-slate-900 flex items-center">
            <ShieldAlert className="w-5 h-5 mr-2 text-amber-600" />
            Security Audit Trail
          </h3>
          <p className="text-xs text-slate-500 mt-2">
            View immutable audit records for logins, administrative modifications, and assessment releases.
          </p>
          <Link
            to="/admin/audit"
            className="mt-4 inline-flex items-center text-xs font-semibold text-amber-600 hover:text-amber-800"
          >
            Inspect Audit Logs <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </div>
      </div>
    </div>
  );
};

