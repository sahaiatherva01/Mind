import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import {
  Sparkles,
  AlertCircle,
  ArrowRight,
  Check,
} from 'lucide-react';

const QUESTION_TYPES = [
  // Objective (6)
  { id: 'mcq', label: 'MCQ (Single Choice)', category: 'Objective' },
  { id: 'multiple_select', label: 'Multiple Select', category: 'Objective' },
  { id: 'fill_in_the_blanks', label: 'Fill in the Blanks', category: 'Objective' },
  { id: 'true_false', label: 'True / False', category: 'Objective' },
  { id: 'match_the_following', label: 'Match the Following', category: 'Objective' },
  { id: 'assertion_reason', label: 'Assertion–Reason', category: 'Objective' },

  // Written (8)
  { id: 'very_short_answer', label: 'Very Short Answer', category: 'Written' },
  { id: 'short_answer', label: 'Short Answer', category: 'Written' },
  { id: 'medium_answer', label: 'Medium Answer', category: 'Written' },
  { id: 'long_answer', label: 'Long Answer', category: 'Written' },
  { id: 'definition_based', label: 'Definition-Based', category: 'Written' },
  { id: 'difference_based', label: 'Difference-Based', category: 'Written' },
  { id: 'reasoning_based', label: 'Reasoning-Based', category: 'Written' },
  { id: 'proof_derivation_based', label: 'Proof / Derivation', category: 'Written' },

  // Visual & Mathematical (9)
  { id: 'diagram_based', label: 'Diagram-Based', category: 'Visual & Math' },
  { id: 'label_the_diagram', label: 'Label Diagram', category: 'Visual & Math' },
  { id: 'graph_based', label: 'Graph-Based', category: 'Visual & Math' },
  { id: 'table_based', label: 'Table-Based', category: 'Visual & Math' },
  { id: 'chart_based', label: 'Chart-Based', category: 'Visual & Math' },
  { id: 'map_based', label: 'Map-Based', category: 'Visual & Math' },
  { id: 'construction_based', label: 'Construction', category: 'Visual & Math' },
  { id: 'numerical_based', label: 'Numerical-Based', category: 'Visual & Math' },
  { id: 'formula_based', label: 'Formula-Based', category: 'Visual & Math' },

  // Application & Analytical (9)
  { id: 'case_based', label: 'Case-Based', category: 'Application & Analytical' },
  { id: 'passage_based', label: 'Passage-Based', category: 'Application & Analytical' },
  { id: 'source_based', label: 'Source-Based', category: 'Application & Analytical' },
  { id: 'data_interpretation', label: 'Data Interpretation', category: 'Application & Analytical' },
  { id: 'application_based', label: 'Application-Based', category: 'Application & Analytical' },
  { id: 'hots', label: 'HOTS (High Order Thinking)', category: 'Application & Analytical' },
  { id: 'critical_thinking', label: 'Critical Thinking', category: 'Application & Analytical' },
  { id: 'problem_solving', label: 'Problem Solving', category: 'Application & Analytical' },
  { id: 'experiment_based', label: 'Experiment-Based', category: 'Application & Analytical' },

  // Computer Science (8)
  { id: 'output_prediction', label: 'Output Prediction (Java)', category: 'Computer Science' },
  { id: 'theory_coding', label: 'Theory + Coding', category: 'Computer Science' },
  { id: 'code_completion', label: 'Code Completion', category: 'Computer Science' },
  { id: 'error_detection', label: 'Error Detection', category: 'Computer Science' },
  { id: 'debugging', label: 'Debugging', category: 'Computer Science' },
  { id: 'dry_run', label: 'Dry Run', category: 'Computer Science' },
  { id: 'algorithm_writing', label: 'Algorithm Writing', category: 'Computer Science' },
  { id: 'program_writing', label: 'Program Writing', category: 'Computer Science' },
];

