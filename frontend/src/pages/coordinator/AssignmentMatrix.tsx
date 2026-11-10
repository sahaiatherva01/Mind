import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../api/client';
import {
  Layers,
  UserCheck,
  Plus,
  Trash2,
  AlertCircle,
  CheckCircle,
  X,
  Search,
  Filter,
} from 'lucide-react';

interface AssignmentItem {
  id: string;
  teacher_id: string;
  teacher_name: string;
  teacher_email: string;
  class_id: string;
  class_name: string;
  section_id: string;
  section_name: string;
  subject_id: string;
  subject_name: string;
  subject_code: string;
  is_class_teacher: boolean;
  status: string;
}

interface TeacherOption {
  id: string;
  email: string;
  full_name: string;
}

interface BandSummary {
  band_id: string;
  band_name: string;
  classes: {
    id: string;
    name: string;
    sections: { id: string; name: string }[];
  }[];
}

interface SubjectItem {
  id: string;
  name: string;
  code: string;
}

export const AssignmentMatrix: React.FC = () => {
  const [matrix, setMatrix] = useState<AssignmentItem[]>([]);
  const [bandSummary, setBandSummary] = useState<BandSummary | null>(null);
  const [subjects, setSubjects] = useState<SubjectItem[]>([]);
  const [allTeachers, setAllTeachers] = useState<TeacherOption[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [selectedTeacherId, setSelectedTeacherId] = useState<string>('');
  const [selectedClassId, setSelectedClassId] = useState<string>('');
  const [selectedSectionId, setSelectedSectionId] = useState<string>('');
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>('');
  const [isClassTeacher, setIsClassTeacher] = useState<boolean>(false);
  const [modalSubmitting, setModalSubmitting] = useState<boolean>(false);
  const [modalError, setModalError] = useState<string | null>(null);

  // Filter State
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterClass, setFilterClass] = useState<string>('all');

  const loadData = async () => {
    try {
      const [matrixData, summaryData, subjectsData, usersData] = await Promise.all([
        apiRequest<AssignmentItem[]>('/coordinator/assignments'),
        apiRequest<BandSummary>('/coordinator/band-summary'),
        apiRequest<SubjectItem[]>('/subjects'),
        apiRequest<any[]>('/users'),
      ]);

      setMatrix(matrixData);
      setBandSummary(summaryData);
      setSubjects(subjectsData);
      const teachers = usersData.filter((u: any) => u.role === 'teacher' || u.role === 'academic_coordinator');
      setAllTeachers(teachers);
    } catch (err: any) {
      setError(err.message || 'Failed to load assignment matrix');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    setModalSubmitting(true);

    try {
      await apiRequest('/coordinator/assignments', {
        method: 'POST',
        body: JSON.stringify({
          teacher_id: selectedTeacherId,
          class_id: selectedClassId,
          section_id: selectedSectionId,
          subject_id: selectedSubjectId,
          is_class_teacher: isClassTeacher,
        }),
      });

      setSuccessMsg('Assignment created successfully.');
      setIsModalOpen(false);
      // Reset form
      setSelectedTeacherId('');
      setSelectedClassId('');
      setSelectedSectionId('');
      setSelectedSubjectId('');
      setIsClassTeacher(false);
      await loadData();
    } catch (err: any) {
      setModalError(err.message || 'Failed to create assignment');
    } finally {
      setModalSubmitting(false);
    }
  };

  const handleDelete = async (assignmentId: string) => {
    if (!window.confirm('Are you sure you want to remove this teacher assignment?')) return;
    try {
      await apiRequest(`/coordinator/assignments/${assignmentId}`, { method: 'DELETE' });
      setSuccessMsg('Assignment removed.');
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to delete assignment');
    }
  };

  const selectedClass = bandSummary?.classes.find((c) => c.id === selectedClassId);
  const availableSections = selectedClass?.sections || [];

  const filteredMatrix = matrix.filter((item) => {
    const matchesSearch =
      item.teacher_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.subject_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.class_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesClass = filterClass === 'all' || item.class_id === filterClass;
    return matchesSearch && matchesClass;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Assignment Matrix</h1>
          <p className="text-sm text-slate-500 mt-1">
            Teacher × Class × Section × Subject allocation with 1 Class Teacher constraint
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setModalError(null);
            setIsModalOpen(true);
          }}
          className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4 mr-2" />
          Assign Teacher
        </button>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between">
          <div className="flex items-center">
            <CheckCircle className="w-4 h-4 mr-2 text-emerald-600" />
            {successMsg}
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-600 hover:text-emerald-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center justify-between">
          <div className="flex items-center">
            <AlertCircle className="w-4 h-4 mr-2 text-rose-600" />
            {error}
          </div>
          <button onClick={() => setError(null)} className="text-rose-600 hover:text-rose-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by teacher, class, or subject..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={filterClass}
            onChange={(e) => setFilterClass(e.target.value)}
            className="text-sm border border-slate-200 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 bg-white"
          >
            <option value="all">All Band Classes</option>
            {bandSummary?.classes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Assignment Matrix Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-slate-500 font-medium">
              <tr>
                <th className="px-6 py-3 text-left">Teacher</th>
                <th className="px-6 py-3 text-left">Class & Section</th>
                <th className="px-6 py-3 text-left">Subject</th>
                <th className="px-6 py-3 text-left">Class Teacher</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredMatrix.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400 text-sm">
                    No teacher assignments found for this filter.
                  </td>
                </tr>
              ) : (
                filteredMatrix.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900">{item.teacher_name}</div>
                      <div className="text-xs text-slate-400">{item.teacher_email}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-medium text-slate-900">{item.class_name}</span>
                      <span className="ml-1 text-slate-500">— Sec {item.section_name}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800">
                        {item.subject_name} ({item.subject_code})
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {item.is_class_teacher ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                          <UserCheck className="w-3.5 h-3.5 mr-1" />
                          Class Teacher
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">Subject Teacher</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        type="button"
                        onClick={() => handleDelete(item.id)}
                        className="text-slate-400 hover:text-rose-600 p-1 rounded transition-colors"
                        title="Delete Assignment"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Assign Teacher Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900 flex items-center">
                <Layers className="w-4 h-4 mr-2 text-indigo-600" />
                Assign Teacher to Band Section
              </h2>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateAssignment} className="p-6 space-y-4">
              {modalError && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-start">
                  <AlertCircle className="w-4 h-4 mr-1.5 flex-shrink-0 mt-0.5" />
                  <span>{modalError}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Teacher
                </label>
                <select
                  required
                  value={selectedTeacherId}
                  onChange={(e) => setSelectedTeacherId(e.target.value)}
                  className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-600 bg-white"
                >
                  <option value="">Select a Teacher...</option>
                  {allTeachers.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.full_name} ({t.email})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Class (Band)
                  </label>
                  <select
                    required
                    value={selectedClassId}
                    onChange={(e) => {
                      setSelectedClassId(e.target.value);
                      setSelectedSectionId('');
                    }}
                    className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-600 bg-white"
                  >
                    <option value="">Select Class...</option>
                    {bandSummary?.classes.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Section
                  </label>
                  <select
                    required
                    disabled={!selectedClassId}
                    value={selectedSectionId}
                    onChange={(e) => setSelectedSectionId(e.target.value)}
                    className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-600 bg-white disabled:opacity-50"
                  >
                    <option value="">Select Section...</option>
                    {availableSections.map((s) => (
                      <option key={s.id} value={s.id}>
                        Section {s.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Subject
                </label>
                <select
                  required
                  value={selectedSubjectId}
                  onChange={(e) => setSelectedSubjectId(e.target.value)}
                  className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-600 bg-white"
                >
                  <option value="">Select Subject...</option>
                  {subjects.map((sub) => (
                    <option key={sub.id} value={sub.id}>
                      {sub.name} ({sub.code})
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-2">
                <label className="flex items-start gap-2.5 p-3 rounded-lg border border-slate-200 bg-slate-50 cursor-pointer hover:bg-slate-100/70 transition-colors">
                  <input
                    type="checkbox"
                    checked={isClassTeacher}
                    onChange={(e) => setIsClassTeacher(e.target.checked)}
                    className="mt-0.5 w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500"
                  />
                  <div>
                    <span className="text-xs font-semibold text-slate-900 block">
                      Designate as Section Class Teacher
                    </span>
                    <span className="text-[11px] text-slate-500 block mt-0.5">
                      Class Teachers govern section rosters and student enrollment. Exactly one Class Teacher is allowed per section.
                    </span>
                  </div>
                </label>
              </div>

              <div className="pt-3 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalSubmitting}
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg disabled:opacity-50 transition-colors shadow-sm"
                >
                  {modalSubmitting ? 'Assigning...' : 'Confirm Assignment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

