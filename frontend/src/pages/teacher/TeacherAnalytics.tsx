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

export const TeacherAnalytics: React.FC = () => {
  const [assessments, setAssessments] = useState<any[]>([]);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string>('');
  const [analytics, setAnalytics] = useState<AssessmentAnalytics | null>(null);
  const [topicMastery, setTopicMastery] = useState<TopicMastery[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'questions' | 'topics'>('questions');

  // Load published/evaluated assessments
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
            Learning Diagnostics & Analytics
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            ICSE/ISC item discrimination index, difficulty analysis, score distribution, and curriculum gaps.
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

      {/* Assessment Selector Bar */}
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
            onClick={() => setActiveTab('questions')}
            className={`px-3 py-1.5 rounded-md transition-all ${
              activeTab === 'questions' ? 'bg-white text-slate-900 shadow-sm' : 'hover:text-slate-900'
            }`}
          >
            Item Diagnostics & Discrimination
          </button>
          <button
            onClick={() => setActiveTab('topics')}
            className={`px-3 py-1.5 rounded-md transition-all ${
              activeTab === 'topics' ? 'bg-white text-slate-900 shadow-sm' : 'hover:text-slate-900'
            }`}
          >
            Curriculum Topic Gaps ({topicMastery.length})
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      {analytics && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium uppercase tracking-wider">Average Score</span>
              <TrendingUp className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900">
              {analytics.average_score_pct}%
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {analytics.average_score} / {analytics.total_max_marks} marks
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium uppercase tracking-wider">Turnout & Submissions</span>
              <BarChart3 className="w-4 h-4 text-indigo-600" />
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900">
              {analytics.submitted_count}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Submissions evaluated
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium uppercase tracking-wider">Median Score</span>
              <Award className="w-4 h-4 text-amber-600" />
            </div>
            <div className="mt-2 text-2xl font-bold text-slate-900">
              {analytics.median_score}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              High: {analytics.highest_score} | Low: {analytics.lowest_score}
            </div>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between text-slate-500">
              <span className="text-xs font-medium uppercase tracking-wider">Learning Gaps</span>
              <AlertTriangle className="w-4 h-4 text-rose-600" />
            </div>
            <div className="mt-2 text-2xl font-bold text-rose-600">
              {topicMastery.filter((t) => t.status === 'needs_reinforcement').length}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Topics requiring remedial practice
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {isLoading ? (
        <div className="p-12 text-center text-sm text-slate-500 animate-pulse bg-white rounded-lg border border-slate-200">
          Computing psychometric items and discrimination indices...
        </div>
      ) : activeTab === 'questions' && analytics ? (
        <div className="space-y-6">
          {/* Score Distribution Bars */}
          <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
            <h2 className="text-sm font-bold text-slate-900 mb-3">Score Distribution (Normalized)</h2>
            <div className="grid grid-cols-5 gap-2 text-center">
              {Object.entries(analytics.score_distribution).map(([range, count]) => (
                <div key={range} className="flex flex-col items-center">
                  <div className="w-full bg-slate-100 rounded h-16 flex items-end justify-center p-1">
                    <div
                      className="w-full bg-indigo-500 rounded-sm transition-all"
                      style={{
                        height: `${analytics.submitted_count > 0 ? (count / analytics.submitted_count) * 100 : 0}%`,
                        minHeight: count > 0 ? '6px' : '0px',
                      }}
                    />
                  </div>
                  <span className="text-xs font-bold text-slate-800 mt-1.5">{count}</span>
                  <span className="text-[11px] text-slate-500">{range}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Question Item Analysis Table */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200">
              <h2 className="text-base font-bold text-slate-900">
                Item-Level Difficulty & Discrimination Diagnostics
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Item discrimination index (D) compares top quartile vs bottom quartile performance. D &ge; 0.40 denotes high diagnostic power.
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Q#</th>
                    <th className="py-3 px-4">Prompt</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Marks</th>
                    <th className="py-3 px-4">Accuracy (P)</th>
                    <th className="py-3 px-4">Discrimination (D)</th>
                    <th className="py-3 px-4">Diagnostic Interpretation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {analytics.question_analysis.map((q, idx) => (
                    <tr key={q.item_id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-slate-900">Q{idx + 1}</td>
                      <td className="py-3.5 px-4 max-w-xs truncate text-slate-800 font-medium" title={q.prompt}>
                        {q.prompt}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[11px] text-slate-600 uppercase">
                        {q.item_type.replace(/_/g, ' ')}
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-slate-900">
                        {q.max_marks}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800">{q.accuracy_pct}%</span>
                          <div className="w-12 bg-slate-200 rounded-full h-1.5 overflow-hidden">
                            <div
                              className={`h-full ${
                                q.accuracy_pct >= 70 ? 'bg-emerald-500' : q.accuracy_pct >= 40 ? 'bg-amber-500' : 'bg-rose-500'
                              }`}
                              style={{ width: `${q.accuracy_pct}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                        {q.discrimination_index >= 0 ? `+${q.discrimination_index}` : q.discrimination_index}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${
                            q.discrimination_index >= 0.4
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : q.discrimination_index >= 0.2
                              ? 'bg-amber-50 text-amber-700 border border-amber-200'
                              : 'bg-rose-50 text-rose-700 border border-rose-200'
                          }`}
                        >
                          {q.interpretation}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : activeTab === 'topics' ? (
        /* Topic Mastery & Remediation Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {topicMastery.map((topic, i) => (
            <div
              key={i}
              className={`p-5 rounded-lg border bg-white shadow-sm flex flex-col justify-between ${
                topic.status === 'needs_reinforcement'
                  ? 'border-rose-200 bg-rose-50/20'
                  : 'border-slate-200'
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                    {topic.subject}
                  </span>
                  <span
                    className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
                      topic.status === 'mastered'
                        ? 'bg-emerald-100 text-emerald-800'
                        : topic.status === 'proficient'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-rose-100 text-rose-800'
                    }`}
                  >
                    {topic.status === 'needs_reinforcement' ? 'Critical Gap' : topic.status}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 mt-2">{topic.topic}</h3>
                <div className="mt-3 flex items-center justify-between text-xs text-slate-600 font-medium">
                  <span>Class Mastery:</span>
                  <span className="font-bold text-slate-900">{topic.average_mastery_pct}%</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 mt-1.5 overflow-hidden">
                  <div
                    className={`h-full ${
                      topic.average_mastery_pct >= 80
                        ? 'bg-emerald-500'
                        : topic.average_mastery_pct >= 60
                        ? 'bg-blue-500'
                        : 'bg-rose-500'
                    }`}
                    style={{ width: `${topic.average_mastery_pct}%` }}
                  />
                </div>
              </div>

              {topic.status === 'needs_reinforcement' && (
                <div className="mt-4 pt-3 border-t border-rose-100 flex items-center justify-between text-xs text-rose-700">
                  <span className="font-semibold flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> Revision recommended
                  </span>
                  <a
                    href="/teacher/ai-studio"
                    className="inline-flex items-center gap-0.5 text-indigo-600 hover:text-indigo-800 font-bold"
                  >
                    Generate Practice <ChevronRight className="w-3 h-3" />
                  </a>
                </div>
              )}
            </div>
          ))}
          {topicMastery.length === 0 && (
            <div className="col-span-full p-8 text-center text-sm text-slate-500 bg-white rounded-lg border border-slate-200">
              <BookOpen className="w-8 h-8 mx-auto text-slate-400 mb-2" />
              No curriculum topic analytics recorded yet. Data will populate as students complete assessments.
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
};
