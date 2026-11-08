import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../api/client';
import { Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

export const TeacherClasses: React.FC = () => {
  const [assignments, setAssignments] = useState<any[]>([]);
  const [curriculum, setCurriculum] = useState<any[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const [aRes, cRes] = await Promise.all([
          apiRequest<any[]>('/teacher-assignments'),
          apiRequest<any[]>('/curriculum'),
        ]);
        setAssignments(aRes);
        setCurriculum(cRes);
      } catch (err) {
        console.error('Failed to load classes', err);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">My Classes & Curriculum Workspaces</h2>
        <p className="text-sm text-slate-500 mt-1">
          Review curriculum topics, enrolled students, and assessment activity for your assigned sections.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {assignments.map((a) => (
          <div key={a.id} className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm flex flex-col justify-between">
            <div className="p-6">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700">
                  {a.subject_name}
                </span>
                <span className="text-xs font-mono font-bold text-slate-500">
                  Sec {a.section_name}
                </span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 mt-3">{a.class_name}</h3>
              <p className="text-xs text-slate-500 mt-1">
                Board: ICSE / ISC prescribed syllabus
              </p>

              {/* Sample curriculum topics */}
              <div className="mt-4 pt-4 border-t border-slate-100">
                <span className="text-xs font-semibold uppercase text-slate-400 tracking-wider">Curriculum Modules</span>
                <div className="mt-2 space-y-1.5">
                  {curriculum
                    .filter((c) => c.subject_id === a.subject_id)
                    .slice(0, 3)
                    .map((item) => (
                      <div key={item.id} className="text-xs text-slate-700 flex items-center">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mr-2"></span>
                        <span className="truncate">{item.chapter} — {item.topic}</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
              <Link
                to="/teacher/ai-studio"
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center"
              >
                <Sparkles className="w-3.5 h-3.5 mr-1 text-indigo-500" />
                Generate Assessment
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
