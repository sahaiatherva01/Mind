import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../api/client';
import {
  BookOpen,
  FileText,
  ExternalLink,
  CheckCircle2,
  Clock,
  Search,
  Filter,
  X,
  Eye,
} from 'lucide-react';

interface StudentMaterial {
  id: string;
  title: string;
  description?: string;
  file_url: string;
  file_type: string;
  file_size_bytes: number;
  subject_id: string;
  subject_name: string;
  class_id: string;
  class_name: string;
  chapter?: string;
  topic?: string;
  content_text?: string;
  created_at: string;
  has_opened: boolean;
  last_opened_at?: string;
}

export const StudentMyLearning: React.FC = () => {
  const [materials, setMaterials] = useState<StudentMaterial[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSubjectFilter, setSelectedSubjectFilter] = useState('');

  // Reader Modal State
  const [activeMaterial, setActiveMaterial] = useState<StudentMaterial | null>(null);

  const loadMaterials = async () => {
    setIsLoading(true);
    try {
      const res = await apiRequest<StudentMaterial[]>('/student/my-learning');
      setMaterials(res);
    } catch (err: any) {
      console.error('Failed to load student learning materials', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMaterials();
  }, []);

  const handleOpenMaterial = async (mat: StudentMaterial) => {
    setActiveMaterial(mat);

    // Track open event with backend
    try {
      await apiRequest(`/student/my-learning/${mat.id}/open`, {
        method: 'POST',
        body: JSON.stringify({ duration_seconds: 60, pages_read: 1 }),
      });

      // Update local state to reflect that it's now opened
      setMaterials((prev) =>
        prev.map((item) =>
          item.id === mat.id
            ? { ...item, has_opened: true, last_opened_at: new Date().toISOString() }
            : item
        )
      );
    } catch (err: any) {
      console.error('Failed to log material open engagement', err);
    }
  };

  const distinctSubjects = Array.from(new Set(materials.map((m) => m.subject_name)));

  const filteredMaterials = materials.filter((m) => {
    if (selectedSubjectFilter && m.subject_name !== selectedSubjectFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchTitle = m.title.toLowerCase().includes(q);
      const matchChapter = m.chapter?.toLowerCase().includes(q) || false;
      const matchTopic = m.topic?.toLowerCase().includes(q) || false;
      if (!matchTitle && !matchChapter && !matchTopic) return false;
    }
    return true;
  });

  const readCount = materials.filter((m) => m.has_opened).length;
  const unreadCount = materials.length - readCount;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">My Learning Library</h2>
        <p className="text-sm text-slate-500 mt-1">
          Handouts, revision guides, and reference materials shared directly by your teachers.
        </p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{materials.length}</div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Total Materials
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{unreadCount}</div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              New / Unread
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{readCount}</div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Completed Readings
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by chapter, title, topic..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3.5 py-1.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={selectedSubjectFilter}
            onChange={(e) => setSelectedSubjectFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Subjects</option>
            {distinctSubjects.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Materials Grid */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-500">Loading your learning materials...</div>
      ) : filteredMaterials.length === 0 ? (
        <div className="bg-white p-12 rounded-xl border border-slate-200 text-center shadow-sm">
          <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-800">No Learning Materials Found</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
            When your teachers share reading handouts or reference materials for your section, they will appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredMaterials.map((m) => (
            <div
              key={m.id}
              className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col justify-between hover:shadow-md transition"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="px-2.5 py-1 rounded text-[11px] font-bold bg-indigo-50 text-indigo-700 uppercase tracking-wider">
                    {m.subject_name}
                  </span>
                  {m.has_opened ? (
                    <span className="inline-flex items-center text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-600" />
                      Read
                    </span>
                  ) : (
                    <span className="inline-flex items-center text-[11px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                      New
                    </span>
                  )}
                </div>

                <h3 className="font-bold text-slate-900 text-base leading-snug line-clamp-2">
                  {m.title}
                </h3>

                {m.chapter && (
                  <p className="text-xs text-slate-500 mt-1">
                    Chapter: <span className="font-semibold text-slate-700">{m.chapter}</span>
                  </p>
                )}

                {m.description && (
                  <p className="text-xs text-slate-600 mt-2 line-clamp-3 leading-relaxed">
                    {m.description}
                  </p>
                )}
              </div>

              <div className="mt-5 pt-3.5 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-400">
                  Shared {new Date(m.created_at).toLocaleDateString()}
                </span>
                <button
                  onClick={() => handleOpenMaterial(m)}
                  className="inline-flex items-center px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-medium text-xs hover:bg-indigo-700 transition shadow-sm"
                >
                  <Eye className="w-3.5 h-3.5 mr-1" />
                  Read Material
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Reader Modal */}
      {activeMaterial && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-3xl w-full p-6 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-slate-200 flex-shrink-0">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">{activeMaterial.title}</h3>
                  <p className="text-xs text-slate-500">
                    {activeMaterial.subject_name} • {activeMaterial.class_name}
                    {activeMaterial.chapter && ` • ${activeMaterial.chapter}`}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setActiveMaterial(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-5 space-y-4 text-sm text-slate-700 leading-relaxed">
              {activeMaterial.description && (
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 italic">
                  {activeMaterial.description}
                </div>
              )}

              {activeMaterial.content_text ? (
                <div className="prose prose-sm max-w-none bg-slate-50 p-4 rounded-xl border border-slate-200 whitespace-pre-wrap font-sans">
                  {activeMaterial.content_text}
                </div>
              ) : (
                <div className="p-8 text-center text-slate-500 bg-slate-50 rounded-xl border border-slate-200">
                  <FileText className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                  <p className="text-xs">
                    This material is stored as a document file. Click below to view or download.
                  </p>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-200 flex items-center justify-between flex-shrink-0">
              <a
                href={activeMaterial.file_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 rounded-lg bg-slate-100 text-slate-700 font-medium text-xs hover:bg-slate-200 transition"
              >
                <ExternalLink className="w-3.5 h-3.5 mr-1.5" />
                Open External File / PDF
              </a>
              <button
                onClick={() => setActiveMaterial(null)}
                className="px-4 py-2 rounded-lg bg-indigo-600 text-white font-medium text-xs hover:bg-indigo-700 transition"
              >
                Done Reading
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