export const AIStudio: React.FC = () => {
  const navigate = useNavigate();
  const [assignments, setAssignments] = useState<any[]>([]);
  const [curriculum, setCurriculum] = useState<any[]>([]);

  // Form states
  const [outputType, setOutputType] = useState<'worksheet' | 'quiz' | 'question_paper' | 'custom'>('quiz');
  const [selectedAssignmentId, setSelectedAssignmentId] = useState('');
  const [chapter, setChapter] = useState('');
  const [topics, setTopics] = useState('');
  const [questionCount, setQuestionCount] = useState(5);
  const [totalMarks, setTotalMarks] = useState(10);
  const [easyPct, setEasyPct] = useState(30);
  const [medPct, setMedPct] = useState(50);
  const [hardPct, setHardPct] = useState(20);
  const [selectedTypes, setSelectedTypes] = useState<string[]>(['mcq', 'short_answer']);
  const [instructions, setInstructions] = useState('');

  const [isGenerating, setIsGenerating] = useState(false);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [aRes, cRes] = await Promise.all([
          apiRequest<any[]>('/teacher-assignments'),
          apiRequest<any[]>('/curriculum'),
        ]);
        setAssignments(aRes);
        setCurriculum(cRes);
        if (aRes.length > 0) {
          setSelectedAssignmentId(aRes[0].id);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load workspaces');
      }
    }
    load();
  }, []);

  const selectedAssignment = assignments.find((a) => a.id === selectedAssignmentId);

  // Filter curriculum for selected subject
  const availableChapters = Array.from(
    new Set(
      curriculum
        .filter((c) => selectedAssignment && c.subject_id === selectedAssignment.subject_id)
        .map((c) => c.chapter)
    )
  );

  const toggleType = (id: string) => {
    if (selectedTypes.includes(id)) {
      if (selectedTypes.length > 1) {
        setSelectedTypes(selectedTypes.filter((t) => t !== id));
      }
    } else {
      setSelectedTypes([...selectedTypes, id]);
    }
  };

  const selectAllCategory = (cat: string) => {
    const ids = QUESTION_TYPES.filter((q) => q.category === cat).map((q) => q.id);
    const newSelected = Array.from(new Set([...selectedTypes, ...ids]));
    setSelectedTypes(newSelected);
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAssignment) return;

    setError(null);
    setIsGenerating(true);

    const topicList = topics
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);

    const payload = {
      class_id: selectedAssignment.class_id,
      section_id: selectedAssignment.section_id,
      subject_id: selectedAssignment.subject_id,
      chapter: chapter || 'Board Curriculum Unit',
      topics: topicList.length > 0 ? topicList : [chapter || 'General Module'],
      difficulty: { easy: easyPct, medium: medPct, hard: hardPct },
      question_count: Number(questionCount),
      total_marks: Number(totalMarks),
      question_types: selectedTypes,
      instructions: instructions || undefined,
      board: 'ICSE/ISC',
      language: 'en',
    };

    try {
      let endpoint = '/generation/quizzes';
      if (outputType === 'worksheet') endpoint = '/generation/worksheets';
      else if (outputType === 'question_paper') endpoint = '/generation/question-papers';
      else if (outputType === 'custom') endpoint = '/generation/questions';

      const jobRes = await apiRequest<{ job_id: string }>(endpoint, {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setActiveJobId(jobRes.job_id);
      setJobStatus('queued');

      // Poll job for completion
      const pollInterval = setInterval(async () => {
        try {
          const job = await apiRequest<any>(`/generation/jobs/${jobRes.job_id}`);
          setJobStatus(job.status);
          if (job.status === 'succeeded' && job.assessment_id) {
            clearInterval(pollInterval);
            setIsGenerating(false);
            setActiveJobId(null);
            navigate(`/teacher/assessments/${job.assessment_id}`);
          } else if (job.status === 'failed') {
            clearInterval(pollInterval);
            setIsGenerating(false);
            setActiveJobId(null);
            setError(job.error_message || 'Generation failed');
          } else if (job.status === 'cancelled') {
            clearInterval(pollInterval);
            setIsGenerating(false);
            setActiveJobId(null);
            setError('Generation job was cancelled.');
          }
        } catch {
          clearInterval(pollInterval);
          setIsGenerating(false);
          setActiveJobId(null);
        }
      }, 1000);
    } catch (err: any) {
      setError(err.message || 'Generation request failed');
      setIsGenerating(false);
      setActiveJobId(null);
    }
  };

  const handleCancelGeneration = async () => {
    if (!activeJobId) return;
    try {
      await apiRequest(`/generation/jobs/${activeJobId}/cancel`, { method: 'POST' });
      setJobStatus('cancelled');
      setIsGenerating(false);
      setActiveJobId(null);
    } catch (err: any) {
      console.error('Failed to cancel job', err);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 flex items-center">
          <Sparkles className="w-6 h-6 mr-2 text-indigo-600" />
          AI Content Studio
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Create curriculum-aligned assessments with authentic ICSE/ISC Board Exam formats.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-800 flex items-center">
          <AlertCircle className="w-4 h-4 mr-2 text-red-500 flex-shrink-0" />
          {error}
        </div>
      )}

      <form onSubmit={handleGenerate} className="space-y-6">
        {/* Step 1: Output Type Selection */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Step 1: Select Assessment Format
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { id: 'quiz', label: 'Speed Quiz', desc: 'Objective checks & MCQs' },
              { id: 'worksheet', label: 'Practice Worksheet', desc: 'Short answers & numerics' },
              { id: 'question_paper', label: 'Board Exam Paper', desc: 'Section A & B structured' },
              { id: 'custom', label: 'Custom Question Set', desc: 'Custom mix of types' },
            ].map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setOutputType(t.id as any)}
                className={`p-4 rounded-xl text-left border transition-all ${
                  outputType === t.id
                    ? 'border-indigo-600 bg-indigo-50/50 ring-2 ring-indigo-500/20'
                    : 'border-slate-200 hover:border-slate-300 bg-white'
                }`}
              >
                <div className="font-bold text-sm text-slate-900">{t.label}</div>
                <div className="text-xs text-slate-500 mt-1">{t.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Step 2: Target Assigned Class & Subject */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Step 2: Select Teaching Workspace (Assigned Only)
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase">Assigned Class & Subject</label>
              <select
                required
                value={selectedAssignmentId}
                onChange={(e) => setSelectedAssignmentId(e.target.value)}
                className="mt-1.5 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
              >
                {assignments.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.class_name} — Section {a.section_name} ({a.subject_name})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase">Curriculum Chapter</label>
              <input
                type="text"
                required
                placeholder="e.g. Quadratic Equations or Calculus"
                value={chapter}
                onChange={(e) => setChapter(e.target.value)}
                className="mt-1.5 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
              />
              {availableChapters.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  <span className="text-[11px] text-slate-400 mr-1 self-center">Suggestions:</span>
                  {availableChapters.map((ch: any) => (
                    <button
                      key={ch}
                      type="button"
                      onClick={() => setChapter(ch)}
                      className="px-2 py-0.5 rounded bg-slate-100 hover:bg-indigo-50 text-[11px] text-slate-700 transition-colors"
                    >
                      {ch}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase">
              Specific Topics / Learning Outcomes (comma separated)
            </label>
            <input
              type="text"
              placeholder="e.g. Nature of Roots, Discriminant, Complex Conjugates"
              value={topics}
              onChange={(e) => setTopics(e.target.value)}
              className="mt-1.5 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase">
              Optional Teacher Instructions / Emphasis
            </label>
            <input
              type="text"
              placeholder="e.g. Include authentic ICSE 2024 specimen question styling"
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              className="mt-1.5 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
            />
          </div>
        </div>

        {/* Step 3: Marks & Difficulty */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Step 3: Assessment Weighting & Difficulty
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase">Question Count</label>
              <input
                type="number"
                min="1"
                max="50"
                value={questionCount}
                onChange={(e) => setQuestionCount(Number(e.target.value))}
                className="mt-1.5 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase">Total Marks</label>
              <input
                type="number"
                min="1"
                max="100"
                value={totalMarks}
                onChange={(e) => setTotalMarks(Number(e.target.value))}
                className="mt-1.5 w-full px-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-600"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase">Easy / Med / Hard (%)</label>
              <div className="mt-1.5 flex space-x-1.5">
                <input
                  type="number"
                  title="Easy %"
                  value={easyPct}
                  onChange={(e) => setEasyPct(Number(e.target.value))}
                  className="w-1/3 px-2 py-2 text-xs border border-slate-300 rounded text-center outline-none"
                />
                <input
                  type="number"
                  title="Medium %"
                  value={medPct}
                  onChange={(e) => setMedPct(Number(e.target.value))}
                  className="w-1/3 px-2 py-2 text-xs border border-slate-300 rounded text-center outline-none"
                />
                <input
                  type="number"
                  title="Hard %"
                  value={hardPct}
                  onChange={(e) => setHardPct(Number(e.target.value))}
                  className="w-1/3 px-2 py-2 text-xs border border-slate-300 rounded text-center outline-none"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase">Board Syllabus</label>
              <input
                type="text"
                disabled
                value="ICSE / ISC 2026-27"
                className="mt-1.5 w-full px-3 py-2 text-sm bg-slate-100 border border-slate-200 rounded-lg text-slate-600"
              />
            </div>
          </div>
        </div>

        {/* Step 4: 40 Question Types Master Selector */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Step 4: Question Types Checklist (40 ICSE/ISC Types)
              </label>
              <p className="text-xs text-slate-500 mt-0.5">
                {selectedTypes.length} question formats selected
              </p>
            </div>
            <div className="flex space-x-2">
              {['Objective', 'Written', 'Visual & Math', 'Application & Analytical', 'Computer Science'].map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => selectAllCategory(cat)}
                  className="px-2 py-1 rounded border border-slate-200 text-[11px] font-semibold text-slate-600 hover:bg-slate-50"
                >
                  + {cat}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-h-64 overflow-y-auto p-1 border border-slate-100 rounded-lg">
            {QUESTION_TYPES.map((qt) => {
              const active = selectedTypes.includes(qt.id);
              return (
                <button
                  key={qt.id}
                  type="button"
                  onClick={() => toggleType(qt.id)}
                  className={`p-2 rounded-lg text-left text-xs border transition-colors flex items-center justify-between ${
                    active
                      ? 'border-indigo-600 bg-indigo-50/70 text-indigo-900 font-semibold'
                      : 'border-slate-200 hover:border-slate-300 text-slate-600 bg-white'
                  }`}
                >
                  <span className="truncate">{qt.label}</span>
                  {active && <Check className="w-3.5 h-3.5 text-indigo-600 flex-shrink-0 ml-1" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Action Button & Active Generation Banner */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          {isGenerating ? (
            <div className="flex items-center gap-3 bg-indigo-50 border border-indigo-200 text-indigo-900 px-4 py-2.5 rounded-xl text-xs font-medium w-full sm:w-auto">
              <Sparkles className="w-4 h-4 text-indigo-600 animate-spin flex-shrink-0" />
              <div>
                <span>Status: </span>
                <span className="font-bold uppercase tracking-wider text-indigo-700">
                  {jobStatus === 'queued' ? 'Queued in Background Queue...' : 'Running: AI Orchestrator...'}
                </span>
                <span className="block text-[11px] text-slate-500 mt-0.5">
                  You can safely leave this tab; your draft will persist automatically.
                </span>
              </div>
              <button
                type="button"
                onClick={handleCancelGeneration}
                className="ml-auto px-3 py-1 bg-white border border-rose-200 hover:bg-rose-50 text-rose-700 font-semibold rounded-lg text-xs"
              >
                Cancel
              </button>
            </div>
          ) : (
            <div className="text-xs text-slate-500">
              * Generated assessments require explicit teacher review & approval before publishing.
            </div>
          )}

          <button
            type="submit"
            disabled={isGenerating}
            className="w-full sm:w-auto px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl shadow-md transition-all flex items-center justify-center disabled:opacity-50"
          >
            {isGenerating ? (
              <>
                <Sparkles className="w-4 h-4 mr-2 animate-spin" />
                Working in Background...
              </>
            ) : (
              <>
                Generate Assessment Draft
                <ArrowRight className="w-4 h-4 ml-2" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
