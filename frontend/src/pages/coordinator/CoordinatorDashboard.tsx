import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import {
  GraduationCap,
  Users,
  Layers,
  BookOpen,
  UserCheck,
  ShieldCheck,
  ArrowRight,
  AlertTriangle,
  ClipboardList,
  CheckCircle,
  PlusCircle,
} from 'lucide-react';

interface ClassItem {
  id: string;
  name: string;
  grade_level?: number;
  sections: { id: string; name: string }[];
}

interface BandSummary {
  band_id: string;
  band_name: string;
  min_grade: number;
  max_grade: number;
  classes: ClassItem[];
  total_classes: number;
  total_sections: number;
  total_teachers: number;
  total_students: number;
  class_teachers: Record<string, string | null>;
}

interface EarlyWarningStudent {
  student_id: string;
  student_name: string;
  class_name: string;
  section_name: string;
  average_score_pct: number;
  tab_switches_total: number;
  materials_read_count: number;
  risk_score: number;
  risk_factors: string[];
}

interface InterventionItem {
  id: string;
  student_name: string;
  student_id: string;
  risk_score: number;
  action_type: string;
  status: string;
  notes: string;
  created_at: string;
}

export const CoordinatorDashboard: React.FC = () => {
  const [summary, setSummary] = useState<BandSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Phase 8 Early-Warning & Interventions
  const [atRiskStudents, setAtRiskStudents] = useState<EarlyWarningStudent[]>([]);
  const [interventions, setInterventions] = useState<InterventionItem[]>([]);
  const [selectedStudentForAction, setSelectedStudentForAction] = useState<EarlyWarningStudent | null>(null);
  const [interventionAction, setInterventionAction] = useState<string>('remedial_session');
  const [interventionNotes, setInterventionNotes] = useState<string>('');
  const [isSubmittingIntervention, setIsSubmittingIntervention] = useState<boolean>(false);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sumData, warnData, intData] = await Promise.all([
          apiRequest<BandSummary>('/coordinator/band-summary'),
          apiRequest<EarlyWarningStudent[]>('/coordinator/early-warning-signals').catch(() => []),
          apiRequest<InterventionItem[]>('/coordinator/interventions').catch(() => []),
        ]);
        setSummary(sumData);
        setAtRiskStudents(warnData || []);
        setInterventions(intData || []);
      } catch (err: any) {
        setError(err.message || 'Failed to load coordinator band summary');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleCreateIntervention = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStudentForAction) return;
    setIsSubmittingIntervention(true);
    setActionSuccessMsg(null);
    try {
      const created = await apiRequest<InterventionItem>('/coordinator/interventions', {
        method: 'POST',
        body: JSON.stringify({
          student_id: selectedStudentForAction.student_id,
          risk_score: selectedStudentForAction.risk_score,
          action_type: interventionAction,
          notes: interventionNotes || 'Early warning pedagogical support planned.',
        }),
      });
      setInterventions([created, ...interventions]);
      setActionSuccessMsg(`Intervention recorded for ${selectedStudentForAction.student_name}`);
      setSelectedStudentForAction(null);
      setInterventionNotes('');
    } catch (err: any) {
      alert(err.message || 'Failed to create intervention');
    } finally {
      setIsSubmittingIntervention(false);
    }
  };

  const handleUpdateStatus = async (interventionId: string, newStatus: string) => {
    try {
      const updated = await apiRequest<InterventionItem>(`/coordinator/interventions/${interventionId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      });
      setInterventions(interventions.map((i) => (i.id === interventionId ? updated : i)));
    } catch (err: any) {
      alert(err.message || 'Failed to update intervention status');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-rose-800">
        <p className="font-semibold">Unable to load Band Dashboard</p>
        <p className="text-sm mt-1">{error || 'No active grade band found for your account.'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 rounded-2xl p-6 text-white shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/30 border border-indigo-400/40 text-indigo-200">
              Grade Band {summary.min_grade}–{summary.max_grade}
            </span>
            <span className="text-xs text-indigo-300 flex items-center">
              <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-400" />
              Band-Scoped Jurisdiction
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">{summary.band_name}</h1>
          <p className="text-sm text-indigo-200 mt-1">
            Academic Coordinator Workspace — Staff assignments, roster governance, and curriculum oversight.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/coordinator/assignments"
            className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors shadow"
          >
            <Layers className="w-4 h-4 mr-2" />
            Assignment Matrix
            <ArrowRight className="w-4 h-4 ml-1.5" />
          </Link>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Classes</span>
            <GraduationCap className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{summary.total_classes}</div>
          <p className="text-xs text-slate-500 mt-1">Grades {summary.min_grade} to {summary.max_grade}</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Sections</span>
            <Layers className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{summary.total_sections}</div>
          <p className="text-xs text-slate-500 mt-1">Active class sections</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Teachers</span>
            <Users className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{summary.total_teachers}</div>
          <p className="text-xs text-slate-500 mt-1">Assigned in band</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Students</span>
            <BookOpen className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{summary.total_students}</div>
          <p className="text-xs text-slate-500 mt-1">Enrolled in band sections</p>
        </div>
      </div>

      {/* Classes & Sections Structure with Class Teachers */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Band Academic Structure</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Classes, sections, and designated Class Teachers within your jurisdiction
            </p>
          </div>
          <span className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md font-medium">
            1 Class Teacher Per Section Policy Enforced
          </span>
        </div>

        <div className="divide-y divide-slate-100">
          {summary.classes.map((cls) => (
            <div key={cls.id} className="p-6">
              <div className="flex items-center gap-3 mb-3">
                <span className="font-semibold text-slate-900 text-base">{cls.name}</span>
                {cls.grade_level && (
                  <span className="text-xs font-medium px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                    Grade {cls.grade_level}
                  </span>
                )}
                <span className="text-xs text-slate-400">
                  {cls.sections.length} {cls.sections.length === 1 ? 'Section' : 'Sections'}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {cls.sections.map((sec) => {
                  const ctName = summary.class_teachers[sec.id];
                  return (
                    <div
                      key={sec.id}
                      className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60 flex items-start justify-between"
                    >
                      <div>
                        <div className="font-medium text-sm text-slate-900">
                          {cls.name} — Section {sec.name}
                        </div>
                        <div className="mt-1 flex items-center text-xs text-slate-600">
                          <UserCheck className="w-3.5 h-3.5 mr-1 text-indigo-600 flex-shrink-0" />
                          {ctName ? (
                            <span className="font-medium text-slate-800 truncate">
                              Class Teacher: {ctName}
                            </span>
                          ) : (
                            <span className="text-amber-600 italic">No Class Teacher Assigned</span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Phase 8: Early-Warning Signals & Coordinator Interventions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Early-Warning At-Risk Signals Card */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-rose-50 text-rose-600 rounded-lg">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Early-Warning Signals</h3>
                <p className="text-xs text-slate-500">Autonomous risk detection across Band {summary.min_grade}–{summary.max_grade}</p>
              </div>
            </div>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-50 text-rose-700 border border-rose-200">
              {atRiskStudents.length} Flagged
            </span>
          </div>

          {actionSuccessMsg && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-600" />
              {actionSuccessMsg}
            </div>
          )}

          {atRiskStudents.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              No students currently flagged in the early-warning matrix for this band.
            </div>
          ) : (
            <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
              {atRiskStudents.map((st) => (
                <div
                  key={st.student_id}
                  className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/70 hover:border-slate-300 transition-all flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-slate-900">{st.student_name}</span>
                      <span className="text-xs text-slate-500 font-mono">
                        {st.class_name} • Sec {st.section_name}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-100 text-rose-700">
                        Risk: {st.risk_score}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {st.risk_factors.map((rf, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 rounded bg-white text-slate-600 border border-slate-200 text-[11px]"
                        >
                          {rf}
                        </span>
                      ))}
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedStudentForAction(st)}
                    className="inline-flex items-center px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold whitespace-nowrap self-start sm:self-auto transition-colors"
                  >
                    <PlusCircle className="w-3.5 h-3.5 mr-1" />
                    Intervene
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Intervention Lifecycle Tracker */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                <ClipboardList className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Intervention Tracker</h3>
                <p className="text-xs text-slate-500">Pedagogical support and action history</p>
              </div>
            </div>
            <span className="text-xs text-slate-500 font-medium">
              {interventions.length} Total
            </span>
          </div>

          {/* New Intervention Form if Student Selected */}
          {selectedStudentForAction && (
            <form onSubmit={handleCreateIntervention} className="p-4 bg-indigo-50/60 rounded-xl border border-indigo-200 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-900">
                  New Action: {selectedStudentForAction.student_name}
                </span>
                <button
                  type="button"
                  onClick={() => setSelectedStudentForAction(null)}
                  className="text-xs text-slate-500 hover:text-slate-800"
                >
                  Cancel
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-700 block mb-1">Action Type</label>
                  <select
                    value={interventionAction}
                    onChange={(e) => setInterventionAction(e.target.value)}
                    className="w-full text-xs rounded-md border-slate-300 shadow-sm py-1.5 px-2 bg-white"
                  >
                    <option value="remedial_session">Remedial Session</option>
                    <option value="counseling">Counseling</option>
                    <option value="parent_meeting">Parent Meeting</option>
                    <option value="peer_tutoring">Peer Tutoring</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-slate-700 block mb-1">Pedagogical Notes</label>
                  <input
                    type="text"
                    value={interventionNotes}
                    onChange={(e) => setInterventionNotes(e.target.value)}
                    placeholder="Focus areas & goals..."
                    className="w-full text-xs rounded-md border-slate-300 shadow-sm py-1.5 px-2 bg-white"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmittingIntervention}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-lg shadow-sm transition-colors"
              >
                {isSubmittingIntervention ? 'Saving...' : 'Confirm Pedagogical Intervention'}
              </button>
            </form>
          )}

          {/* Intervention List */}
          {interventions.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              No active interventions logged yet.
            </div>
          ) : (
            <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
              {interventions.map((inv) => (
                <div
                  key={inv.id}
                  className="p-3.5 rounded-lg border border-slate-200 bg-white shadow-xs space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-bold text-sm text-slate-900">{inv.student_name}</span>
                      <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 uppercase">
                        {inv.action_type.replace('_', ' ')}
                      </span>
                    </div>
                    <select
                      value={inv.status}
                      onChange={(e) => handleUpdateStatus(inv.id, e.target.value)}
                      className={`text-xs font-semibold rounded-md border px-2 py-1 ${
                        inv.status === 'resolved'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : inv.status === 'in_progress'
                          ? 'bg-amber-50 text-amber-700 border-amber-200'
                          : 'bg-rose-50 text-rose-700 border-rose-200'
                      }`}
                    >
                      <option value="open">Open</option>
                      <option value="in_progress">In Progress</option>
                      <option value="resolved">Resolved</option>
                    </select>
                  </div>
                  {inv.notes && <p className="text-xs text-slate-600">{inv.notes}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
