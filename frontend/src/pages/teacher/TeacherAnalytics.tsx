import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../api/client';
import {
  BarChart3,
  TrendingUp,
  AlertTriangle,
  Award,
  Download,
  Printer,
  ChevronRight,
  BookOpen,
  Sparkles,
  ShieldCheck,
  Users,
  CheckCircle2,
} from 'lucide-react';

interface QuestionAnalysis {
  item_id: string;
  item_type: string;
  prompt: string;
  max_marks: number;
  topic?: string;
  total_responses: number;
  correct_responses: number;
  average_marks_awarded: number;
  accuracy_pct: number;
  discrimination_index: number;
  interpretation: string;
}

interface AssessmentAnalytics {
  assessment_id: string;
  title: string;
  subject: string;
  total_enrolled: number;
  submitted_count: number;
  total_max_marks: number;
  average_score: number;
  average_score_pct: number;
  median_score: number;
  highest_score: number;
  lowest_score: number;
  score_distribution: Record<string, number>;
  question_analysis: QuestionAnalysis[];
}

interface TopicMastery {
  topic: string;
  subject: string;
  total_items: number;
  total_attempts: number;
  average_mastery_pct: number;
  status: 'mastered' | 'proficient' | 'needs_reinforcement';
}

interface FourLevelAnalytics {
  class_level: {
    class_id?: string;
    class_name: string;
    section_id?: string;
    section_name: string;
    total_enrolled: number;
    section_average_pct: number;
    highest_score_pct: number;
    lowest_score_pct: number;
    toppers: Array<{ student_id: string; student_name: string; roll_number?: string; average_score_pct: number }>;
    at_risk: Array<{ student_id: string; student_name: string; roll_number?: string; average_score_pct: number }>;
  };
  subject_level: {
    subject_id?: string;
    subject_name: string;
    average_mastery_pct: number;
    topic_mastery: TopicMastery[];
    weakest_topics: TopicMastery[];
  };
  cross_analytics: {
    material_engagement_correlation: {
      engaged_students_count: number;
      engaged_students_average_pct: number;
      unengaged_students_count: number;
      unengaged_students_average_pct: number;
      performance_lift_pct: number;
    };
    section_comparison: Array<{ section_id: string; section_name: string; average_score_pct: number }>;
  };
  individual_student?: {
    student_id: string;
    student_name: string;
    roll_number?: string;
    class_name: string;
    section_name: string;
    average_score_pct: number;
    submission_rate_pct: number;
    marks_trend: Array<{ attempt_id: string; score_pct: number; date?: string }>;
    topic_strengths: TopicMastery[];
    materials_read_count: number;
    reading_duration_minutes: number;
  };
}

interface AIInsightResponse {
  scope_type: string;
  scope_id?: string;
  summary: string;
  strengths: string[];
  conceptual_gaps: string[];
  pedagogical_recommendations: string[];
  evidence_tools_used: string[];
}

