import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { FileCheck, CheckCircle2, Clock } from 'lucide-react';

export const StudentDashboard: React.FC = () => {
  const { user } = useAuth();
  const [enrollments, setEnrollments] = useState<any[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const eRes = await apiRequest<any[]>('/student-enrollments');
        setEnrollments(eRes);
      } catch (err) {
        console.error('Failed to load student enrollments', err);
      }
    }
    load();
  }, []);

  const myEnrollment = enrollments[0];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Welcome, {user?.full_name}</h2>
        <p className="text-sm text-slate-500 mt-1">
          {myEnrollment ? `${myEnrollment.class_name} • Section ${myEnrollment.section_name} (Roll: ${myEnrollment.roll_number || 'N/A'})` : 'Student Learning Portal'}
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">0</div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Upcoming Tests</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <FileCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">0</div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Completed Attempts</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">0</div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Released Results</div>
          </div>
        </div>
      </div>

      {/* Assigned Assessments Container */}
      <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm text-center">
        <FileCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-800">No Assessments Assigned Right Now</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
          When your teachers publish tests, quizzes, or practice worksheets for your section, they will appear here with instructions and time limits.
        </p>
      </div>
    </div>
  );
};
