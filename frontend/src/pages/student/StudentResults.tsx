import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import {
  AlertCircle,
  ArrowLeft,
  Key,
} from 'lucide-react';

export const StudentResults: React.FC = () => {
  const [searchParams] = useSearchParams();
  const attemptId = searchParams.get('attempt_id');

  const [result, setResult] = useState<any | null>(null);
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
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-purple-50 text-purple-700">
            Released Results & Model Solutions
          </span>
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
    </div>
  );
};
