import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import {
  UserCheck,
  Plus,
  Lock,
  CheckCircle,
  AlertCircle,
  Printer,
  X,
  ArrowLeft,
  KeyRound,
  ShieldAlert,
} from 'lucide-react';

interface StudentItem {
  id: string;
  student_id: string;
  student_name: string;
  roll_number: string;
  status: string;
  created_at: string;
}

interface RosterData {
  section_id: string;
  section_name: string;
  class_id: string;
  class_name: string;
  roster_status: 'pending' | 'verified' | 'locked';
  class_teacher_id: string | null;
  class_teacher_name: string | null;
  students: StudentItem[];
  total_students: number;
}

interface CredentialSlip {
  student_id: string;
  full_name: string;
  roll_number: string;
  login_email: string;
  initial_password: string;
  class_name: string;
  section_name: string;
  school_name: string;
  must_change_password: boolean;
}

export const SectionRoster: React.FC = () => {
  const { sectionId } = useParams<{ sectionId: string }>();
  const [roster, setRoster] = useState<RosterData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Add Student Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [fullName, setFullName] = useState<string>('');
  const [rollNumber, setRollNumber] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [addLoading, setAddLoading] = useState<boolean>(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [newSlip, setNewSlip] = useState<CredentialSlip | null>(null);

  // Credential Slips Modal State
  const [isSlipsModalOpen, setIsSlipsModalOpen] = useState<boolean>(false);
  const [slips, setSlips] = useState<CredentialSlip[]>([]);
  const [slipsLoading, setSlipsLoading] = useState<boolean>(false);

  // Roster Change Request Modal State
  const [isChangeModalOpen, setIsChangeModalOpen] = useState<boolean>(false);
  const [changeType, setChangeType] = useState<string>('add_student');
  const [changeFullName, setChangeFullName] = useState<string>('');
  const [changeRoll, setChangeRoll] = useState<string>('');
  const [changeReason, setChangeReason] = useState<string>('');
  const [changeSubmitting, setChangeSubmitting] = useState<boolean>(false);

  const fetchRoster = async () => {
    if (!sectionId) return;
    try {
      const data = await apiRequest<RosterData>(`/rosters/${sectionId}`);
      setRoster(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load section roster');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoster();
  }, [sectionId]);

  const handleAddStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sectionId) return;
    setAddError(null);
    setAddLoading(true);

    try {
      const slip = await apiRequest<CredentialSlip>(`/rosters/${sectionId}/students`, {
        method: 'POST',
        body: JSON.stringify({
          full_name: fullName.trim(),
          roll_number: rollNumber.trim(),
          email: email.trim() || undefined,
        }),
      });

      setNewSlip(slip);
      setSuccessMsg(`Student '${slip.full_name}' added successfully.`);
      setFullName('');
      setRollNumber('');
      setEmail('');
      await fetchRoster();
    } catch (err: any) {
      setAddError(err.message || 'Failed to add student to roster');
    } finally {
      setAddLoading(false);
    }
  };

  const handleUpdateStatus = async (newStatus: 'pending' | 'verified' | 'locked') => {
    if (!sectionId) return;
    try {
      await apiRequest(`/rosters/${sectionId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      });
      setSuccessMsg(`Roster status updated to ${newStatus.toUpperCase()}.`);
      await fetchRoster();
    } catch (err: any) {
      setError(err.message || 'Failed to update roster status');
    }
  };

  const handleFetchSlips = async () => {
    if (!sectionId) return;
    setSlipsLoading(true);
    setIsSlipsModalOpen(true);
    try {
      const data = await apiRequest<CredentialSlip[]>(`/rosters/${sectionId}/credentials`);
      setSlips(data);
    } catch (err: any) {
      setError(err.message || 'Failed to generate credential slips');
    } finally {
      setSlipsLoading(false);
    }
  };

  const handleSubmitChangeRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sectionId) return;
    setChangeSubmitting(true);
    try {
      await apiRequest(`/rosters/${sectionId}/change-requests`, {
        method: 'POST',
        body: JSON.stringify({
          change_type: changeType,
          student_data: { full_name: changeFullName, roll_number: changeRoll },
          reason: changeReason,
        }),
      });
      setSuccessMsg('Roster change request submitted to Academic Coordinator.');
      setIsChangeModalOpen(false);
      setChangeFullName('');
      setChangeRoll('');
      setChangeReason('');
    } catch (err: any) {
      setError(err.message || 'Failed to submit change request');
    } finally {
      setChangeSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !roster) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-rose-800">
        <p className="font-semibold">Unable to access Section Roster</p>
        <p className="text-sm mt-1">{error || 'Section not found.'}</p>
        <Link to="/teacher/classes" className="inline-flex items-center text-xs font-semibold text-rose-900 mt-3 underline">
          <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to My Classes
        </Link>
      </div>
    );
  }

  const isLocked = roster.roster_status === 'locked';

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Link to="/teacher/classes" className="inline-flex items-center text-xs font-medium text-slate-500 hover:text-slate-800 mb-2">
          <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to My Classes
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-slate-900">
                {roster.class_name} — Section {roster.section_name} Roster
              </h1>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${
                  roster.roster_status === 'locked'
                    ? 'bg-rose-100 text-rose-800 border border-rose-200'
                    : roster.roster_status === 'verified'
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    : 'bg-amber-100 text-amber-800 border border-amber-200'
                }`}
              >
                {roster.roster_status}
              </span>
            </div>
            <p className="text-sm text-slate-500 mt-1 flex items-center">
              <UserCheck className="w-4 h-4 mr-1 text-indigo-600" />
              Class Teacher: <span className="font-medium text-slate-800 ml-1">{roster.class_teacher_name || 'Designated Class Teacher'}</span>
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={handleFetchSlips}
              className="inline-flex items-center px-3.5 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-sm transition-colors"
            >
              <Printer className="w-4 h-4 mr-1.5 text-indigo-600" />
              Credential Slips
            </button>

            {!isLocked ? (
              <>
                <button
                  type="button"
                  onClick={() => {
                    setAddError(null);
                    setNewSlip(null);
                    setIsAddModalOpen(true);
                  }}
                  className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-sm transition-colors"
                >
                  <Plus className="w-4 h-4 mr-1.5" />
                  Add Student
                </button>

                {roster.roster_status === 'pending' && (
                  <button
                    type="button"
                    onClick={() => handleUpdateStatus('verified')}
                    className="inline-flex items-center px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-colors"
                  >
                    <CheckCircle className="w-4 h-4 mr-1.5" />
                    Verify Roster
                  </button>
                )}

                {roster.roster_status === 'verified' && (
                  <button
                    type="button"
                    onClick={() => handleUpdateStatus('locked')}
                    className="inline-flex items-center px-3.5 py-2 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-sm transition-colors"
                  >
                    <Lock className="w-4 h-4 mr-1.5" />
                    Lock Roster
                  </button>
                )}
              </>
            ) : (
              <button
                type="button"
                onClick={() => setIsChangeModalOpen(true)}
                className="inline-flex items-center px-3.5 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shadow-sm transition-colors"
              >
                <ShieldAlert className="w-4 h-4 mr-1.5" />
                Request Roster Change
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between">
          <div className="flex items-center">
            <CheckCircle className="w-4 h-4 mr-2 text-emerald-600 flex-shrink-0" />
            {successMsg}
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-600 hover:text-emerald-800">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {isLocked && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center">
          <Lock className="w-4 h-4 mr-2 text-rose-600 flex-shrink-0" />
          <span>
            This roster is <strong>Locked</strong> for upcoming board examinations. Direct student additions or roll number changes are disabled. Use <em>Request Roster Change</em> to submit adjustments to the Academic Coordinator.
          </span>
        </div>
      )}

      {/* Students Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <span className="font-semibold text-sm text-slate-900">
            Enrolled Students ({roster.total_students})
          </span>
          <span className="text-xs text-slate-400">Roll number uniqueness enforced</span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-slate-500 font-medium">
              <tr>
                <th className="px-6 py-3 text-left">Roll Number</th>
                <th className="px-6 py-3 text-left">Student Name</th>
                <th className="px-6 py-3 text-left">Status</th>
                <th className="px-6 py-3 text-right">Enrollment Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {roster.students.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-slate-400 text-sm">
                    No students currently enrolled in this section. Click &ldquo;Add Student&rdquo; above.
                  </td>
                </tr>
              ) : (
                roster.students.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-3.5 font-mono font-bold text-indigo-700">{s.roll_number}</td>
                    <td className="px-6 py-3.5 font-medium text-slate-900">{s.student_name}</td>
                    <td className="px-6 py-3.5">
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {s.status}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-right text-xs text-slate-400">
                      {new Date(s.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Student Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900 flex items-center">
                <Plus className="w-4 h-4 mr-2 text-indigo-600" />
                Add Student to {roster.class_name} Section {roster.section_name}
              </h2>
              <button onClick={() => setIsAddModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {newSlip ? (
              <div className="p-6 space-y-4">
                <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs">
                  <p className="font-bold text-sm text-emerald-800 mb-1">Student Added & Credentials Generated!</p>
                  <p>Hand this initial slip to the student. They will be prompted to choose a new private password on first login.</p>
                </div>
                <div className="border border-slate-200 rounded-xl p-4 bg-slate-50 space-y-2 text-xs">
                  <div className="flex justify-between"><span className="text-slate-500">Name:</span><span className="font-semibold text-slate-900">{newSlip.full_name}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Roll Number:</span><span className="font-mono font-bold text-indigo-700">{newSlip.roll_number}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Login Email:</span><span className="font-mono text-slate-900">{newSlip.login_email}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Initial Password:</span><span className="font-mono font-bold text-emerald-700">{newSlip.initial_password}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">First Login Flag:</span><span className="text-amber-700 font-semibold">Forced Password Reset</span></div>
                </div>
                <div className="flex justify-end pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setNewSlip(null);
                      setIsAddModalOpen(false);
                    }}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-semibold hover:bg-indigo-700"
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleAddStudent} className="p-6 space-y-4">
                {addError && (
                  <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-start">
                    <AlertCircle className="w-4 h-4 mr-1.5 flex-shrink-0 mt-0.5" />
                    <span>{addError}</span>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Student Full Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Aarav Gupta"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Section Roll Number
                  </label>
                  <input
                    type="text"
                    required
                    placeholder={`e.g. ${roster.section_name}-15`}
                    value={rollNumber}
                    onChange={(e) => setRollNumber(e.target.value)}
                    className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-600"
                  />
                  <span className="text-[11px] text-slate-400 mt-0.5 block">Must be unique within Section {roster.section_name}.</span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Custom Email (Optional)
                  </label>
                  <input
                    type="email"
                    placeholder="Auto-generated if left blank"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-600"
                  />
                </div>

                <div className="pt-3 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setIsAddModalOpen(false)}
                    className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={addLoading}
                    className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg disabled:opacity-50"
                  >
                    {addLoading ? 'Enrolling...' : 'Enroll Student'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Credential Slips Printable Modal */}
      {isSlipsModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] shadow-xl border border-slate-200 flex flex-col overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-slate-900 flex items-center">
                  <KeyRound className="w-4 h-4 mr-2 text-indigo-600" />
                  Printable Credential Slips
                </h2>
                <p className="text-xs text-slate-500">Distribution slips for {roster.class_name} Section {roster.section_name}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700"
                >
                  Print
                </button>
                <button onClick={() => setIsSlipsModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 flex-1">
              {slipsLoading ? (
                <div className="text-center py-8 text-sm text-slate-500">Generating credential slips...</div>
              ) : slips.length === 0 ? (
                <div className="text-center py-8 text-sm text-slate-400">No students found.</div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {slips.map((s) => (
                    <div key={s.student_id} className="border-2 border-dashed border-slate-300 rounded-xl p-4 bg-slate-50/70 text-xs space-y-1.5">
                      <div className="font-bold text-slate-900 text-sm border-b pb-1 border-slate-200 flex justify-between">
                        <span>{s.full_name}</span>
                        <span className="font-mono text-indigo-700">Roll: {s.roll_number}</span>
                      </div>
                      <div className="text-slate-500 text-[11px]">{s.school_name} — {s.class_name} ({s.section_name})</div>
                      <div className="pt-1">
                        <span className="text-slate-400 block text-[10px] uppercase">Login ID</span>
                        <span className="font-mono font-medium text-slate-900">{s.login_email}</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase">Initial Password</span>
                        <span className="font-mono font-bold text-emerald-700">{s.initial_password}</span>
                      </div>
                      <div className="text-[10px] text-amber-700 italic pt-1">
                        * You will be prompted to set a new password on your first login.
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Roster Change Request Modal */}
      {isChangeModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900 flex items-center">
                <ShieldAlert className="w-4 h-4 mr-2 text-amber-600" />
                Submit Roster Change Request
              </h2>
              <button onClick={() => setIsChangeModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmitChangeRequest} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Change Type
                </label>
                <select
                  value={changeType}
                  onChange={(e) => setChangeType(e.target.value)}
                  className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white"
                >
                  <option value="add_student">Add New Student</option>
                  <option value="remove_student">Remove Student</option>
                  <option value="update_roll">Update Roll Number</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Student Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="Student name"
                  value={changeFullName}
                  onChange={(e) => setChangeFullName(e.target.value)}
                  className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Roll Number
                </label>
                <input
                  type="text"
                  required
                  placeholder="Roll number"
                  value={changeRoll}
                  onChange={(e) => setChangeRoll(e.target.value)}
                  className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Administrative Justification
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Reason for post-lock change (e.g., Transfer certificate approved by Principal)..."
                  value={changeReason}
                  onChange={(e) => setChangeReason(e.target.value)}
                  className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2"
                />
              </div>

              <div className="pt-3 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsChangeModalOpen(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={changeSubmitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 rounded-lg disabled:opacity-50"
                >
                  {changeSubmitting ? 'Submitting...' : 'Submit to Coordinator'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
