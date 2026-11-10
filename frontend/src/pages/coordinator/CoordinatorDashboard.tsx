import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import {
  GraduationCap,
  Users,
  Layers,
  BookOpen,
  UserCheck,
  ShieldCheck,
  ArrowRight,
} from 'lucide-react';

interface ClassItem {
  id: string;
  name: string;
  grade_level?: number;
  sections: { id: string; name: string }[];
}

interface BandSummary {
  band_id: string;
  band_name: string;
  min_grade: number;
  max_grade: number;
  classes: ClassItem[];
  total_classes: number;
  total_sections: number;
  total_teachers: number;
  total_students: number;
  class_teachers: Record<string, string | null>;
}

export const CoordinatorDashboard: React.FC = () => {
  const [summary, setSummary] = useState<BandSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const data = await apiRequest<BandSummary>('/coordinator/band-summary');
        setSummary(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load coordinator band summary');
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-rose-800">
        <p className="font-semibold">Unable to load Band Dashboard</p>
        <p className="text-sm mt-1">{error || 'No active grade band found for your account.'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-indigo-900 via-indigo-800 to-slate-900 rounded-2xl p-6 text-white shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/30 border border-indigo-400/40 text-indigo-200">
              Grade Band {summary.min_grade}–{summary.max_grade}
            </span>
            <span className="text-xs text-indigo-300 flex items-center">
              <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-400" />
              Band-Scoped Jurisdiction
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">{summary.band_name}</h1>
          <p className="text-sm text-indigo-200 mt-1">
            Academic Coordinator Workspace — Staff assignments, roster governance, and curriculum oversight.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/coordinator/assignments"
            className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors shadow"
          >
            <Layers className="w-4 h-4 mr-2" />
            Assignment Matrix
            <ArrowRight className="w-4 h-4 ml-1.5" />
          </Link>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Classes</span>
            <GraduationCap className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{summary.total_classes}</div>
          <p className="text-xs text-slate-500 mt-1">Grades {summary.min_grade} to {summary.max_grade}</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Sections</span>
            <Layers className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{summary.total_sections}</div>
          <p className="text-xs text-slate-500 mt-1">Active class sections</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Teachers</span>
            <Users className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{summary.total_teachers}</div>
          <p className="text-xs text-slate-500 mt-1">Assigned in band</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Students</span>
            <BookOpen className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{summary.total_students}</div>
          <p className="text-xs text-slate-500 mt-1">Enrolled in band sections</p>
        </div>
      </div>

      {/* Classes & Sections Structure with Class Teachers */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Band Academic Structure</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Classes, sections, and designated Class Teachers within your jurisdiction
            </p>
          </div>
          <span className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md font-medium">
            1 Class Teacher Per Section Policy Enforced
          </span>
        </div>

        <div className="divide-y divide-slate-100">
          {summary.classes.map((cls) => (
            <div key={cls.id} className="p-6">
              <div className="flex items-center gap-3 mb-3">
                <span className="font-semibold text-slate-900 text-base">{cls.name}</span>
                {cls.grade_level && (
                  <span className="text-xs font-medium px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                    Grade {cls.grade_level}
                  </span>
                )}
                <span className="text-xs text-slate-400">
                  {cls.sections.length} {cls.sections.length === 1 ? 'Section' : 'Sections'}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {cls.sections.map((sec) => {
                  const ctName = summary.class_teachers[sec.id];
                  return (
                    <div
                      key={sec.id}
                      className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/60 flex items-start justify-between"
                    >
                      <div>
                        <div className="font-medium text-sm text-slate-900">
                          {cls.name} — Section {sec.name}
                        </div>
                        <div className="mt-1 flex items-center text-xs text-slate-600">
                          <UserCheck className="w-3.5 h-3.5 mr-1 text-indigo-600 flex-shrink-0" />
                          {ctName ? (
                            <span className="font-medium text-slate-800 truncate">
                              Class Teacher: {ctName}
                            </span>
                          ) : (
                            <span className="text-amber-600 italic">No Class Teacher Assigned</span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
