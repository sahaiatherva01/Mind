import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../api/client';
import {
  FileText,
  Upload,
  Sparkles,
  Trash2,
  Eye,
  BookOpen,
  Filter,
  Check,
  X,
} from 'lucide-react';

interface MaterialItem {
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
  status: string;
  created_at: string;
  distributed_section_ids: string[];
  distributed_section_names: string[];
  open_count: number;
  unique_readers_count: number;
}

interface TeacherAssignment {
  id: string;
  class_id: string;
  class_name: string;
  section_id: string;
  section_name: string;
  subject_id: string;
  subject_name: string;
  is_class_teacher: boolean;
}

interface ExtractedQuestion {
  id: string;
  source_chunk_id: number;
  source_excerpt: string;
  category: string;
  type: string;
  prompt: string;
  marks: number;
  difficulty: string;
  bloom_taxonomy: string;
  options?: { id: string; text: string }[];
  answer_keys?: string[];
  expected_answer: string;
  marking_scheme: string;
  status: string;
}

export const TeacherMaterials: React.FC = () => {
  const [materials, setMaterials] = useState<MaterialItem[]>([]);
  const [assignments, setAssignments] = useState<TeacherAssignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedClassFilter, setSelectedClassFilter] = useState('');

  // Upload Modal State
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploadFileUrl, setUploadFileUrl] = useState('');
  const [uploadChapter, setUploadChapter] = useState('');
  const [uploadTopic, setUploadTopic] = useState('');
  const [uploadContentText, setUploadContentText] = useState('');
  const [selectedClassId, setSelectedClassId] = useState('');
  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [selectedSectionIds, setSelectedSectionIds] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Question Extractor State
  const [selectedMaterialForExtraction, setSelectedMaterialForExtraction] = useState<MaterialItem | null>(null);
  const [extractedQuestions, setExtractedQuestions] = useState<ExtractedQuestion[]>([]);
  const [isExtracting, setIsExtracting] = useState(false);
  const [approvedQuestionIds, setApprovedQuestionIds] = useState<Set<string>>(new Set());
  const [extractorError, setExtractorError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [matRes, asgnRes] = await Promise.all([
        apiRequest<MaterialItem[]>('/content/materials'),
        apiRequest<TeacherAssignment[]>('/teacher-assignments'),
      ]);
      setMaterials(matRes);
      setAssignments(asgnRes);

      if (asgnRes.length > 0 && !selectedClassId) {
        setSelectedClassId(asgnRes[0].class_id);
        setSelectedSubjectId(asgnRes[0].subject_id);
      }
    } catch (err: any) {
      console.error('Failed to load materials data', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filter sections available to the teacher for the chosen class and subject
  const availableSections = assignments
    .filter(
      (a) =>
        (!selectedClassId || a.class_id === selectedClassId) &&
        (!selectedSubjectId || a.subject_id === selectedSubjectId)
    )
    .map((a) => ({ id: a.section_id, name: a.section_name }));

  // Distinct classes from assignments
  const distinctClasses = Array.from(
    new Map(assignments.map((a) => [a.class_id, { id: a.class_id, name: a.class_name }])).values()
  );

  // Distinct subjects for selected class
  const distinctSubjects = Array.from(
    new Map(
      assignments
        .filter((a) => !selectedClassId || a.class_id === selectedClassId)
        .map((a) => [a.subject_id, { id: a.subject_id, name: a.subject_name }])
    ).values()
  );

  const handleSectionToggle = (secId: string) => {
    if (selectedSectionIds.includes(secId)) {
      setSelectedSectionIds(selectedSectionIds.filter((id) => id !== secId));
    } else {
      setSelectedSectionIds([...selectedSectionIds, secId]);
    }
  };

  const handleCreateMaterial = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadTitle.trim() || !uploadFileUrl.trim() || !selectedClassId || !selectedSubjectId) {
      setUploadError('Please fill in title, file URL, class, and subject.');
      return;
    }
    if (selectedSectionIds.length === 0) {
      setUploadError('Please select at least one assigned section to distribute this material to.');
      return;
    }

    setIsSubmitting(true);
    setUploadError(null);
    try {
      await apiRequest('/content/materials', {
        method: 'POST',
        body: JSON.stringify({
          title: uploadTitle.trim(),
          description: uploadDescription.trim() || null,
          file_url: uploadFileUrl.trim(),
          file_type: 'application/pdf',
          file_size_bytes: 102400,
          class_id: selectedClassId,
          subject_id: selectedSubjectId,
          chapter: uploadChapter.trim() || null,
          topic: uploadTopic.trim() || null,
          content_text: uploadContentText.trim() || null,
          target_section_ids: selectedSectionIds,
        }),
      });

      setShowUploadModal(false);
      setUploadTitle('');
      setUploadDescription('');
      setUploadFileUrl('');
      setUploadChapter('');
      setUploadTopic('');
      setUploadContentText('');
      setSelectedSectionIds([]);
      await loadData();
    } catch (err: any) {
      setUploadError(err.message || 'Failed to distribute material');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteMaterial = async (materialId: string) => {
    if (!window.confirm('Are you sure you want to archive this material? Students will no longer see it.')) {
      return;
    }
    try {
      await apiRequest(`/content/materials/${materialId}`, { method: 'DELETE' });
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to archive material');
    }
  };

  const handleOpenExtractor = async (material: MaterialItem) => {
    setSelectedMaterialForExtraction(material);
    setExtractedQuestions([]);
    setApprovedQuestionIds(new Set());
    setExtractorError(null);
    setIsExtracting(true);

    try {
      const res = await apiRequest<any>(`/content/materials/${material.id}/extract-questions`, {
        method: 'POST',
        body: JSON.stringify({ max_questions: 6 }),
      });
      setExtractedQuestions(res.questions || []);
    } catch (err: any) {
      setExtractorError(err.message || 'Failed to run question extractor');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleApproveQuestion = async (candidate: ExtractedQuestion) => {
    if (!selectedMaterialForExtraction) return;
    try {
      await apiRequest(`/content/materials/${selectedMaterialForExtraction.id}/approve-question`, {
        method: 'POST',
        body: JSON.stringify({
          candidate_question_id: candidate.id,
          prompt: candidate.prompt,
          category: candidate.category,
          type: candidate.type,
          marks: candidate.marks,
          difficulty: candidate.difficulty,
          expected_answer: candidate.expected_answer,
          marking_scheme: candidate.marking_scheme,
          options: candidate.options,
          answer_keys: candidate.answer_keys,
        }),
      });
      setApprovedQuestionIds(new Set(approvedQuestionIds).add(candidate.id));
    } catch (err: any) {
      alert(err.message || 'Failed to approve question');
    }
  };

  const filteredMaterials = materials.filter((m) => {
    if (selectedClassFilter && m.class_id !== selectedClassFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Learning Materials & PDFs</h2>
          <p className="text-sm text-slate-500 mt-1">
            Upload curriculum-grounded notes, distribute to assigned sections, and extract exam questions with AI.
          </p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="inline-flex items-center px-4 py-2.5 rounded-lg bg-indigo-600 text-white font-medium text-sm hover:bg-indigo-700 transition shadow-sm"
        >
          <Upload className="w-4 h-4 mr-2" />
          Upload & Distribute
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Filter by Class:</span>
          <select
            value={selectedClassFilter}
            onChange={(e) => setSelectedClassFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Assigned Classes</option>
            {distinctClasses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        <div className="text-xs text-slate-500">
          Showing <span className="font-semibold text-slate-700">{filteredMaterials.length}</span> active materials
        </div>
      </div>

      {/* Materials Table / List */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-500">Loading materials library...</div>
      ) : filteredMaterials.length === 0 ? (
        <div className="bg-white p-12 rounded-xl border border-slate-200 text-center shadow-sm">
          <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-800">No Learning Materials Uploaded</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-4">
            Upload syllabus notes, handouts, or reference sheets to share directly with your assigned class sections.
          </p>
          <button
            onClick={() => setShowUploadModal(true)}
            className="inline-flex items-center px-3.5 py-2 rounded-lg bg-indigo-50 text-indigo-600 font-medium text-xs hover:bg-indigo-100 transition"
          >
            <Upload className="w-3.5 h-3.5 mr-1.5" />
            Upload First Material
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 font-medium text-xs uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Material Details</th>
                <th className="px-6 py-3.5">Subject & Class</th>
                <th className="px-6 py-3.5">Distributed Sections</th>
                <th className="px-6 py-3.5">Engagement</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredMaterials.map((m) => (
                <tr key={m.id} className="hover:bg-slate-50/70 transition">
                  <td className="px-6 py-4">
                    <div className="flex items-start space-x-3">
                      <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600 flex-shrink-0 mt-0.5">
                        <FileText className="w-5 h-5" />
                      </div>
                      <div>
                        <a
                          href={m.file_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-semibold text-slate-900 hover:text-indigo-600 transition"
                        >
                          {m.title}
                        </a>
                        {m.chapter && (
                          <div className="text-xs text-slate-500 mt-0.5">
                            Chapter: <span className="font-medium text-slate-700">{m.chapter}</span>
                            {m.topic && ` • Topic: ${m.topic}`}
                          </div>
                        )}
                        <div className="text-[11px] text-slate-400 mt-1">
                          Added {new Date(m.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-medium text-slate-900">{m.subject_name}</div>
                    <div className="text-xs text-slate-500">{m.class_name}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1.5">
                      {m.distributed_section_names.length > 0 ? (
                        m.distributed_section_names.map((secName, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200"
                          >
                            Sec {secName}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-400">Undistributed</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-1.5 text-xs text-slate-700 font-medium">
                      <Eye className="w-3.5 h-3.5 text-slate-400" />
                      <span>{m.unique_readers_count} readers</span>
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      {m.open_count} total opens
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button
                      onClick={() => handleOpenExtractor(m)}
                      className="inline-flex items-center px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-semibold hover:bg-indigo-100 transition"
                      title="Run Question Extractor Agent"
                    >
                      <Sparkles className="w-3.5 h-3.5 mr-1 text-indigo-600" />
                      Extract Questions
                    </button>
                    <button
                      onClick={() => handleDeleteMaterial(m.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition"
                      title="Archive Material"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Upload & Distribute Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-200">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                  <Upload className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Upload & Distribute Material</h3>
                  <p className="text-xs text-slate-500">Curriculum-linked learning resource for your assigned sections</p>
                </div>
              </div>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {uploadError && (
              <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {uploadError}
              </div>
            )}

            <form onSubmit={handleCreateMaterial} className="mt-4 space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Title <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Chapter 4: Electric Potential and Capacitance Handout"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Class <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={selectedClassId}
                    onChange={(e) => {
                      setSelectedClassId(e.target.value);
                      setSelectedSectionIds([]);
                    }}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {distinctClasses.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Subject <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={selectedSubjectId}
                    onChange={(e) => setSelectedSubjectId(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {distinctSubjects.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Target Assigned Sections */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Distribute to Assigned Sections <span className="text-rose-500">*</span>
                </label>
                {availableSections.length === 0 ? (
                  <p className="text-xs text-amber-600 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                    You have no active teaching assignments for this class/subject combination.
                  </p>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {availableSections.map((sec) => (
                      <label
                        key={sec.id}
                        className={`flex items-center p-2.5 rounded-lg border cursor-pointer text-xs transition ${
                          selectedSectionIds.includes(sec.id)
                            ? 'bg-indigo-50 border-indigo-300 text-indigo-900 font-medium'
                            : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedSectionIds.includes(sec.id)}
                          onChange={() => handleSectionToggle(sec.id)}
                          className="mr-2 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        Section {sec.name}
                      </label>
                    ))}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Chapter Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Electric Charges and Fields"
                    value={uploadChapter}
                    onChange={(e) => setUploadChapter(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Topic / Key Concept
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Gauss Law and its Applications"
                    value={uploadTopic}
                    onChange={(e) => setUploadTopic(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  File URL or Storage Link <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="https://storage.mind.local/uploads/electrostatics_ch1.pdf"
                  value={uploadFileUrl}
                  onChange={(e) => setUploadFileUrl(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Notes / Excerpt Content (For AI Question Extraction)
                </label>
                <textarea
                  rows={4}
                  placeholder="Paste key definitions, theorems, or text excerpt from the PDF to power the AI Question Extractor..."
                  value={uploadContentText}
                  onChange={(e) => setUploadContentText(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 font-medium text-xs hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-white font-medium text-xs hover:bg-indigo-700 transition disabled:opacity-50"
                >
                  {isSubmitting ? 'Distributing...' : 'Publish to Sections'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Question Extractor Side-by-Side Review Modal */}
      {selectedMaterialForExtraction && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-5xl w-full p-6 max-h-[92vh] flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-slate-200 flex-shrink-0">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                  <Sparkles className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">
                    Question Extractor Agent: {selectedMaterialForExtraction.title}
                  </h3>
                  <p className="text-xs text-slate-500">
                    Side-by-side pedagogical review. Every candidate question requires teacher approval.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedMaterialForExtraction(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {extractorError && (
              <div className="my-3 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {extractorError}
              </div>
            )}

            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6 overflow-hidden pt-4">
              {/* Left Column: Source Document / Excerpt */}
              <div className="flex flex-col bg-slate-50 p-4 rounded-xl border border-slate-200 overflow-y-auto">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center">
                    <BookOpen className="w-3.5 h-3.5 mr-1.5 text-slate-500" />
                    Source Material Excerpt
                  </span>
                  <span className="text-[11px] text-slate-500">
                    {selectedMaterialForExtraction.subject_name} • {selectedMaterialForExtraction.class_name}
                  </span>
                </div>
                <div className="prose prose-xs max-w-none text-slate-700 whitespace-pre-wrap leading-relaxed flex-1 bg-white p-3.5 rounded-lg border border-slate-200/80 font-mono text-xs">
                  {selectedMaterialForExtraction.chapter && (
                    <div className="font-bold text-indigo-900 mb-2 font-sans">
                      CHAPTER: {selectedMaterialForExtraction.chapter.toUpperCase()}
                    </div>
                  )}
                  {selectedMaterialForExtraction.description && (
                    <p className="text-slate-600 italic mb-3 font-sans">
                      Summary: {selectedMaterialForExtraction.description}
                    </p>
                  )}
                  {/* Default text if no raw text */}
                  {selectedMaterialForExtraction.title}: Academic core principles and curriculum concepts.
                  Standard syllabus alignment for {selectedMaterialForExtraction.subject_name} in{' '}
                  {selectedMaterialForExtraction.class_name}.
                </div>
              </div>

              {/* Right Column: Extracted Candidate Questions with Human Review */}
              <div className="flex flex-col overflow-y-auto space-y-4 pr-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center">
                    <Sparkles className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
                    Candidate Questions ({extractedQuestions.length})
                  </span>
                  <span className="text-[11px] font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                    Status: Needs Review
                  </span>
                </div>

                {isExtracting ? (
                  <div className="p-12 text-center text-slate-500">
                    <div className="animate-spin w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full mx-auto mb-2" />
                    <p className="text-xs font-medium">Extracting canonical questions from material chunks...</p>
                  </div>
                ) : extractedQuestions.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 text-xs">
                    No questions could be extracted. Please ensure material contains substantive text.
                  </div>
                ) : (
                  extractedQuestions.map((q, idx) => {
                    const isApproved = approvedQuestionIds.has(q.id);
                    return (
                      <div
                        key={q.id}
                        className={`p-4 rounded-xl border transition ${
                          isApproved
                            ? 'bg-emerald-50/60 border-emerald-300'
                            : 'bg-white border-slate-200 shadow-sm'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-800 uppercase">
                              Q#{idx + 1} • {q.type.replace('_', ' ')}
                            </span>
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-600 uppercase">
                              {q.bloom_taxonomy}
                            </span>
                          </div>
                          <span className="text-xs font-bold text-slate-700">{q.marks} Mark(s)</span>
                        </div>

                        <p className="text-sm font-semibold text-slate-900 mb-2">{q.prompt}</p>

                        {q.options && q.options.length > 0 && (
                          <div className="space-y-1 my-2 pl-2 border-l-2 border-slate-200 text-xs">
                            {q.options.map((opt) => (
                              <div
                                key={opt.id}
                                className={`py-0.5 ${
                                  q.answer_keys?.includes(opt.id)
                                    ? 'font-bold text-emerald-700'
                                    : 'text-slate-600'
                                }`}
                              >
                                <span className="font-mono mr-1">({opt.id})</span> {opt.text}
                              </div>
                            ))}
                          </div>
                        )}

                        <div className="mt-2.5 p-2.5 rounded bg-slate-50 border border-slate-200 text-xs space-y-1">
                          <div>
                            <span className="font-semibold text-slate-700">Model Answer: </span>
                            <span className="text-slate-600">{q.expected_answer}</span>
                          </div>
                          <div>
                            <span className="font-semibold text-slate-700">Marking Rubric: </span>
                            <span className="text-slate-600">{q.marking_scheme}</span>
                          </div>
                        </div>

                        <div className="mt-3 flex items-center justify-between pt-2 border-t border-slate-100">
                          <span className="text-[11px] text-slate-400">
                            Excerpt: "{q.source_excerpt.substring(0, 45)}..."
                          </span>
                          {isApproved ? (
                            <span className="inline-flex items-center text-xs font-bold text-emerald-700 bg-emerald-100/70 px-2.5 py-1 rounded-md">
                              <Check className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                              Approved into Bank
                            </span>
                          ) : (
                            <button
                              onClick={() => handleApproveQuestion(q)}
                              className="inline-flex items-center px-3 py-1.5 rounded-lg bg-emerald-600 text-white font-medium text-xs hover:bg-emerald-700 transition shadow-sm"
                            >
                              <Check className="w-3.5 h-3.5 mr-1" />
                              Approve Question
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-200 flex items-center justify-between flex-shrink-0">
              <span className="text-xs text-slate-500">
                Approved <strong className="text-slate-800">{approvedQuestionIds.size}</strong> of{' '}
                {extractedQuestions.length} candidate questions
              </span>
              <button
                onClick={() => setSelectedMaterialForExtraction(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 text-white font-medium text-xs hover:bg-slate-900 transition"
              >
                Done Reviewing
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
