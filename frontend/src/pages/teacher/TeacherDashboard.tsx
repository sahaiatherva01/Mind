import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  FileCheck,
  CheckCircle,
  ArrowRight,
  ShieldCheck,
  Users2,
  Clock,
} from 'lucide-react';

interface SmartGroupItem {
  id: string;
  name: string;
  group_type: string;
  class_id: string;
  section_id: string;
  subject_id: string;
  student_ids: string[];
  weak_topics: string[];
  created_at: string;
}

export const TeacherDashboard: React.FC = () => {
  const { user } = useAuth();
  const [assignments, setAssignments] = useState<any[]>([]);
  const [smartGroups, setSmartGroups] = useState<SmartGroupItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [generatingForGroupId, setGeneratingForGroupId] = useState<string | null>(null);
  const [generationMsg, setGenerationMsg] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [aRes, gRes] = await Promise.all([
          apiRequest<any[]>('/teacher-assignments'),
          apiRequest<SmartGroupItem[]>('/teacher/smart-groups').catch(() => []),
        ]);
        setAssignments(aRes);
        setSmartGroups(gRes || []);
      } catch (err) {
        console.error('Failed to load teacher workspaces', err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const handleGenerateRemedial = async (groupId: string, groupName: string) => {
    setGeneratingForGroupId(groupId);
    setGenerationMsg(null);
    try {
      const res = await apiRequest<any>(`/teacher/smart-groups/${groupId}/generate-remedial`, {
        method: 'POST',
      });
      setGenerationMsg(
        `Draft generated for "${groupName}"! Saved with ${res.total_items} remedial questions under review status.`
      );
    } catch (err: any) {
      alert(err.message || 'Failed to generate remedial worksheet');
    } finally {
      setGeneratingForGroupId(null);
    }
  };

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
                    <div className="flex items-center gap-1.5">
                      {a.is_substitute && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                          Substitute
                        </span>
                      )}
                      <span className="text-xs font-mono font-semibold text-slate-500">
                        Sec {a.section_name}
                      </span>
                    </div>
                  </div>
                  <h4 className="text-lg font-bold text-slate-900 mt-3">{a.class_name}</h4>
                  <p className="text-xs text-slate-500 mt-1">Section {a.section_name} • {a.subject_name}</p>
                  {a.is_substitute && a.valid_to && (
                    <div className="mt-2 flex items-center text-[11px] text-amber-700">
                      <Clock className="w-3 h-3 mr-1" />
                      Valid through: {new Date(a.valid_to).toLocaleDateString()}
                    </div>
                  )}
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

      {/* Phase 8: Smart Student Groups & Adaptive Remedial Worksheets */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-lg">
              <Users2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Smart Student Groups & Cohorts</h3>
              <p className="text-xs text-slate-500">
                Segment learners by topic mastery and generate targeted remedial worksheets with teacher review.
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-700 rounded-full self-start sm:self-auto">
            {smartGroups.length} Active Cohorts
          </span>
        </div>

        {generationMsg && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>{generationMsg}</span>
          </div>
        )}

        {smartGroups.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">
            <Users2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            No cohorts configured yet. Groups are formed automatically based on concept mastery thresholds or created manually.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {smartGroups.map((g) => (
              <div
                key={g.id}
                className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:border-slate-300 transition-all flex flex-col justify-between space-y-3"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-900">{g.name}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        g.group_type === 'remedial'
                          ? 'bg-rose-100 text-rose-800'
                          : g.group_type === 'advanced'
                          ? 'bg-indigo-100 text-indigo-800'
                          : 'bg-emerald-100 text-emerald-800'
                      }`}
                    >
                      {g.group_type}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    {g.student_ids.length} Students enrolled in cohort
                  </div>
                  {g.weak_topics && g.weak_topics.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {g.weak_topics.map((t, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded bg-white text-slate-600 border border-slate-200 text-[10px]"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400">
                    Draft awaits review before release
                  </span>
                  <button
                    onClick={() => handleGenerateRemedial(g.id, g.name)}
                    disabled={generatingForGroupId === g.id}
                    className="inline-flex items-center px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition-colors disabled:opacity-50"
                  >
                    <Sparkles className="w-3.5 h-3.5 mr-1" />
                    {generatingForGroupId === g.id ? 'Generating Draft...' : '1-Click Remedial'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
