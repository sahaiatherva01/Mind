import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import {
  AlertCircle,
  ArrowLeft,
  Key,
  Award,
  Printer,
  X,
  GraduationCap,
} from 'lucide-react';

interface SubjectGradeReport {
  subject_id: string;
  subject_name: string;
  total_max_marks: number;
  obtained_marks: number;
  percentage: number;
  grade: string;
  remarks: string;
}

interface StudentReportCardData {
  school_name: string;
  student_name: string;
  roll_number?: string;
  class_name: string;
  section_name: string;
  term: string;
  academic_year: string;
  subjects: SubjectGradeReport[];
  total_possible_marks: number;
  total_obtained_marks: number;
  overall_percentage: number;
  overall_grade: string;
  attendance_pct: number;
  teacher_general_remarks: string;
}

export const StudentResults: React.FC = () => {
  const [searchParams] = useSearchParams();
  const attemptId = searchParams.get('attempt_id');
  const { user } = useAuth();

  const [result, setResult] = useState<any | null>(null);
  const [reportCard, setReportCard] = useState<StudentReportCardData | null>(null);
  const [showReportCardModal, setShowReportCardModal] = useState(false);
  const [isLoadingReportCard, setIsLoadingReportCard] = useState(false);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      if (!attemptId) {
        setIsLoading(false);
        return;
      }
      try {
        const data = await apiRequest<any>(`/attempts/${attemptId}/results`);
        setResult(data);
      } catch (err: any) {
        setError(err.message || 'Results have not been released yet.');
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [attemptId]);

  const handleOpenReportCard = async () => {
    if (!user) return;
    setIsLoadingReportCard(true);
    setShowReportCardModal(true);
    try {
      const rc = await apiRequest<StudentReportCardData>(`/reports/student/${user.id}/report-card`);
      setReportCard(rc);
    } catch (err: any) {
      console.error('Failed to load student report card', err);
    } finally {
      setIsLoadingReportCard(false);
    }
  };

  if (!attemptId) {
    return (
      <div className="p-12 text-center text-slate-500 bg-white rounded-xl border border-slate-200">
        Please select a completed assessment from your <Link to="/student/assessments" className="text-indigo-600 underline">assigned tests list</Link> to view released results.
      </div>
    );
  }

  if (isLoading) {
    return <div className="p-12 text-center text-slate-400">Loading released assessment results...</div>;
  }

  if (error || !result) {
    return (
      <div className="max-w-md mx-auto my-12 p-8 bg-white rounded-xl border border-amber-200 text-center space-y-3">
        <AlertCircle className="w-10 h-10 text-amber-500 mx-auto" />
        <h3 className="font-bold text-slate-800">Results Pending Release</h3>
        <p className="text-xs text-slate-600">
          {error || 'Your teacher has not released marks and model solutions for this assessment yet.'}
        </p>
        <Link
          to="/student/assessments"
          className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold shadow-sm"
        >
          <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Return to My Tests
        </Link>
      </div>
    );
  }

  const scorePct = Math.round(((result.total_score || 0) / result.max_score) * 100);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Result Hero Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-purple-50 text-purple-700">
              Released Results & Model Solutions
            </span>
            <button
              onClick={handleOpenReportCard}
              className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition border border-indigo-200"
            >
              <Award className="w-3.5 h-3.5 text-indigo-600" />
              View Official Term Report Card
            </button>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mt-2">{result.assessment_title}</h2>
          <p className="text-xs text-slate-400 mt-1">
            Submitted on: {new Date(result.submitted_at).toLocaleString()}
          </p>
        </div>

        <div className="text-center sm:text-right bg-slate-50 p-4 rounded-xl border border-slate-100 min-w-[140px]">
          <div className="text-3xl font-extrabold text-indigo-600">
            {result.total_score} <span className="text-sm font-normal text-slate-400">/ {result.max_score}</span>
          </div>
          <div className="text-xs font-bold text-slate-500 uppercase mt-0.5">{scorePct}% Score</div>
        </div>
      </div>

      {/* Questions & Feedback Breakdown */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">Detailed Question Breakdown</h3>

        {result.responses?.map((r: any, idx: number) => {
          const awarded = r.manual_score !== null ? r.manual_score : (r.auto_score !== null ? r.auto_score : 0);
          return (
            <div key={r.item_id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                <span className="font-bold text-xs text-slate-800">Question {idx + 1}</span>
                <span className="font-mono text-xs font-bold text-slate-700">
                  Score: <span className="text-indigo-600">{awarded}</span> Marks
                </span>
              </div>

              <p className="text-sm font-medium text-slate-900 whitespace-pre-wrap">{r.prompt}</p>

              {/* Student's submitted response */}
              <div className="p-3 bg-slate-50 rounded-lg text-xs">
                <span className="font-semibold text-slate-600 uppercase text-[10px]">Your Answer:</span>
                <div className="font-medium text-slate-800 mt-0.5">
                  {r.student_answer?.selected_option ? `Option ${r.student_answer.selected_option}` : (r.student_answer?.text || 'No response recorded')}
                </div>
              </div>

              {/* Teacher feedback if present */}
              {r.teacher_feedback && (
                <div className="p-3 bg-emerald-50/60 border border-emerald-200 rounded-lg text-xs space-y-0.5">
                  <span className="font-bold text-emerald-900 uppercase text-[10px]">Teacher Feedback:</span>
                  <div className="text-emerald-950 font-medium">{r.teacher_feedback}</div>
                </div>
              )}

              {/* Model solution & rationale */}
              <div className="p-3 bg-purple-50/40 border border-purple-100 rounded-lg text-xs space-y-1">
                <div className="flex items-center text-purple-900 font-bold uppercase text-[10px]">
                  <Key className="w-3 h-3 mr-1 text-purple-600" />
                  Model Answer & Board Marking Scheme
                </div>
                <div className="text-slate-800 font-medium">
                  <span className="font-semibold">Expected: </span> {r.expected_answer}
                </div>
                {r.marking_scheme && (
                  <div className="text-slate-600">
                    <span className="font-semibold">Marking Scheme: </span> {r.marking_scheme}
                  </div>
                )}
                {r.rationale && (
                  <div className="text-slate-500 italic mt-0.5">
                    Rationale: {r.rationale}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Official Branded Report Card Modal */}
      {showReportCardModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full p-8 shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-200 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-indigo-600 text-white rounded-xl">
                  <GraduationCap className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">
                    {reportCard?.school_name || 'Academic Institution'}
                  </h3>
                  <p className="text-xs text-slate-500">Official Student Progress Report & Cumulative Transcript</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => window.print()}
                  className="p-2 text-slate-600 hover:text-indigo-600 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
                  title="Print Report Card"
                >
                  <Printer className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setShowReportCardModal(false)}
                  className="p-2 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {isLoadingReportCard ? (
              <div className="p-12 text-center text-slate-400">Loading student transcript records...</div>
            ) : reportCard ? (
              <div className="space-y-6">
                {/* Student Bio Row */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-xl text-xs">
                  <div>
                    <span className="text-slate-400 uppercase font-semibold text-[10px]">Student Name</span>
                    <div className="font-bold text-slate-900 mt-0.5">{reportCard.student_name}</div>
                  </div>
                  <div>
                    <span className="text-slate-400 uppercase font-semibold text-[10px]">Roll Number</span>
                    <div className="font-bold text-slate-900 mt-0.5">{reportCard.roll_number || 'N/A'}</div>
                  </div>
                  <div>
                    <span className="text-slate-400 uppercase font-semibold text-[10px]">Class & Section</span>
                    <div className="font-bold text-slate-900 mt-0.5">{reportCard.class_name} - {reportCard.section_name}</div>
                  </div>
                  <div>
                    <span className="text-slate-400 uppercase font-semibold text-[10px]">Term & Year</span>
                    <div className="font-bold text-slate-900 mt-0.5">{reportCard.term} ({reportCard.academic_year})</div>
                  </div>
                </div>

                {/* Subject Grades Table */}
                <div className="rounded-xl border border-slate-200 overflow-hidden">
                  <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
                    <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider">
                      <tr>
                        <th className="py-3 px-4">Subject</th>
                        <th className="py-3 px-4">Max Marks</th>
                        <th className="py-3 px-4">Obtained</th>
                        <th className="py-3 px-4">% Score</th>
                        <th className="py-3 px-4">Grade</th>
                        <th className="py-3 px-4">Teacher Remark</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {reportCard.subjects.map((sub) => (
                        <tr key={sub.subject_id} className="hover:bg-slate-50/50">
                          <td className="py-3 px-4 font-bold text-slate-900">{sub.subject_name}</td>
                          <td className="py-3 px-4 text-slate-500">{sub.total_max_marks}</td>
                          <td className="py-3 px-4 font-semibold text-slate-800">{sub.obtained_marks}</td>
                          <td className="py-3 px-4 font-bold text-indigo-600">{sub.percentage}%</td>
                          <td className="py-3 px-4">
                            <span className="px-2 py-0.5 rounded font-bold text-xs bg-indigo-50 text-indigo-700">
                              {sub.grade}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-slate-600">{sub.remarks}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Cumulative Totals and Remarks */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-4 bg-indigo-50/60 rounded-xl border border-indigo-100 text-center">
                    <span className="text-xs text-indigo-700 font-semibold uppercase">Overall Aggregate</span>
                    <div className="text-2xl font-black text-indigo-900 mt-1">
                      {reportCard.overall_percentage}%
                    </div>
                    <span className="text-xs font-bold text-indigo-600">Grade {reportCard.overall_grade}</span>
                  </div>

                  <div className="p-4 bg-emerald-50/60 rounded-xl border border-emerald-100 text-center">
                    <span className="text-xs text-emerald-700 font-semibold uppercase">Total Marks</span>
                    <div className="text-2xl font-black text-emerald-900 mt-1">
                      {reportCard.total_obtained_marks} / {reportCard.total_possible_marks}
                    </div>
                    <span className="text-xs font-bold text-emerald-600">Term Weighted</span>
                  </div>

                  <div className="p-4 bg-purple-50/60 rounded-xl border border-purple-100 text-center">
                    <span className="text-xs text-purple-700 font-semibold uppercase">Term Attendance</span>
                    <div className="text-2xl font-black text-purple-900 mt-1">
                      {reportCard.attendance_pct}%
                    </div>
                    <span className="text-xs font-bold text-purple-600">Regular & Punctual</span>
                  </div>
                </div>

                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 space-y-1">
                  <span className="font-bold text-slate-900 uppercase text-[10px]">Class Teacher Observations:</span>
                  <p>{reportCard.teacher_general_remarks}</p>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
