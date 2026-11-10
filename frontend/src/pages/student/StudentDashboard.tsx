import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import {
  FileCheck,
  CheckCircle2,
  Clock,
  BookOpen,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Award,
  Target,
  ListChecks,
  HelpCircle,
  Send,
  PlusCircle,
} from 'lucide-react';

interface TopicMastery {
  topic: string;
  subject: string;
  total_items: number;
  total_attempts: number;
  average_mastery_pct: number;
  status: 'mastered' | 'proficient' | 'needs_reinforcement';
}

interface StudentPerformanceMap {
  student_id: string;
  student_name: string;
  class_name: string;
  section_name: string;
  total_assessments_taken: number;
  average_score_pct: number;
  topic_mastery: TopicMastery[];
  materials_completed_count: number;
}

interface AcademicGoal {
  id: string;
  goal_title: string;
  target_pct: number;
  current_pct: number;
  deadline_date?: string;
  status: string;
}

interface RevisionTopic {
  topic: string;
  subject: string;
  error_count: number;
  average_mastery_pct: number;
  recommended_action: string;
}

interface DoubtItem {
  id: string;
  subject_name: string;
  question_text: string;
  status: string;
  reply_text?: string;
  created_at: string;
}

export const StudentDashboard: React.FC = () => {
  const { user } = useAuth();
  const [enrollments, setEnrollments] = useState<any[]>([]);
  const [performanceMap, setPerformanceMap] = useState<StudentPerformanceMap | null>(null);

  // Phase 8 States
  const [goals, setGoals] = useState<AcademicGoal[]>([]);
  const [revisionList, setRevisionList] = useState<RevisionTopic[]>([]);
  const [doubts, setDoubts] = useState<DoubtItem[]>([]);
  
  const [newGoalTitle, setNewGoalTitle] = useState('');
  const [newGoalTarget, setNewGoalTarget] = useState(85);
  const [isSavingGoal, setIsSavingGoal] = useState(false);

  const [doubtSubject, setDoubtSubject] = useState('');
  const [doubtText, setDoubtText] = useState('');
  const [isSubmittingDoubt, setIsSubmittingDoubt] = useState(false);
  const [doubtSuccessMsg, setDoubtSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [eRes, pRes, gRes, rRes, dRes] = await Promise.all([
          apiRequest<any[]>('/student-enrollments'),
          apiRequest<StudentPerformanceMap>('/student/performance-map').catch(() => null),
          apiRequest<AcademicGoal[]>('/student/academic-goals').catch(() => []),
          apiRequest<RevisionTopic[]>('/student/revision-list').catch(() => []),
          apiRequest<DoubtItem[]>('/student/doubts').catch(() => []),
        ]);
        setEnrollments(eRes || []);
        setPerformanceMap(pRes);
        setGoals(gRes || []);
        setRevisionList(rRes || []);
        setDoubts(dRes || []);
      } catch (err) {
        console.error('Failed to load student dashboard metadata', err);
      }
    }
    load();
  }, []);

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGoalTitle.trim()) return;
    setIsSavingGoal(true);
    try {
      const created = await apiRequest<AcademicGoal>('/student/academic-goals', {
        method: 'POST',
        body: JSON.stringify({
          goal_title: newGoalTitle,
          target_pct: newGoalTarget,
        }),
      });
      setGoals([created, ...goals]);
      setNewGoalTitle('');
    } catch (err: any) {
      alert(err.message || 'Failed to create academic goal');
    } finally {
      setIsSavingGoal(false);
    }
  };

  const handleAskDoubt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!doubtText.trim()) return;
    setIsSubmittingDoubt(true);
    setDoubtSuccessMsg(null);
    try {
      const created = await apiRequest<DoubtItem>('/student/doubts', {
        method: 'POST',
        body: JSON.stringify({
          subject_name: doubtSubject || 'General',
          question_text: doubtText,
        }),
      });
      setDoubts([created, ...doubts]);
      setDoubtText('');
      setDoubtSuccessMsg('Your doubt has been submitted to your assigned subject teacher.');
    } catch (err: any) {
      alert(err.message || 'Failed to submit academic doubt');
    } finally {
      setIsSubmittingDoubt(false);
    }
  };

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
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
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
            <div className="text-2xl font-bold text-slate-900">
              {performanceMap?.total_assessments_taken || 0}
            </div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Assessments Taken</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">
              {performanceMap?.average_score_pct || 0}%
            </div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Cumulative Average</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">
              {performanceMap?.materials_completed_count || 0}
            </div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Materials Read</div>
          </div>
        </div>
      </div>

      {/* Private Performance Map Section */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-indigo-600" />
              <h3 className="text-base font-bold text-slate-900">Personal Topic Mastery & Strength Map</h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Your real-time concept mastery across assessed chapters and distributed curriculum notes.
            </p>
          </div>
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 self-start sm:self-auto">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            Strictly Private to You
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
          {performanceMap?.topic_mastery && performanceMap.topic_mastery.length > 0 ? (
            performanceMap.topic_mastery.map((tm, idx) => (
              <div key={idx} className="p-4 bg-slate-50 rounded-lg border border-slate-100 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-800 truncate">{tm.topic}</span>
                  <span
                    className={`font-semibold px-2 py-0.5 rounded text-[10px] uppercase tracking-wider ${
                      tm.status === 'mastered'
                        ? 'bg-emerald-100 text-emerald-800'
                        : tm.status === 'proficient'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-rose-100 text-rose-800'
                    }`}
                  >
                    {tm.status}
                  </span>
                </div>
                <div className="flex justify-between text-xs text-slate-500 font-medium">
                  <span>Accuracy</span>
                  <span className="font-bold text-slate-900">{tm.average_mastery_pct}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full ${
                      tm.average_mastery_pct >= 80 ? 'bg-emerald-500' : tm.average_mastery_pct >= 60 ? 'bg-blue-500' : 'bg-rose-500'
                    }`}
                    style={{ width: `${tm.average_mastery_pct}%` }}
                  />
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full py-8 text-center text-xs text-slate-400">
              <CheckCircle2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              Your personalized topic mastery map will populate as you complete evaluations and review materials.
            </div>
          )}
        </div>
      </div>

      {/* My Learning Quick Banner */}
      <div className="bg-gradient-to-r from-indigo-900 to-slate-900 text-white rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-white/10 rounded-lg text-indigo-300">
            <BookOpen className="w-7 h-7" />
          </div>
          <div>
            <h3 className="font-bold text-base text-white">Curriculum Notes & Reference Guides</h3>
            <p className="text-xs text-slate-300 mt-0.5">
              Access handouts, chapter notes, and learning materials distributed to your class section.
            </p>
          </div>
        </div>
        <Link
          to="/student/my-learning"
          className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-600 text-white font-medium text-xs hover:bg-indigo-500 transition shadow-sm whitespace-nowrap self-start sm:self-auto"
        >
          <span>Open My Learning</span>
          <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
        </Link>
      </div>

      {/* Assigned Assessments Container */}
      <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm text-center">
        <FileCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-800">No Assessments Assigned Right Now</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
          When your teachers publish tests, quizzes, or practice worksheets for your section, they will appear here with instructions and time limits.
        </p>
      </div>

      {/* Phase 8: Academic Goals & Smart Revision List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Academic Goals Card */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                <Target className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">My Academic Targets</h3>
                <p className="text-xs text-slate-500">Personal target mastery & exam benchmarks</p>
              </div>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-700 rounded-full">
              {goals.length} Goals
            </span>
          </div>

          {/* New Goal Input Form */}
          <form onSubmit={handleCreateGoal} className="flex gap-2">
            <input
              type="text"
              placeholder="e.g. Master Calculus Limits & Continuity"
              value={newGoalTitle}
              onChange={(e) => setNewGoalTitle(e.target.value)}
              className="flex-1 text-xs rounded-lg border-slate-300 shadow-sm px-3 py-2 border focus:ring-indigo-500 focus:border-indigo-500"
            />
            <input
              type="number"
              min="50"
              max="100"
              value={newGoalTarget}
              onChange={(e) => setNewGoalTarget(Number(e.target.value))}
              className="w-16 text-xs rounded-lg border-slate-300 shadow-sm px-2 py-2 border text-center font-bold"
              title="Target %"
            />
            <button
              type="submit"
              disabled={isSavingGoal || !newGoalTitle.trim()}
              className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center transition-colors disabled:opacity-50"
            >
              <PlusCircle className="w-4 h-4 mr-1" />
              Set
            </button>
          </form>

          {/* Goals List */}
          {goals.length === 0 ? (
            <div className="py-6 text-center text-xs text-slate-400">
              No target goals set yet. Set a score target above to track your progress!
            </div>
          ) : (
            <div className="space-y-3 max-h-[280px] overflow-y-auto pr-1">
              {goals.map((g) => (
                <div
                  key={g.id}
                  className="p-3 rounded-lg border border-slate-200 bg-slate-50/60 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-slate-900">{g.goal_title}</span>
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                        g.status === 'achieved'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-indigo-100 text-indigo-800'
                      }`}
                    >
                      {g.status}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>Target: {g.target_pct}%</span>
                    <span className="font-bold text-slate-800">Current: {g.current_pct}%</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full ${
                        g.current_pct >= g.target_pct ? 'bg-emerald-500' : 'bg-indigo-600'
                      }`}
                      style={{ width: `${Math.min(100, g.current_pct)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Smart Revision Priority List */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-amber-50 text-amber-600 rounded-lg">
                <ListChecks className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Smart Revision Queue</h3>
                <p className="text-xs text-slate-500">Adaptive priority based on assessment error patterns</p>
              </div>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-amber-50 text-amber-700 rounded-full border border-amber-200">
              {revisionList.length} Priority Topics
            </span>
          </div>

          {revisionList.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              All assessed topics meet proficient mastery! No urgent revision tasks queued.
            </div>
          ) : (
            <div className="space-y-3 max-h-[340px] overflow-y-auto pr-1">
              {revisionList.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg border border-slate-200 bg-white hover:border-slate-300 transition-all space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="font-bold text-xs text-slate-900">{item.topic}</span>
                      <span className="text-[11px] text-slate-500 ml-2">({item.subject})</span>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                      {item.error_count} Errors
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-600 flex items-center gap-1">
                    <span className="font-medium text-amber-700">Recommended Action:</span>
                    <span>{item.recommended_action}</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                    <span>Mastery Level</span>
                    <span className="font-bold text-slate-800">{item.average_mastery_pct}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Phase 8: Structured Academic Doubt Clearance */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <HelpCircle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Ask Your Subject Teacher</h3>
              <p className="text-xs text-slate-500">Direct academic doubt routing to assigned faculty</p>
            </div>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            {doubts.length} Inquiries
          </span>
        </div>

        {doubtSuccessMsg && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>{doubtSuccessMsg}</span>
          </div>
        )}

        {/* Doubt Form */}
        <form onSubmit={handleAskDoubt} className="space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div className="sm:col-span-1">
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">Subject</label>
              <input
                type="text"
                placeholder="e.g. Mathematics"
                value={doubtSubject}
                onChange={(e) => setDoubtSubject(e.target.value)}
                className="w-full text-xs rounded-lg border-slate-300 shadow-sm px-3 py-2 border bg-white"
              />
            </div>
            <div className="sm:col-span-3">
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">Your Question or Conceptual Doubt</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Explain the intuition behind the Mean Value Theorem application in Section B..."
                  value={doubtText}
                  onChange={(e) => setDoubtText(e.target.value)}
                  className="flex-1 text-xs rounded-lg border-slate-300 shadow-sm px-3 py-2 border bg-white"
                />
                <button
                  type="submit"
                  disabled={isSubmittingDoubt || !doubtText.trim()}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold flex items-center transition-colors disabled:opacity-50 shadow-sm"
                >
                  <Send className="w-3.5 h-3.5 mr-1" />
                  Ask
                </button>
              </div>
            </div>
          </div>
        </form>

        {/* Doubts History */}
        {doubts.length > 0 && (
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">Recent Doubts & Teacher Responses</h4>
            <div className="space-y-2.5 max-h-[260px] overflow-y-auto pr-1">
              {doubts.map((d) => (
                <div
                  key={d.id}
                  className="p-3 rounded-lg border border-slate-200 bg-white space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800">{d.subject_name}</span>
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                        d.status === 'answered'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {d.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-700">{d.question_text}</p>
                  {d.reply_text ? (
                    <div className="mt-2 p-2.5 bg-emerald-50/70 border border-emerald-200 rounded-md text-xs text-emerald-900">
                      <span className="font-bold block text-[11px] text-emerald-800">Teacher Response:</span>
                      {d.reply_text}
                    </div>
                  ) : (
                    <span className="text-[11px] text-amber-700 italic block">
                      Awaiting teacher reply in next academic office hours.
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
