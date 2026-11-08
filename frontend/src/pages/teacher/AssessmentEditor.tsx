import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import {
  CheckCircle,
  AlertCircle,
  ArrowUp,
  ArrowDown,
  Trash2,
  RefreshCw,
  Edit2,
  Key,
  ShieldCheck,
  Check,
} from 'lucide-react';

export const AssessmentEditor: React.FC = () => {
  const { assessmentId } = useParams<{ assessmentId: string }>();

  const [assessment, setAssessment] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Item edit state
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [editPrompt, setEditPrompt] = useState('');
  const [editMarks, setEditMarks] = useState(1);

  // Item regenerate modal state
  const [regenItemId, setRegenItemId] = useState<string | null>(null);
  const [regenFeedback, setRegenFeedback] = useState('');
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Toggle answer keys visibility for teacher review
  const [showAnswerKeys, setShowAnswerKeys] = useState(true);

  const loadAssessment = async () => {
    try {
      const data = await apiRequest<any>(`/assessments/${assessmentId}`);
      setAssessment(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load assessment');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAssessment();
  }, [assessmentId]);

  const handleStartEdit = (item: any) => {
    setEditingItemId(item.id);
    setEditPrompt(item.question.prompt);
    setEditMarks(item.marks_override !== null ? item.marks_override : item.question.marks);
  };

  const handleSaveEdit = async (itemId: string) => {
    try {
      const updated = await apiRequest<any>(`/assessments/${assessmentId}/items/${itemId}`, {
        method: 'PATCH',
        body: JSON.stringify({
          prompt: editPrompt,
          marks: Number(editMarks),
        }),
      });
      setAssessment(updated);
      setEditingItemId(null);
      setMessage('Question updated successfully.');
    } catch (err: any) {
      setError(err.message || 'Failed to save question edit');
    }
  };

  const handleDeleteItem = async (itemId: string) => {
    if (!window.confirm('Are you sure you want to remove this question?')) return;
    try {
      const updated = await apiRequest<any>(`/assessments/${assessmentId}/items/${itemId}`, {
        method: 'DELETE',
      });
      setAssessment(updated);
      setMessage('Question removed.');
    } catch (err: any) {
      setError(err.message || 'Failed to delete question');
    }
  };

  const handleMove = async (index: number, direction: 'up' | 'down') => {
    if (!assessment) return;
    const items = [...assessment.items];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= items.length) return;

    const temp = items[index];
    items[index] = items[targetIndex];
    items[targetIndex] = temp;

    const orderedIds = items.map((i) => i.id);
    try {
      const updated = await apiRequest<any>(`/assessments/${assessmentId}/reorder`, {
        method: 'POST',
        body: JSON.stringify(orderedIds),
      });
      setAssessment(updated);
    } catch (err: any) {
      setError(err.message || 'Failed to reorder items');
    }
  };

  const handleRegenerateItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regenItemId || !regenFeedback) return;
    setIsRegenerating(true);
    try {
      const updated = await apiRequest<any>(
        `/assessments/${assessmentId}/items/${regenItemId}/regenerate`,
        {
          method: 'POST',
          body: JSON.stringify({ feedback: regenFeedback }),
        }
      );
      setAssessment(updated);
      setRegenItemId(null);
      setRegenFeedback('');
      setMessage('Item regenerated successfully without losing other edits.');
    } catch (err: any) {
      setError(err.message || 'Failed to regenerate item');
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleApprove = async () => {
    try {
      const approved = await apiRequest<any>(`/assessments/${assessmentId}/approve`, {
        method: 'POST',
      });
      setAssessment(approved);
      setMessage('Assessment approved! It is now signed off and ready for scheduling/publishing.');
    } catch (err: any) {
      setError(err.message || 'Failed to approve assessment');
    }
  };

  if (isLoading) {
    return <div className="p-12 text-center text-slate-500">Loading assessment draft...</div>;
  }

  if (!assessment) {
    return <div className="p-12 text-center text-red-500">Assessment not found.</div>;
  }

  const isApproved = assessment.status === 'approved';

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                isApproved ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
              }`}
            >
              {assessment.status.replace('_', ' ')}
            </span>
            <span className="text-xs text-slate-400 font-mono">v{assessment.version}</span>
            <span className="text-xs text-slate-500 font-semibold uppercase">
              • {assessment.type.replace('_', ' ')}
            </span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mt-2">{assessment.title}</h2>
          <p className="text-xs text-slate-500 mt-1">
            Total Weight: <span className="font-bold text-slate-800">{assessment.total_marks} Marks</span> • {assessment.items.length} Questions
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowAnswerKeys(!showAnswerKeys)}
            className="px-3 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 flex items-center transition-colors"
          >
            <Key className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
            {showAnswerKeys ? 'Hide Answer Keys' : 'Review Answer Keys'}
          </button>

          {!isApproved ? (
            <button
              onClick={handleApprove}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg shadow-sm flex items-center transition-colors"
            >
              <CheckCircle className="w-4 h-4 mr-1.5" />
              Approve Assessment (Sign Off)
            </button>
          ) : (
            <div className="px-3 py-2 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs font-semibold flex items-center">
              <Check className="w-4 h-4 mr-1.5" /> Approved & Signed Off
            </div>
          )}
        </div>
      </div>

      {/* Mandatory review banner */}
      {!isApproved && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start space-x-3 text-xs text-amber-900">
          <ShieldCheck className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Human Verification Required: </span>
            Please review the prompts, mark weights, and answer keys below. You can modify questions, reorder them, or regenerate individual items before approving.
          </div>
        </div>
      )}

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

      {/* Questions list */}
      <div className="space-y-4">
        {assessment.items.map((item: any, idx: number) => {
          const q = item.question;
          const isEditing = editingItemId === item.id;
          const marks = item.marks_override !== null ? item.marks_override : q.marks;

          return (
            <div
              key={item.id}
              className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3 transition-all"
            >
              {/* Question header row */}
              <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                <div className="flex items-center space-x-2">
                  <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-xs">
                    {idx + 1}
                  </span>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 uppercase tracking-wider">
                    {q.type.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs text-slate-400 capitalize">• {q.difficulty}</span>
                </div>

                <div className="flex items-center space-x-1.5">
                  <span className="text-xs font-bold font-mono text-slate-700 mr-2">{marks} Marks</span>

                  {/* Reorder buttons */}
                  <button
                    disabled={idx === 0 || isApproved}
                    onClick={() => handleMove(idx, 'up')}
                    className="p-1 rounded text-slate-400 hover:text-slate-600 disabled:opacity-30"
                    title="Move Up"
                  >
                    <ArrowUp className="w-3.5 h-3.5" />
                  </button>
                  <button
                    disabled={idx === assessment.items.length - 1 || isApproved}
                    onClick={() => handleMove(idx, 'down')}
                    className="p-1 rounded text-slate-400 hover:text-slate-600 disabled:opacity-30"
                    title="Move Down"
                  >
                    <ArrowDown className="w-3.5 h-3.5" />
                  </button>

                  {!isApproved && (
                    <>
                      <button
                        onClick={() => handleStartEdit(item)}
                        className="p-1 rounded text-slate-400 hover:text-indigo-600"
                        title="Edit Question"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => {
                          setRegenItemId(item.id);
                          setRegenFeedback('');
                        }}
                        className="p-1 rounded text-slate-400 hover:text-indigo-600"
                        title="Regenerate Item"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteItem(item.id)}
                        className="p-1 rounded text-slate-400 hover:text-red-600"
                        title="Delete Question"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Question Body */}
              {isEditing ? (
                <div className="space-y-3 pt-2">
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 uppercase">Question Prompt</label>
                    <textarea
                      rows={3}
                      value={editPrompt}
                      onChange={(e) => setEditPrompt(e.target.value)}
                      className="mt-1 w-full p-2.5 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
                    />
                  </div>
                  <div className="flex items-center space-x-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-600 uppercase">Mark Weight</label>
                      <input
                        type="number"
                        min="1"
                        max="20"
                        value={editMarks}
                        onChange={(e) => setEditMarks(Number(e.target.value))}
                        className="mt-1 w-24 p-1.5 text-sm border border-slate-300 rounded outline-none"
                      />
                    </div>
                    <div className="self-end flex space-x-2">
                      <button
                        type="button"
                        onClick={() => handleSaveEdit(item.id)}
                        className="px-3 py-1.5 bg-indigo-600 text-white rounded text-xs font-semibold hover:bg-indigo-700"
                      >
                        Save Edits
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingItemId(null)}
                        className="px-3 py-1.5 border border-slate-300 rounded text-xs text-slate-600 hover:bg-slate-50"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-3 pt-1">
                  <p className="text-sm font-medium text-slate-900 whitespace-pre-wrap">{q.prompt}</p>

                  {/* Code snippet if present */}
                  {q.content_data?.code_snippet && (
                    <pre className="p-3 bg-slate-900 text-slate-100 rounded-lg font-mono text-xs overflow-x-auto">
                      <code>{q.content_data.code_snippet}</code>
                    </pre>
                  )}

                  {/* Options if objective */}
                  {q.content_data?.options && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                      {q.content_data.options.map((opt: any) => (
                        <div
                          key={opt.id}
                          className="p-2.5 rounded-lg border border-slate-200 bg-slate-50 text-xs text-slate-700 flex items-start"
                        >
                          <span className="font-bold text-indigo-600 mr-2">{opt.id}.</span>
                          <span>{opt.text}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Match pairs if match_the_following */}
                  {q.content_data?.match_pairs && (
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1">
                      {q.content_data.match_pairs.map((mp: any, mIdx: number) => (
                        <div key={mIdx} className="flex justify-between text-slate-700">
                          <span className="font-medium">{mp.left}</span>
                          <span className="text-slate-400">↔</span>
                          <span className="font-mono text-slate-900">{mp.right}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Teacher-only Answer Key & Rationale Panel */}
              {showAnswerKeys && q.answer_data && (
                <div className="mt-3 pt-3 border-t border-dashed border-indigo-100 bg-indigo-50/40 p-3 rounded-lg text-xs space-y-1">
                  <div className="flex items-center text-indigo-900 font-bold uppercase tracking-wider text-[11px]">
                    <Key className="w-3 h-3 mr-1 text-indigo-600" />
                    Teacher Answer Key & Marking Guide (Hidden from Students)
                  </div>
                  <div className="text-slate-800">
                    <span className="font-semibold text-slate-900">Expected: </span>
                    {q.answer_data.expected_answer}
                  </div>
                  {q.answer_data.marking_scheme && (
                    <div className="text-slate-600">
                      <span className="font-semibold text-slate-900">Marking Scheme: </span>
                      {q.answer_data.marking_scheme}
                    </div>
                  )}
                  {q.answer_data.rationale && (
                    <div className="text-slate-500 italic mt-0.5">
                      Rationale: {q.answer_data.rationale}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Single-Item Regenerate Modal */}
      {regenItemId && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center">
              <RefreshCw className="w-4 h-4 mr-2 text-indigo-600" />
              Regenerate Item with Feedback
            </h3>
            <p className="text-xs text-slate-500">
              Provide specific instructions for adjusting this question. All other items and teacher edits are preserved.
            </p>
            <form onSubmit={handleRegenerateItem} className="space-y-4">
              <textarea
                required
                rows={3}
                placeholder="e.g. Make it a numerical calculation with given values, or emphasize ISC board phrasing"
                value={regenFeedback}
                onChange={(e) => setRegenFeedback(e.target.value)}
                className="w-full p-2.5 text-xs border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
              />
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setRegenItemId(null)}
                  className="px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isRegenerating}
                  className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold disabled:opacity-50"
                >
                  {isRegenerating ? 'Regenerating...' : 'Regenerate Item'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
