import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { Link } from 'react-router-dom';
import { Sparkles, FileCheck, CheckCircle, ArrowRight, ShieldCheck } from 'lucide-react';

export const TeacherDashboard: React.FC = () => {
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const aRes = await apiRequest<any[]>('/teacher-assignments');
        setAssignments(aRes);
      } catch (err) {
        console.error('Failed to load teacher workspaces', err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Welcome, {user?.full_name}</h2>
        <p className="text-sm text-slate-500 mt-1">
          {user?.designation || 'Academic Faculty'} — Your assigned teaching workspaces and academic actions.
        </p>
      </div>

      {/* Human in the loop reassurance banner */}
      <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-100 flex items-start space-x-3 text-sm text-indigo-950">
        <ShieldCheck className="w-5 h-5 text-indigo-600 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-indigo-900">Mandatory Teacher Control: </span>
          All AI-assisted assessments, worksheets, and question papers are generated as editable drafts. Nothing reaches your students without your explicit review and sign-off.
        </div>
      </div>

      {/* Assigned Workspaces */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-700">
            My Assigned Teaching Workspaces
          </h3>
          <span className="text-xs text-slate-500 font-medium">
            Strictly scoped: {assignments.length} assigned classes
          </span>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-slate-400 bg-white rounded-xl border border-slate-200">
            Loading your assigned academic scopes...
          </div>
        ) : assignments.length === 0 ? (
          <div className="p-8 text-center text-slate-500 bg-white rounded-xl border border-slate-200">
            No class assignments currently allocated. Please contact your school administrator.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {assignments.map((a) => (
              <div
                key={a.id}
                className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-indigo-400 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700">
                      {a.subject_name}
                    </span>
                    <span className="text-xs font-mono font-semibold text-slate-500">
                      Sec {a.section_name}
                    </span>
                  </div>
                  <h4 className="text-lg font-bold text-slate-900 mt-3">{a.class_name}</h4>
                  <p className="text-xs text-slate-500 mt-1">Section {a.section_name} • {a.subject_name}</p>
                </div>
                <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between">
                  <Link
                    to="/teacher/ai-studio"
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center"
                  >
                    Generate Content <Sparkles className="w-3 h-3 ml-1" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Launch Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4">
            <Sparkles className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-slate-900">AI Content Studio</h3>
          <p className="text-xs text-slate-500 mt-2">
            Generate curriculum-aligned worksheets, quizzes, and board-format question papers with 40 ICSE/ISC question types.
          </p>
          <Link
            to="/teacher/ai-studio"
            className="mt-4 inline-flex items-center text-xs font-semibold text-indigo-600 hover:text-indigo-800"
          >
            Launch Studio <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
            <FileCheck className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-slate-900">Assessments & Publishing</h3>
          <p className="text-xs text-slate-500 mt-2">
            Schedule exams, publish assessments to assigned sections, set time limits and result release policies.
          </p>
          <Link
            to="/teacher/assessments"
            className="mt-4 inline-flex items-center text-xs font-semibold text-emerald-600 hover:text-emerald-800"
          >
            View Assessments <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center mb-4">
            <CheckCircle className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-slate-900">Evaluation Queue</h3>
          <p className="text-xs text-slate-500 mt-2">
            Review subjective submissions, audit automated marks, and release results and model solutions to students.
          </p>
          <Link
            to="/teacher/evaluations"
            className="mt-4 inline-flex items-center text-xs font-semibold text-amber-600 hover:text-amber-800"
          >
            Grade Submissions <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </div>
      </div>
    </div>
  );
};
