import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import {
  FileCheck,
  CheckCircle2,
  Clock,
  BookOpen,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Award,
} from 'lucide-react';

interface TopicMastery {
  topic: string;
  subject: string;
  total_items: number;
  total_attempts: number;
  average_mastery_pct: number;
  status: 'mastered' | 'proficient' | 'needs_reinforcement';
}

interface StudentPerformanceMap {
  student_id: string;
  student_name: string;
  class_name: string;
  section_name: string;
  total_assessments_taken: number;
  average_score_pct: number;
  topic_mastery: TopicMastery[];
  materials_completed_count: number;
}

export const StudentDashboard: React.FC = () => {
  const { user } = useAuth();
  const [enrollments, setEnrollments] = useState<any[]>([]);
  const [performanceMap, setPerformanceMap] = useState<StudentPerformanceMap | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const eRes = await apiRequest<any[]>('/student-enrollments');
        setEnrollments(eRes);

        const pRes = await apiRequest<StudentPerformanceMap>('/student/performance-map');
        setPerformanceMap(pRes);
      } catch (err) {
        console.error('Failed to load student dashboard metadata', err);
      }
    }
    load();
  }, []);

  const myEnrollment = enrollments[0];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Welcome, {user?.full_name}</h2>
        <p className="text-sm text-slate-500 mt-1">
          {myEnrollment ? `${myEnrollment.class_name} • Section ${myEnrollment.section_name} (Roll: ${myEnrollment.roll_number || 'N/A'})` : 'Student Learning Portal'}
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">0</div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Upcoming Tests</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <FileCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">
              {performanceMap?.total_assessments_taken || 0}
            </div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Assessments Taken</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">
              {performanceMap?.average_score_pct || 0}%
            </div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Cumulative Average</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">
              {performanceMap?.materials_completed_count || 0}
            </div>
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Materials Read</div>
          </div>
        </div>
      </div>

      {/* Private Performance Map Section */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Award className="w-5 h-5 text-indigo-600" />
              <h3 className="text-base font-bold text-slate-900">Personal Topic Mastery & Strength Map</h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Your real-time concept mastery across assessed chapters and distributed curriculum notes.
            </p>
          </div>
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 self-start sm:self-auto">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            Strictly Private to You
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
          {performanceMap?.topic_mastery && performanceMap.topic_mastery.length > 0 ? (
            performanceMap.topic_mastery.map((tm, idx) => (
              <div key={idx} className="p-4 bg-slate-50 rounded-lg border border-slate-100 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-800 truncate">{tm.topic}</span>
                  <span
                    className={`font-semibold px-2 py-0.5 rounded text-[10px] uppercase tracking-wider ${
                      tm.status === 'mastered'
                        ? 'bg-emerald-100 text-emerald-800'
                        : tm.status === 'proficient'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-rose-100 text-rose-800'
                    }`}
                  >
                    {tm.status}
                  </span>
                </div>
                <div className="flex justify-between text-xs text-slate-500 font-medium">
                  <span>Accuracy</span>
                  <span className="font-bold text-slate-900">{tm.average_mastery_pct}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full ${
                      tm.average_mastery_pct >= 80 ? 'bg-emerald-500' : tm.average_mastery_pct >= 60 ? 'bg-blue-500' : 'bg-rose-500'
                    }`}
                    style={{ width: `${tm.average_mastery_pct}%` }}
                  />
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full py-8 text-center text-xs text-slate-400">
              <CheckCircle2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              Your personalized topic mastery map will populate as you complete evaluations and review materials.
            </div>
          )}
        </div>
      </div>

      {/* My Learning Quick Banner */}
      <div className="bg-gradient-to-r from-indigo-900 to-slate-900 text-white rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-white/10 rounded-lg text-indigo-300">
            <BookOpen className="w-7 h-7" />
          </div>
          <div>
            <h3 className="font-bold text-base text-white">Curriculum Notes & Reference Guides</h3>
            <p className="text-xs text-slate-300 mt-0.5">
              Access handouts, chapter notes, and learning materials distributed to your class section.
            </p>
          </div>
        </div>
        <Link
          to="/student/my-learning"
          className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-600 text-white font-medium text-xs hover:bg-indigo-500 transition shadow-sm whitespace-nowrap self-start sm:self-auto"
        >
          <span>Open My Learning</span>
          <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
        </Link>
      </div>

      {/* Assigned Assessments Container */}
      <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm text-center">
        <FileCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-800">No Assessments Assigned Right Now</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
          When your teachers publish tests, quizzes, or practice worksheets for your section, they will appear here with instructions and time limits.
        </p>
      </div>
    </div>
  );
};