export const TeacherAnalytics: React.FC = () => {
  const [assessments, setAssessments] = useState<any[]>([]);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string>('');
  const [analytics, setAnalytics] = useState<AssessmentAnalytics | null>(null);
  const [topicMastery, setTopicMastery] = useState<TopicMastery[]>([]);
  const [fourLevel, setFourLevel] = useState<FourLevelAnalytics | null>(null);
  const [aiInsights, setAiInsights] = useState<AIInsightResponse | null>(null);
  const [isGeneratingInsights, setIsGeneratingInsights] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'four_level' | 'ai_insights' | 'questions' | 'topics'>('four_level');

  // Load published/evaluated assessments and 4-level metrics
  useEffect(() => {
    async function init() {
      try {
        const asmtList = await apiRequest<any[]>('/assessments');
        setAssessments(asmtList);
        if (asmtList.length > 0) {
          setSelectedAssessmentId(asmtList[0].id);
        }

        const topics = await apiRequest<TopicMastery[]>('/analytics/topics');
        setTopicMastery(topics);

        const flData = await apiRequest<FourLevelAnalytics>('/teacher/analytics');
        setFourLevel(flData);
      } catch (err) {
        console.error('Failed to load initial analytics metadata', err);
      } finally {
        setIsLoading(false);
      }
    }
    init();
  }, []);

  // Load selected assessment analytics
  useEffect(() => {
    if (!selectedAssessmentId) return;
    async function loadAssessmentAnalytics() {
      setIsLoading(true);
      try {
        const data = await apiRequest<AssessmentAnalytics>(
          `/analytics/assessments/${selectedAssessmentId}`
        );
        setAnalytics(data);
      } catch (err) {
        console.error('Failed to load assessment analytics', err);
        setAnalytics(null);
      } finally {
        setIsLoading(false);
      }
    }
    loadAssessmentAnalytics();
  }, [selectedAssessmentId]);

  const handleGenerateInsights = async () => {
    setIsGeneratingInsights(true);
    try {
      const res = await apiRequest<AIInsightResponse>('/analytics/insights', {
        method: 'POST',
        body: JSON.stringify({
          scope_type: 'class',
          scope_id: fourLevel?.class_level?.class_id,
        }),
      });
      setAiInsights(res);
    } catch (err) {
      console.error('Failed to generate AI insights', err);
    } finally {
      setIsGeneratingInsights(false);
    }
  };

  const handleExportCSV = () => {
    if (!selectedAssessmentId) return;
    window.open(`/api/v1/assessments/${selectedAssessmentId}/export/csv`, '_blank');
  };

  const handleExportPDF = (includeKeys: boolean) => {
    if (!selectedAssessmentId) return;
    const url = `/api/v1/assessments/${selectedAssessmentId}/export/pdf${
      includeKeys ? '?include_marking_scheme=true' : ''
    }`;
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            4-Level Learning Diagnostics & Cross-Analytics
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Hierarchical analytics across Student, Section, Subject, and Cross-Engagement with AI pedagogical insights.
          </p>
        </div>

        {/* Global Export Controls */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleExportCSV}
            disabled={!selectedAssessmentId}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            Export Gradebook CSV
          </button>
          <button
            onClick={() => handleExportPDF(false)}
            disabled={!selectedAssessmentId}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            <Printer className="w-3.5 h-3.5" />
            Print Paper
          </button>
          <button
            onClick={() => handleExportPDF(true)}
            disabled={!selectedAssessmentId}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            <Printer className="w-3.5 h-3.5" />
            Print with Marking Scheme
          </button>
        </div>
      </div>

      {/* Navigation & Selector Bar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <label htmlFor="assessment-select" className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Active Assessment:
          </label>
          <select
            id="assessment-select"
            value={selectedAssessmentId}
            onChange={(e) => setSelectedAssessmentId(e.target.value)}
            className="text-sm font-semibold rounded-md border border-slate-300 px-3 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {assessments.map((a) => (
              <option key={a.id} value={a.id}>
                {a.title} ({a.status})
              </option>
            ))}
          </select>
        </div>

        {/* Tab Toggle */}
        <div className="inline-flex p-1 bg-slate-100 rounded-lg text-xs font-semibold text-slate-600">
          <button
            onClick={() => setActiveTab('four_level')}
            className={`px-3 py-1.5 rounded-md transition-all ${
              activeTab === 'four_level' ? 'bg-white text-slate-900 shadow-sm' : 'hover:text-slate-900'
            }`}
          >
            4-Level & Cross-Analytics
          </button>
          <button
            onClick={() => {
              setActiveTab('ai_insights');
              if (!aiInsights) handleGenerateInsights();
            }}
            className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
              activeTab === 'ai_insights' ? 'bg-white text-indigo-700 shadow-sm' : 'hover:text-slate-900'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            AI Diagnostic Insights
          </button>
          <button
            onClick={() => setActiveTab('questions')}
            className={`px-3 py-1.5 rounded-md transition-all ${
              activeTab === 'questions' ? 'bg-white text-slate-900 shadow-sm' : 'hover:text-slate-900'
            }`}
          >
            Item Discrimination
          </button>
          <button
            onClick={() => setActiveTab('topics')}
            className={`px-3 py-1.5 rounded-md transition-all ${
              activeTab === 'topics' ? 'bg-white text-slate-900 shadow-sm' : 'hover:text-slate-900'
            }`}
          >
            Curriculum Gaps ({topicMastery.length})
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="p-12 text-center text-slate-400">Loading comprehensive analytics data...</div>
      ) : activeTab === 'four_level' ? (
        /* --- Tab: 4-Level & Cross-Analytics --- */
        <div className="space-y-6">
          {/* Level 4: Cross-Analytics & Material Engagement Correlation Hero */}
          {fourLevel?.cross_analytics?.material_engagement_correlation && (
            <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 text-white rounded-xl p-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-white/20 text-indigo-200">
                    Level 4 • Cross-Analytics Correlation
                  </span>
                  <h3 className="text-xl font-bold text-white mt-1">
                    Learning Material Engagement vs Performance Lift
                  </h3>
                  <p className="text-xs text-indigo-200 mt-0.5">
                    Empirical correlation comparing students actively reading course materials against class performance.
                  </p>
                </div>
                <div className="flex items-center gap-6 bg-white/10 px-5 py-3 rounded-lg backdrop-blur-sm self-start sm:self-auto">
                  <div className="text-center">
                    <div className="text-2xl font-black text-emerald-400">
                      +{fourLevel.cross_analytics.material_engagement_correlation.performance_lift_pct}%
                    </div>
                    <div className="text-[11px] uppercase tracking-wider text-slate-300 font-semibold">
                      Performance Lift
                    </div>
                  </div>
                  <div className="h-8 w-px bg-white/20" />
                  <div className="text-center">
                    <div className="text-2xl font-black text-white">
                      {fourLevel.cross_analytics.material_engagement_correlation.engaged_students_average_pct}%
                    </div>
                    <div className="text-[11px] uppercase tracking-wider text-slate-300 font-semibold">
                      Engaged Student Avg
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Grid: Level 2 (Section) and Level 3 (Subject) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Level 2: Section Overview */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-indigo-600" />
                  <h2 className="text-base font-bold text-slate-900">
                    Level 2 • Section {fourLevel?.class_level.section_name} Performance
                  </h2>
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 bg-slate-100 text-slate-700 rounded">
                  {fourLevel?.class_level.total_enrolled || 0} Enrolled
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="text-xs text-slate-500 font-medium">Section Average</div>
                  <div className="text-xl font-bold text-slate-900 mt-1">
                    {fourLevel?.class_level.section_average_pct}%
                  </div>
                </div>
                <div className="p-3 bg-emerald-50 rounded-lg">
                  <div className="text-xs text-emerald-700 font-medium">Highest Score</div>
                  <div className="text-xl font-bold text-emerald-700 mt-1">
                    {fourLevel?.class_level.highest_score_pct}%
                  </div>
                </div>
                <div className="p-3 bg-amber-50 rounded-lg">
                  <div className="text-xs text-amber-700 font-medium">Lowest Score</div>
                  <div className="text-xl font-bold text-amber-700 mt-1">
                    {fourLevel?.class_level.lowest_score_pct}%
                  </div>
                </div>
              </div>

              {/* Toppers and At-Risk */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1 mb-2">
                    <Award className="w-4 h-4" /> Top Performers
                  </h3>
                  <div className="space-y-1.5">
                    {fourLevel?.class_level.toppers.map((t, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs p-2 bg-emerald-50/50 rounded border border-emerald-100">
                        <span className="font-semibold text-slate-800">{t.student_name}</span>
                        <span className="font-bold text-emerald-700">{t.average_score_pct}%</span>
                      </div>
                    ))}
                    {fourLevel?.class_level.toppers.length === 0 && (
                      <div className="text-xs text-slate-400 italic">No evaluated attempts recorded yet.</div>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-rose-700 flex items-center gap-1 mb-2">
                    <AlertTriangle className="w-4 h-4" /> At-Risk Attention Needed
                  </h3>
                  <div className="space-y-1.5">
                    {fourLevel?.class_level.at_risk.map((r, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs p-2 bg-rose-50/50 rounded border border-rose-100">
                        <span className="font-semibold text-slate-800">{r.student_name}</span>
                        <span className="font-bold text-rose-700">{r.average_score_pct}%</span>
                      </div>
                    ))}
                    {fourLevel?.class_level.at_risk.length === 0 && (
                      <div className="text-xs text-emerald-600 italic">No at-risk students (&lt;45%) detected.</div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Level 3: Subject & Topic Mastery */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-indigo-600" />
                  <h2 className="text-base font-bold text-slate-900">
                    Level 3 • Subject Mastery & Weakest Chapters
                  </h2>
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded">
                  {fourLevel?.subject_level.subject_name || 'Subject'}
                </span>
              </div>

              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Topic Breakdown & Diagnostic Accuracy
                </h3>
                {fourLevel?.subject_level.topic_mastery.slice(0, 4).map((tm, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs font-medium text-slate-700">
                      <span>{tm.topic}</span>
                      <span className="font-bold">{tm.average_mastery_pct}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full ${
                          tm.average_mastery_pct >= 80 ? 'bg-emerald-500' : tm.average_mastery_pct >= 60 ? 'bg-blue-500' : 'bg-rose-500'
                        }`}
                        style={{ width: `${tm.average_mastery_pct}%` }}
                      />
                    </div>
                  </div>
                ))}
                {fourLevel?.subject_level.topic_mastery.length === 0 && (
                  <div className="text-xs text-slate-400 italic">No topic data accumulated yet.</div>
                )}
              </div>
            </div>
          </div>

          {/* Level 1: Individual Student Detailed Record */}
          {fourLevel?.individual_student && (
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-indigo-600" />
                  <h2 className="text-base font-bold text-slate-900">
                    Level 1 • Student Progress: {fourLevel.individual_student.student_name}
                  </h2>
                </div>
                <span className="text-xs text-slate-500">
                  Roll: {fourLevel.individual_student.roll_number || 'N/A'} • {fourLevel.individual_student.class_name} - {fourLevel.individual_student.section_name}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="text-xs text-slate-500">Cumulative Average</div>
                  <div className="text-lg font-bold text-slate-900 mt-1">{fourLevel.individual_student.average_score_pct}%</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="text-xs text-slate-500">Submission Rate</div>
                  <div className="text-lg font-bold text-slate-900 mt-1">{fourLevel.individual_student.submission_rate_pct}%</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="text-xs text-slate-500">Materials Read</div>
                  <div className="text-lg font-bold text-slate-900 mt-1">{fourLevel.individual_student.materials_read_count} docs</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="text-xs text-slate-500">Reading Duration</div>
                  <div className="text-lg font-bold text-slate-900 mt-1">{fourLevel.individual_student.reading_duration_minutes} min</div>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : activeTab === 'ai_insights' ? (
        /* --- Tab: AI Diagnostic Insights (Track A5) --- */
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-indigo-100 p-6 shadow-sm space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-4">
              <div>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                  Analytics Insight Agent (Track A5)
                </div>
                <h2 className="text-xl font-bold text-slate-900 mt-1.5">
                  Automated Pedagogical Diagnostic Synthesis
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Generated via deterministic typed tool functions with strict zero text-to-SQL architecture.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  Zero Text-to-SQL Guaranteed
                </span>
                <button
                  onClick={handleGenerateInsights}
                  disabled={isGeneratingInsights}
                  className="px-4 py-2 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
                >
                  {isGeneratingInsights ? 'Synthesizing...' : 'Refresh Insights'}
                </button>
              </div>
            </div>

            {isGeneratingInsights ? (
              <div className="p-12 text-center text-slate-400">
                <Sparkles className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-2" />
                Querying telemetry tools and synthesizing pedagogical diagnosis...
              </div>
            ) : aiInsights ? (
              <div className="space-y-6">
                {/* Summary Banner */}
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 leading-relaxed font-medium">
                  {aiInsights.summary}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Strengths */}
                  <div className="p-5 bg-emerald-50/60 border border-emerald-200 rounded-xl space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      Pedagogical Strengths
                    </h3>
                    <ul className="space-y-2 text-xs text-emerald-900">
                      {aiInsights.strengths.map((str, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-emerald-500 font-bold">•</span>
                          <span>{str}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Conceptual Gaps */}
                  <div className="p-5 bg-rose-50/60 border border-rose-200 rounded-xl space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-rose-800 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-rose-600" />
                      Conceptual Gaps & Friction Areas
                    </h3>
                    <ul className="space-y-2 text-xs text-rose-900">
                      {aiInsights.conceptual_gaps.map((gap, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-rose-500 font-bold">•</span>
                          <span>{gap}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Recommendations */}
                <div className="p-5 bg-indigo-50/50 border border-indigo-200 rounded-xl space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-800 flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-indigo-600" />
                    Targeted Actionable Recommendations
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {aiInsights.pedagogical_recommendations.map((rec, idx) => (
                      <div key={idx} className="p-3 bg-white rounded-lg border border-indigo-100 text-xs text-slate-800 font-medium shadow-sm">
                        <span className="font-bold text-indigo-600 mr-1.5">#{idx + 1}</span>
                        {rec}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Evidence Tools Trace */}
                <div className="pt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100">
                  <span>Diagnostic Evidence Retrieved Via:</span>
                  <span className="font-mono text-slate-600">
                    {aiInsights.evidence_tools_used.join(' • ')}
                  </span>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      ) : activeTab === 'questions' ? (
        /* --- Tab: Questions (Existing) --- */
        <div className="space-y-6">
          {analytics && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                  <span>Submissions</span>
                  <BarChart3 className="w-4 h-4 text-indigo-500" />
                </div>
                <div className="text-2xl font-bold text-slate-900 mt-2">
                  {analytics.submitted_count}
                  <span className="text-xs font-normal text-slate-400 ml-1">/ {analytics.total_enrolled}</span>
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {Math.round((analytics.submitted_count / (analytics.total_enrolled || 1)) * 100)}% class turnout
                </div>
              </div>

              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                  <span>Average Score</span>
                  <TrendingUp className="w-4 h-4 text-emerald-500" />
                </div>
                <div className="text-2xl font-bold text-slate-900 mt-2">
                  {analytics.average_score_pct}%
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  {analytics.average_score} / {analytics.total_max_marks} avg marks
                </div>
              </div>

              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                  <span>Median Marks</span>
                  <Award className="w-4 h-4 text-amber-500" />
                </div>
                <div className="text-2xl font-bold text-slate-900 mt-2">
                  {analytics.median_score}
                </div>
                <div className="text-xs text-slate-500 mt-1">50th percentile mark</div>
              </div>

              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
                  <span>Score Range</span>
                  <AlertTriangle className="w-4 h-4 text-rose-500" />
                </div>
                <div className="text-2xl font-bold text-slate-900 mt-2">
                  {analytics.highest_score} - {analytics.lowest_score}
                </div>
                <div className="text-xs text-slate-500 mt-1">High vs Low scored</div>
              </div>
            </div>
          )}

          {/* Table */}
          {analytics && (
            <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
              <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
                <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">#</th>
                    <th className="py-3 px-4">Question Prompt</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Marks</th>
                    <th className="py-3 px-4">Topic</th>
                    <th className="py-3 px-4">Accuracy</th>
                    <th className="py-3 px-4">Discrimination</th>
                    <th className="py-3 px-4">Diagnostic Interpretation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {analytics.question_analysis.map((q, idx) => (
                    <tr key={q.item_id} className="hover:bg-slate-50/50">
                      <td className="py-3 px-4 font-bold text-slate-500">{idx + 1}</td>
                      <td className="py-3 px-4 font-medium text-slate-800 max-w-xs truncate">{q.prompt}</td>
                      <td className="py-3 px-4 text-slate-500">{q.item_type}</td>
                      <td className="py-3 px-4 font-semibold text-slate-700">{q.max_marks}</td>
                      <td className="py-3 px-4 text-slate-500">{q.topic || 'General'}</td>
                      <td className="py-3 px-4 font-bold text-slate-900">{q.accuracy_pct}%</td>
                      <td className="py-3 px-4 font-mono font-bold text-indigo-600">{q.discrimination_index}</td>
                      <td className="py-3 px-4 text-slate-600">{q.interpretation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : activeTab === 'topics' ? (
        /* --- Tab: Topics (Existing) --- */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {topicMastery.map((topic, i) => (
            <div key={i} className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{topic.subject}</span>
                <h3 className="text-base font-bold text-slate-900 mt-1">{topic.topic}</h3>
                <div className="mt-3 flex items-center justify-between text-xs text-slate-600 font-medium">
                  <span>Class Mastery:</span>
                  <span className="font-bold text-slate-900">{topic.average_mastery_pct}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 mt-1.5 overflow-hidden">
                  <div
                    className={`h-full ${
                      topic.average_mastery_pct >= 80 ? 'bg-emerald-500' : topic.average_mastery_pct >= 60 ? 'bg-blue-500' : 'bg-rose-500'
                    }`}
                    style={{ width: `${topic.average_mastery_pct}%` }}
                  />
                </div>
              </div>
              {topic.status === 'needs_reinforcement' && (
                <div className="mt-4 pt-3 border-t border-rose-100 flex items-center justify-between text-xs text-rose-700 font-semibold">
                  <span className="flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> Revision recommended
                  </span>
                  <a href="/teacher/ai-studio" className="text-indigo-600 hover:text-indigo-800 font-bold flex items-center gap-0.5">
                    Generate Practice <ChevronRight className="w-3 h-3" />
                  </a>
                </div>
              )}
            </div>
          ))}
          {topicMastery.length === 0 && (
            <div className="col-span-full p-8 text-center text-sm text-slate-500 bg-white rounded-lg border border-slate-200">
              <BookOpen className="w-8 h-8 mx-auto text-slate-400 mb-2" />
              No curriculum topic analytics recorded yet.
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
};
