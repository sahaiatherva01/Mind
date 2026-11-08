import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import {
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Send,
} from 'lucide-react';

export const AssessmentPlayer: React.FC = () => {
  const { assessmentId } = useParams<{ assessmentId: string }>();
  const navigate = useNavigate();

  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('saved');

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showConfirmSubmit, setShowConfirmSubmit] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Timer
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);

  useEffect(() => {
    async function start() {
      try {
        const data = await apiRequest<any>(`/assessments/${assessmentId}/attempts`, {
          method: 'POST',
        });
        setAttemptId(data.attempt_id);
        setQuestions(data.questions);

        // Fetch instructions for duration
        const inst = await apiRequest<any>(`/assessments/${assessmentId}/instructions`);
        if (inst.duration_minutes) {
          const startedAt = new Date(data.started_at).getTime();
          const elapsedSecs = Math.floor((Date.now() - startedAt) / 1000);
          const remaining = Math.max(0, inst.duration_minutes * 60 - elapsedSecs);
          setSecondsLeft(remaining);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to start assessment attempt');
      } finally {
        setIsLoading(false);
      }
    }
    start();
  }, [assessmentId]);

  // Countdown timer hook
  useEffect(() => {
    if (secondsLeft === null || secondsLeft <= 0) return;
    const interval = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev !== null && prev <= 1) {
          clearInterval(interval);
          handleSubmit(); // Auto-submit when time expires
          return 0;
        }
        return prev !== null ? prev - 1 : null;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [secondsLeft]);

  const handleAnswerChange = async (itemId: string, newAns: any) => {
    setAnswers((prev) => ({ ...prev, [itemId]: newAns }));
    if (!attemptId) return;

    setSaveStatus('saving');
    try {
      await apiRequest(`/attempts/${attemptId}/responses/${itemId}`, {
        method: 'PUT',
        body: JSON.stringify({ answer_json: newAns }),
      });
      setSaveStatus('saved');
    } catch {
      setSaveStatus('idle');
    }
  };

  const handleSubmit = async () => {
    if (!attemptId) return;
    setIsSubmitting(true);
    try {
      const sub = await apiRequest<any>(`/attempts/${attemptId}/submit`, {
        method: 'POST',
      });
      if (sub.is_released) {
        navigate(`/student/results?attempt_id=${attemptId}`);
      } else {
        navigate('/student/assessments');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to submit assessment');
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center text-sm text-slate-500 font-sans">
        Preparing examination workspace...
      </div>
    );
  }

  if (error || questions.length === 0) {
    return (
      <div className="max-w-md mx-auto my-16 p-6 bg-white rounded-xl border border-red-200 text-center space-y-3">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto" />
        <h3 className="font-bold text-slate-800">Cannot Load Assessment</h3>
        <p className="text-xs text-slate-600">{error || 'No questions available.'}</p>
        <button
          onClick={() => navigate('/student/assessments')}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold"
        >
          Return to My Tests
        </button>
      </div>
    );
  }

  const currentQ = questions[currentIndex];
  const currentAnswer = answers[currentQ.item_id] || {};
  const answeredCount = Object.keys(answers).length;

  const formatTimer = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      {/* Top Authoritative Exam Header */}
      <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between shadow-xs sticky top-0 z-30">
        <div className="flex items-center space-x-3">
          <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white font-bold text-sm flex items-center justify-center">
            M
          </div>
          <span className="font-bold text-slate-900 text-sm truncate">Assessment Player</span>
        </div>

        <div className="flex items-center space-x-5 text-xs">
          {/* Autosave Indicator */}
          <div className="flex items-center text-slate-500">
            {saveStatus === 'saving' ? (
              <span className="animate-pulse text-amber-600 font-medium">Autosaving...</span>
            ) : (
              <span className="flex items-center text-emerald-600 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                All changes saved
              </span>
            )}
          </div>

          {/* Countdown Timer */}
          {secondsLeft !== null && (
            <div
              className={`flex items-center font-mono font-bold px-3 py-1 rounded-md border ${
                secondsLeft < 300
                  ? 'bg-red-50 border-red-300 text-red-700 animate-pulse'
                  : 'bg-slate-50 border-slate-200 text-slate-800'
              }`}
            >
              <Clock className="w-3.5 h-3.5 mr-1.5" />
              <span>{formatTimer(secondsLeft)}</span>
            </div>
          )}

          <button
            onClick={() => setShowConfirmSubmit(true)}
            className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-sm flex items-center transition-colors"
          >
            <Send className="w-3.5 h-3.5 mr-1.5" />
            Finish & Submit
          </button>
        </div>
      </header>

      {/* Main Examination View */}
      <div className="flex-1 max-w-5xl w-full mx-auto p-6 flex flex-col md:flex-row gap-6">
        {/* Question Area */}
        <div className="flex-1 bg-white p-8 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            {/* Question metadata row */}
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <span className="px-2 py-0.5 rounded bg-slate-100 font-bold text-xs text-slate-800">
                  Question {currentIndex + 1} of {questions.length}
                </span>
                <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold text-[11px] uppercase tracking-wider">
                  {currentQ.type.replace(/_/g, ' ')}
                </span>
              </div>
              <span className="font-mono text-xs font-bold text-slate-700">
                {currentQ.marks} Marks
              </span>
            </div>

            {/* Prompt text */}
            <div className="mt-5 space-y-4">
              <p className="text-base font-semibold text-slate-900 whitespace-pre-wrap leading-relaxed">
                {currentQ.prompt}
              </p>

              {/* Code snippet if present */}
              {currentQ.content_data?.code_snippet && (
                <pre className="p-4 bg-slate-900 text-slate-100 rounded-lg font-mono text-xs overflow-x-auto">
                  <code>{currentQ.content_data.code_snippet}</code>
                </pre>
              )}

              {/* Objective Question Choices */}
              {currentQ.content_data?.options && (
                <div className="space-y-2 pt-2">
                  {currentQ.content_data.options.map((opt: any) => {
                    const isSelected = currentAnswer.selected_option === opt.id;
                    return (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() =>
                          handleAnswerChange(currentQ.item_id, { selected_option: opt.id })
                        }
                        className={`w-full p-3.5 rounded-xl border text-left text-xs font-medium transition-all flex items-start space-x-3 ${
                          isSelected
                            ? 'border-indigo-600 bg-indigo-50 text-indigo-950 ring-2 ring-indigo-500/20'
                            : 'border-slate-200 hover:border-slate-300 bg-white text-slate-800'
                        }`}
                      >
                        <span
                          className={`w-5 h-5 rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0 border ${
                            isSelected
                              ? 'bg-indigo-600 text-white border-indigo-600'
                              : 'bg-white text-slate-600 border-slate-300'
                          }`}
                        >
                          {opt.id}
                        </span>
                        <span className="self-center">{opt.text}</span>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Written Text Answer Input */}
              {!currentQ.content_data?.options && (
                <div className="pt-2">
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                    Your Response:
                  </label>
                  <textarea
                    rows={6}
                    placeholder="Type your academic solution, derivation, or reasoning here..."
                    value={currentAnswer.text || ''}
                    onChange={(e) =>
                      handleAnswerChange(currentQ.item_id, { text: e.target.value })
                    }
                    className="w-full p-3.5 text-sm border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-indigo-600"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Navigation Controls */}
          <div className="mt-8 pt-4 border-t border-slate-100 flex items-center justify-between">
            <button
              disabled={currentIndex === 0}
              onClick={() => setCurrentIndex((prev) => prev - 1)}
              className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-30 flex items-center"
            >
              <ArrowLeft className="w-3.5 h-3.5 mr-1.5" /> Previous
            </button>

            {currentIndex < questions.length - 1 ? (
              <button
                onClick={() => setCurrentIndex((prev) => prev + 1)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center shadow-sm"
              >
                Next <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
              </button>
            ) : (
              <button
                onClick={() => setShowConfirmSubmit(true)}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold flex items-center shadow-sm"
              >
                Submit Paper <Send className="w-3.5 h-3.5 ml-1.5" />
              </button>
            )}
          </div>
        </div>

        {/* Sidebar Question Palette */}
        <aside className="w-full md:w-64 bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-fit space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Question Palette</h4>
            <span className="text-xs text-slate-400 font-mono">
              {answeredCount}/{questions.length}
            </span>
          </div>

          <div className="grid grid-cols-5 gap-2">
            {questions.map((q, idx) => {
              const isAnswered = Boolean(answers[q.item_id]);
              const isCurrent = idx === currentIndex;
              return (
                <button
                  key={q.item_id}
                  onClick={() => setCurrentIndex(idx)}
                  className={`h-9 rounded-lg font-bold text-xs transition-all flex items-center justify-center border ${
                    isCurrent
                      ? 'border-indigo-600 bg-indigo-600 text-white shadow-sm'
                      : isAnswered
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-800'
                      : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>

          <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500 space-y-1">
            <div className="flex items-center">
              <span className="w-2.5 h-2.5 rounded bg-emerald-500 mr-2"></span> Answered
            </div>
            <div className="flex items-center">
              <span className="w-2.5 h-2.5 rounded bg-slate-200 mr-2"></span> Unanswered
            </div>
            <div className="flex items-center">
              <span className="w-2.5 h-2.5 rounded bg-indigo-600 mr-2"></span> Active Question
            </div>
          </div>
        </aside>
      </div>

      {/* Confirmation Submit Modal */}
      {showConfirmSubmit && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-sm w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center">
              <Send className="w-4 h-4 mr-2 text-indigo-600" />
              Submit Assessment?
            </h3>
            <p className="text-xs text-slate-600">
              You have answered <span className="font-bold text-slate-900">{answeredCount}</span> of{' '}
              <span className="font-bold text-slate-900">{questions.length}</span> questions.
              {answeredCount < questions.length && (
                <span className="block mt-1 text-amber-700 font-semibold">
                  Warning: You have {questions.length - answeredCount} unanswered questions!
                </span>
              )}
            </p>
            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100 text-xs">
              <button
                type="button"
                onClick={() => setShowConfirmSubmit(false)}
                className="px-3 py-1.5 border border-slate-300 rounded-lg font-semibold text-slate-600 hover:bg-slate-50"
              >
                Continue Reviewing
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg shadow-sm disabled:opacity-50"
              >
                {isSubmitting ? 'Submitting...' : 'Yes, Submit Now'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
