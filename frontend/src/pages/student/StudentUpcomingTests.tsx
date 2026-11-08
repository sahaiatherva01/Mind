import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import { FileCheck, Clock, CheckCircle2, Play, Eye } from 'lucide-react';

export const StudentUpcomingTests: React.FC = () => {
  const [assignments, setAssignments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiRequest<any[]>('/student/assignments');
        setAssignments(data);
      } catch (err) {
        console.error('Failed to load assignments', err);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Assigned Tests & Worksheets</h2>
        <p className="text-sm text-slate-500 mt-1">
          Assessments published by your teachers for your enrolled section.
        </p>
      </div>

      {isLoading ? (
        <div className="p-12 text-center text-slate-400 bg-white rounded-xl border border-slate-200">
          Loading assigned work...
        </div>
      ) : assignments.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200 space-y-2">
          <FileCheck className="w-12 h-12 text-slate-300 mx-auto mb-2" />
          <h3 className="text-base font-bold text-slate-800">No Tests Assigned</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            When tests or practice worksheets are scheduled for your section, they will appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {assignments.map((asmt) => {
            const isSubmitted = asmt.attempt_status === 'submitted';
            const inProgress = asmt.attempt_status === 'in_progress';
            const isReleased = asmt.is_released;

            return (
              <div
                key={asmt.id}
                className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between hover:border-indigo-300 transition-all"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700">
                      {asmt.type.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-slate-500 font-semibold font-mono">
                      {asmt.total_marks} Marks
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-slate-900 mt-3">{asmt.title}</h3>

                  <div className="mt-3 space-y-1.5 text-xs text-slate-500">
                    {asmt.duration_minutes && (
                      <div className="flex items-center">
                        <Clock className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
                        <span>Duration: {asmt.duration_minutes} Minutes</span>
                      </div>
                    )}
                    {asmt.ends_at && (
                      <div className="flex items-center">
                        <Clock className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
                        <span>Closes: {new Date(asmt.ends_at).toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between">
                  {isReleased ? (
                    <Link
                      to={`/student/results?attempt_id=${asmt.attempt_id}`}
                      className="inline-flex items-center px-3 py-1.5 rounded-lg bg-purple-50 text-purple-700 hover:bg-purple-100 text-xs font-semibold transition-colors"
                    >
                      <Eye className="w-3.5 h-3.5 mr-1.5" />
                      View Released Results
                    </Link>
                  ) : isSubmitted ? (
                    <span className="inline-flex items-center text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-md">
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                      Submitted (Results Pending Release)
                    </span>
                  ) : (
                    <Link
                      to={`/student/player/${asmt.id}`}
                      className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-colors"
                    >
                      <Play className="w-3.5 h-3.5 mr-1.5" />
                      {inProgress ? 'Resume Attempt' : 'Start Assessment'}
                    </Link>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
