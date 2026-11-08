import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../api/client';
import { CheckCircle, AlertCircle, Award, Key } from 'lucide-react';

export const TeacherEvaluationQueue: React.FC = () => {
  const [queue, setQueue] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Active grading response state
  const [scores, setScores] = useState<Record<string, number>>({});
  const [feedbacks, setFeedbacks] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState<Record<string, boolean>>({});

  const loadQueue = async () => {
    try {
      const data = await apiRequest<any[]>('/teacher/evaluation-queue');
      setQueue(data);
      // Initialize score inputs
      const initScores: Record<string, number> = {};
      const initFeedbacks: Record<string, string> = {};
      data.forEach((item) => {
        initScores[item.response_id] = 0;
        initFeedbacks[item.response_id] = '';
      });
      setScores(initScores);
      setFeedbacks(initFeedbacks);
    } catch (err: any) {
      setError(err.message || 'Failed to load evaluation queue');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleGradeSubmit = async (responseId: string, maxMarks: number) => {
    const scoreVal = Number(scores[responseId] || 0);
    if (scoreVal < 0 || scoreVal > maxMarks) {
      alert(`Score must be between 0 and ${maxMarks}`);
      return;
    }

    setIsSubmitting((prev) => ({ ...prev, [responseId]: true }));
    setError(null);

    try {
      await apiRequest(`/evaluations/${responseId}`, {
        method: 'PATCH',
        body: JSON.stringify({
          manual_score: scoreVal,
          teacher_feedback: feedbacks[responseId] || undefined,
        }),
      });
      setMessage('Response graded successfully! Remaining subjective responses updated.');
      await loadQueue();
    } catch (err: any) {
      setError(err.message || 'Failed to grade response');
    } finally {
      setIsSubmitting((prev) => ({ ...prev, [responseId]: false }));
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Teacher Evaluation Queue</h2>
        <p className="text-sm text-slate-500 mt-1">
          Review subjective and written student responses, award marks against marking schemes, and leave constructive feedback.
        </p>
      </div>

      {message && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg">
          {message}
        </div>
      )}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-800 text-xs rounded-lg flex items-center">
          <AlertCircle className="w-4 h-4 mr-2 text-red-500" /> {error}
        </div>
      )}

      {isLoading ? (
        <div className="p-12 text-center text-slate-400 bg-white rounded-xl border border-slate-200">
          Loading pending submissions...
        </div>
      ) : queue.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200 space-y-2">
          <CheckCircle className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
          <h3 className="text-base font-bold text-slate-800">All Caught Up!</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            There are no subjective student responses pending teacher grading. Any objective questions are evaluated automatically.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            {queue.length} Responses Pending Grading
          </div>
          {queue.map((item) => (
            <div key={item.response_id} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div>
                  <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">
                    {item.assessment_title}
                  </span>
                  <h4 className="text-sm font-bold text-slate-900 mt-0.5">
                    Student: {item.student_name}
                  </h4>
                </div>
                <div className="text-xs font-mono font-bold bg-slate-100 px-2.5 py-1 rounded text-slate-700">
                  Weight: {item.max_marks} Marks
                </div>
              </div>

              {/* Question & Student Answer */}
              <div className="space-y-3 text-xs">
                <div>
                  <span className="font-semibold text-slate-500 uppercase tracking-wider text-[11px]">Prompt:</span>
                  <p className="text-sm text-slate-900 mt-0.5 font-medium whitespace-pre-wrap">{item.question_prompt}</p>
                </div>

                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                  <span className="font-semibold text-slate-700 uppercase tracking-wider text-[11px]">Student's Submitted Answer:</span>
                  <p className="text-sm text-slate-800 mt-1 whitespace-pre-wrap">
                    {item.student_answer?.text || JSON.stringify(item.student_answer)}
                  </p>
                </div>

                {/* Teacher Marking Scheme Reference */}
                {item.marking_scheme && (
                  <div className="p-3 bg-indigo-50/50 rounded-lg border border-indigo-100 text-slate-700 space-y-0.5">
                    <div className="flex items-center text-indigo-900 font-bold uppercase text-[10px]">
                      <Key className="w-3 h-3 mr-1 text-indigo-600" />
                      Marking Guide Reference
                    </div>
                    <div>{item.marking_scheme}</div>
                  </div>
                )}
              </div>

              {/* Grading Input Form */}
              <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row items-center gap-3">
                <div className="flex items-center space-x-2 w-full sm:w-auto">
                  <span className="text-xs font-semibold text-slate-700 uppercase whitespace-nowrap">Award Marks:</span>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    max={item.max_marks}
                    value={scores[item.response_id] ?? 0}
                    onChange={(e) =>
                      setScores((prev) => ({ ...prev, [item.response_id]: Number(e.target.value) }))
                    }
                    className="w-24 p-2 text-sm border border-slate-300 rounded-lg outline-none font-bold text-center focus:ring-2 focus:ring-indigo-600"
                  />
                  <span className="text-xs text-slate-400 font-bold">/ {item.max_marks}</span>
                </div>

                <input
                  type="text"
                  placeholder="Optional teacher feedback or rubric note for student"
                  value={feedbacks[item.response_id] ?? ''}
                  onChange={(e) =>
                    setFeedbacks((prev) => ({ ...prev, [item.response_id]: e.target.value }))
                  }
                  className="flex-1 w-full p-2 text-xs border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
                />

                <button
                  onClick={() => handleGradeSubmit(item.response_id, item.max_marks)}
                  disabled={isSubmitting[item.response_id]}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm flex items-center whitespace-nowrap disabled:opacity-50 transition-colors"
                >
                  <Award className="w-3.5 h-3.5 mr-1" />
                  {isSubmitting[item.response_id] ? 'Saving...' : 'Submit Grade'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
