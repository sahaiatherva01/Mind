import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import {
  Send,
  AlertCircle,
  Eye,
  Key,
} from 'lucide-react';

export const TeacherAssessments: React.FC = () => {
  const [assessments, setAssessments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Publish modal state
  const [publishModalAsmt, setPublishModalAsmt] = useState<any | null>(null);
  const [startsAt, setStartsAt] = useState('');
  const [endsAt, setEndsAt] = useState('');
  const [durationMinutes, setDurationMinutes] = useState(45);
  const [maxAttempts, setMaxAttempts] = useState(1);
  const [releaseMode, setReleaseMode] = useState('manual_by_teacher');
  const [isPublishing, setIsPublishing] = useState(false);

  const loadAssessments = async () => {
    try {
      const data = await apiRequest<any[]>('/assessments');
      setAssessments(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load assessments');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAssessments();
    // Default start/end
    const now = new Date();
    const end = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    setStartsAt(now.toISOString().slice(0, 16));
    setEndsAt(end.toISOString().slice(0, 16));
  }, []);

  const handleOpenPublish = (asmt: any) => {
    setPublishModalAsmt(asmt);
    setError(null);
  };

  const handleExecutePublish = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!publishModalAsmt) return;
    setIsPublishing(true);
    setError(null);

    try {
      await apiRequest(`/assessments/${publishModalAsmt.id}/publish`, {
        method: 'POST',
        body: JSON.stringify({
          starts_at: new Date(startsAt).toISOString(),
          ends_at: new Date(endsAt).toISOString(),
          duration_minutes: durationMinutes ? Number(durationMinutes) : undefined,
          max_attempts: Number(maxAttempts),
          result_release_mode: releaseMode,
          timezone: 'Asia/Kolkata',
        }),
      });
      setMessage(`'${publishModalAsmt.title}' has been successfully published to students!`);
      setPublishModalAsmt(null);
      await loadAssessments();
    } catch (err: any) {
      setError(err.message || 'Failed to publish assessment');
    } finally {
      setIsPublishing(false);
    }
  };

  const handleReleaseResults = async (asmtId: string) => {
    if (!window.confirm('Are you sure you want to release scores and model solutions to all student attempts?')) return;
    try {
      const res = await apiRequest<any>(`/assessments/${asmtId}/release-results`, {
        method: 'POST',
      });
      setMessage(`Results released to ${res.released_attempts} student attempts!`);
      await loadAssessments();
    } catch (err: any) {
      setError(err.message || 'Failed to release results');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Assessments & Examination Roster</h2>
          <p className="text-sm text-slate-500 mt-1">
            Review drafts, schedule exam availability, and control result release policies.
          </p>
        </div>
        <Link
          to="/teacher/ai-studio"
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
        >
          + New Assessment in AI Studio
        </Link>
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

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
            <tr>
              <th className="px-6 py-3 text-left">Title & Format</th>
              <th className="px-6 py-3 text-left">Status</th>
              <th className="px-6 py-3 text-left">Marks & Questions</th>
              <th className="px-6 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {isLoading ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-slate-400">
                  Loading assessments...
                </td>
              </tr>
            ) : assessments.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-slate-400">
                  No assessments created yet. Start with AI Studio!
                </td>
              </tr>
            ) : (
              assessments.map((a) => {
                const isApproved = a.status === 'approved';
                const isPublished = a.status === 'published' || a.status === 'scheduled';
                const isReleased = a.status === 'results_released';

                return (
                  <tr key={a.id} className="hover:bg-slate-50/50">
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-900">{a.title}</div>
                      <div className="text-xs text-slate-400 capitalize">
                        {a.type.replace('_', ' ')} • Version {a.version}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${
                          isReleased
                            ? 'bg-purple-50 text-purple-700 border border-purple-200'
                            : isPublished
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : isApproved
                            ? 'bg-blue-50 text-blue-700 border border-blue-200'
                            : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}
                      >
                        {a.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-600 font-medium">
                      <span className="font-bold text-slate-900">{a.total_marks} Marks</span> • {a.items?.length || 0} Items
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2 text-xs">
                        <Link
                          to={`/teacher/assessments/${a.id}`}
                          className="px-2.5 py-1.5 rounded border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold flex items-center"
                        >
                          <Eye className="w-3.5 h-3.5 mr-1 text-slate-500" />
                          Editor
                        </Link>

                        {isApproved && (
                          <button
                            onClick={() => handleOpenPublish(a)}
                            className="px-2.5 py-1.5 rounded bg-indigo-600 hover:bg-indigo-700 text-white font-semibold flex items-center shadow-sm"
                          >
                            <Send className="w-3.5 h-3.5 mr-1" />
                            Publish
                          </button>
                        )}

                        {isPublished && !isReleased && (
                          <button
                            onClick={() => handleReleaseResults(a.id)}
                            className="px-2.5 py-1.5 rounded bg-purple-600 hover:bg-purple-700 text-white font-semibold flex items-center shadow-sm"
                            title="Release Marks and Rationales to Students"
                          >
                            <Key className="w-3.5 h-3.5 mr-1" />
                            Release Results
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Publish & Schedule Modal */}
      {publishModalAsmt && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center">
              <Send className="w-4 h-4 mr-2 text-indigo-600" />
              Publish Assessment to Students
            </h3>
            <p className="text-xs text-slate-500">
              Publishing will create an immutable version of <span className="font-semibold text-slate-800">{publishModalAsmt.title}</span> and deliver it to your assigned section.
            </p>

            <form onSubmit={handleExecutePublish} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 uppercase">Available From</label>
                  <input
                    type="datetime-local"
                    required
                    value={startsAt}
                    onChange={(e) => setStartsAt(e.target.value)}
                    className="mt-1 w-full p-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600 text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 uppercase">Deadline (Closes At)</label>
                  <input
                    type="datetime-local"
                    required
                    value={endsAt}
                    onChange={(e) => setEndsAt(e.target.value)}
                    className="mt-1 w-full p-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600 text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 uppercase">Exam Duration (Minutes)</label>
                  <input
                    type="number"
                    min="5"
                    max="180"
                    value={durationMinutes}
                    onChange={(e) => setDurationMinutes(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600 text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 uppercase">Max Attempts</label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={maxAttempts}
                    onChange={(e) => setMaxAttempts(Number(e.target.value))}
                    className="mt-1 w-full p-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600 text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 uppercase">Result & Solution Release Policy</label>
                <select
                  value={releaseMode}
                  onChange={(e) => setReleaseMode(e.target.value)}
                  className="mt-1 w-full p-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600 text-xs"
                >
                  <option value="manual_by_teacher">Manual (Teacher explicitly clicks 'Release Results')</option>
                  <option value="immediate_on_submit">Immediate upon Submission (For pure objective practice)</option>
                  <option value="scheduled_datetime">Scheduled Date/Time</option>
                </select>
                <p className="text-[11px] text-slate-400 mt-1">
                  Prevents answer keys and rationales from leaking before all students have submitted.
                </p>
              </div>

              <div className="flex justify-end space-x-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setPublishModalAsmt(null)}
                  className="px-3 py-1.5 border border-slate-300 rounded-lg font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isPublishing}
                  className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-sm disabled:opacity-50"
                >
                  {isPublishing ? 'Publishing...' : 'Confirm & Deliver'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
