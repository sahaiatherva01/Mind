import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../api/client';
import { Plus, UserCheck, AlertCircle } from 'lucide-react';

export const AcademicSetup: React.FC = () => {
  const [classes, setClasses] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'classes' | 'subjects' | 'assignments'>('classes');

  // Form states
  const [newClassName, setNewClassName] = useState('');
  const [newClassSections, setNewClassSections] = useState('A, B');
  const [newSubjectName, setNewSubjectName] = useState('');
  const [newSubjectCode, setNewSubjectCode] = useState('');
  const [selectedTeacherId, setSelectedTeacherId] = useState('');
  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedSectionId, setSelectedSectionId] = useState('');
  const [selectedSubjectId, setSelectedSubjectId] = useState('');

  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [cRes, sRes, aRes, uRes] = await Promise.all([
        apiRequest<any[]>('/classes'),
        apiRequest<any[]>('/subjects'),
        apiRequest<any[]>('/teacher-assignments'),
        apiRequest<any[]>('/users?limit=200'),
      ]);
      setClasses(cRes);
      setSubjects(sRes);
      setAssignments(aRes);
      setUsers(uRes);
    } catch (err: any) {
      setError(err.message || 'Failed to load academic setup data');
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateClass = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    try {
      // Find academic year
      const me = await apiRequest<any>('/auth/me');
      const yearId = me.active_academic_year_id || 'default';
      const sections = newClassSections.split(',').map((s) => s.trim()).filter(Boolean);

      await apiRequest('/classes', {
        method: 'POST',
        body: JSON.stringify({
          academic_year_id: yearId,
          name: newClassName,
          section_names: sections,
        }),
      });
      setMessage(`Class '${newClassName}' created successfully!`);
      setNewClassName('');
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to create class');
    }
  };

  const handleCreateSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await apiRequest('/subjects', {
        method: 'POST',
        body: JSON.stringify({
          name: newSubjectName,
          code: newSubjectCode.toUpperCase(),
        }),
      });
      setMessage(`Subject '${newSubjectName}' created successfully!`);
      setNewSubjectName('');
      setNewSubjectCode('');
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to create subject');
    }
  };

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await apiRequest('/teacher-assignments', {
        method: 'POST',
        body: JSON.stringify({
          teacher_id: selectedTeacherId,
          class_id: selectedClassId,
          section_id: selectedSectionId,
          subject_id: selectedSubjectId,
        }),
      });
      setMessage('Teacher assigned successfully!');
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to assign teacher');
    }
  };

  const teachers = users.filter((u) => u.role === 'teacher' || u.role === 'admin');
  const selectedClass = classes.find((c) => c.id === selectedClassId);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Academic Structure & Assignments</h2>
        <p className="text-sm text-slate-500 mt-1">
          Define grades, sections, ICSE/ISC subjects, and explicit teacher-class assignments.
        </p>
      </div>

      {message && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-800">
          {message}
        </div>
      )}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800 flex items-center">
          <AlertCircle className="w-4 h-4 mr-2 text-red-500" />
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200 flex space-x-6">
        <button
          onClick={() => setActiveTab('classes')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'classes'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          Classes & Sections ({classes.length})
        </button>
        <button
          onClick={() => setActiveTab('subjects')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'subjects'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          Subjects Catalogue ({subjects.length})
        </button>
        <button
          onClick={() => setActiveTab('assignments')}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'assignments'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          Teacher Assignments ({assignments.length})
        </button>
      </div>

      {/* Classes Tab */}
      {activeTab === 'classes' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3 text-left">Class Name</th>
                    <th className="px-6 py-3 text-left">Sections Configured</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white">
                  {classes.map((c) => (
                    <tr key={c.id}>
                      <td className="px-6 py-4 font-medium text-slate-900">{c.name}</td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1.5">
                          {c.sections?.map((s: any) => (
                            <span
                              key={s.id}
                              className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-xs font-mono font-semibold"
                            >
                              Section {s.name}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-fit">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center">
              <Plus className="w-4 h-4 mr-1 text-indigo-600" />
              Add Class
            </h3>
            <form onSubmit={handleCreateClass} className="mt-4 space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Class Label</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Class 11"
                  value={newClassName}
                  onChange={(e) => setNewClassName(e.target.value)}
                  className="mt-1 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Sections (comma separated)</label>
                <input
                  type="text"
                  placeholder="A, B, C, E"
                  value={newClassSections}
                  onChange={(e) => setNewClassSections(e.target.value)}
                  className="mt-1 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm rounded-lg transition-colors shadow-sm"
              >
                Create Class
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Subjects Tab */}
      {activeTab === 'subjects' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3 text-left">Code</th>
                    <th className="px-6 py-3 text-left">Subject Name</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white">
                  {subjects.map((s) => (
                    <tr key={s.id}>
                      <td className="px-6 py-4 font-mono font-semibold text-indigo-600 text-xs">{s.code}</td>
                      <td className="px-6 py-4 font-medium text-slate-900">{s.name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-fit">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center">
              <Plus className="w-4 h-4 mr-1 text-indigo-600" />
              Add Subject
            </h3>
            <form onSubmit={handleCreateSubject} className="mt-4 space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Subject Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Computer Science"
                  value={newSubjectName}
                  onChange={(e) => setNewSubjectName(e.target.value)}
                  className="mt-1 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Subject Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CS"
                  value={newSubjectCode}
                  onChange={(e) => setNewSubjectCode(e.target.value)}
                  className="mt-1 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm rounded-lg transition-colors shadow-sm"
              >
                Create Subject
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Assignments Tab */}
      {activeTab === 'assignments' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-3 text-left">Teacher</th>
                    <th className="px-6 py-3 text-left">Assigned Class & Section</th>
                    <th className="px-6 py-3 text-left">Subject</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white">
                  {assignments.map((a) => (
                    <tr key={a.id}>
                      <td className="px-6 py-4 font-medium text-slate-900">{a.teacher_name}</td>
                      <td className="px-6 py-4">
                        <span className="font-semibold text-slate-800">{a.class_name}</span> - Section {a.section_name}
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded text-xs font-semibold">
                          {a.subject_name}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm h-fit">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center">
              <UserCheck className="w-4 h-4 mr-1 text-indigo-600" />
              Assign Teacher
            </h3>
            <form onSubmit={handleCreateAssignment} className="mt-4 space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Teacher</label>
                <select
                  required
                  value={selectedTeacherId}
                  onChange={(e) => setSelectedTeacherId(e.target.value)}
                  className="mt-1 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
                >
                  <option value="">Select Teacher...</option>
                  {teachers.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.full_name} ({t.email})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Class</label>
                <select
                  required
                  value={selectedClassId}
                  onChange={(e) => {
                    setSelectedClassId(e.target.value);
                    setSelectedSectionId('');
                  }}
                  className="mt-1 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
                >
                  <option value="">Select Class...</option>
                  {classes.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Section</label>
                <select
                  required
                  disabled={!selectedClass}
                  value={selectedSectionId}
                  onChange={(e) => setSelectedSectionId(e.target.value)}
                  className="mt-1 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600 disabled:opacity-50"
                >
                  <option value="">Select Section...</option>
                  {selectedClass?.sections?.map((s: any) => (
                    <option key={s.id} value={s.id}>
                      Section {s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase">Subject</label>
                <select
                  required
                  value={selectedSubjectId}
                  onChange={(e) => setSelectedSubjectId(e.target.value)}
                  className="mt-1 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
                >
                  <option value="">Select Subject...</option>
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.code})
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm rounded-lg transition-colors shadow-sm"
              >
                Assign Scope
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
