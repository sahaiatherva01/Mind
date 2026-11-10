import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth, UserRole } from './context/AuthContext';
import { LoginPage } from './pages/auth/LoginPage';
import { DashboardLayout } from './layouts/DashboardLayout';

// Admin Pages
import { AdminDashboard } from './pages/admin/AdminDashboard';
import { AcademicSetup } from './pages/admin/AcademicSetup';
import { BulkImport } from './pages/admin/BulkImport';
import { AuditLogs } from './pages/admin/AuditLogs';

// Coordinator Pages
import { CoordinatorDashboard } from './pages/coordinator/CoordinatorDashboard';
import { AssignmentMatrix } from './pages/coordinator/AssignmentMatrix';

// Teacher Pages
import { TeacherDashboard } from './pages/teacher/TeacherDashboard';
import { TeacherClasses } from './pages/teacher/TeacherClasses';
import { AIStudio } from './pages/teacher/AIStudio';
import { AssessmentEditor } from './pages/teacher/AssessmentEditor';
import { TeacherAssessments } from './pages/teacher/TeacherAssessments';
import { TeacherEvaluationQueue } from './pages/teacher/TeacherEvaluationQueue';
import { TeacherAnalytics } from './pages/teacher/TeacherAnalytics';

// Student Pages
import { StudentDashboard } from './pages/student/StudentDashboard';
import { StudentUpcomingTests } from './pages/student/StudentUpcomingTests';
import { AssessmentPlayer } from './pages/student/AssessmentPlayer';
import { StudentResults } from './pages/student/StudentResults';

const ProtectedRoute: React.FC<{ children: React.ReactNode; allowedRoles?: string[] }> = ({
  children,
  allowedRoles,
}) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-slate-50 text-slate-500 font-sans text-sm">
        <div className="animate-pulse">Loading Mind workspace...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Redirect to appropriate home based on role
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

const RootRedirect: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) return null;
  if (!user) return <Navigate to="/login" replace />;

  if (user.role === 'academic_coordinator') return <Navigate to="/coordinator/dashboard" replace />;
  if (user.role === 'admin' || user.role === 'school_admin' || user.role === 'platform_admin') {
    return <Navigate to="/admin/dashboard" replace />;
  }
  if (user.role === 'teacher') return <Navigate to="/teacher/dashboard" replace />;
  if (user.role === 'student') return <Navigate to="/student/dashboard" replace />;

  return <Navigate to="/login" replace />;
};

export const App: React.FC = () => {
  const adminRoles: UserRole[] = ['admin', 'school_admin', 'academic_coordinator', 'platform_admin'];
  const coordinatorRoles: UserRole[] = ['academic_coordinator', 'school_admin', 'platform_admin'];
  const teacherRoles: UserRole[] = ['teacher', 'admin', 'school_admin', 'academic_coordinator'];
  const studentRoles: UserRole[] = ['student'];

  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<RootRedirect />} />

            {/* Admin Routes */}
            <Route
              path="/admin/dashboard"
              element={
                <ProtectedRoute allowedRoles={adminRoles}>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/academic-setup"
              element={
                <ProtectedRoute allowedRoles={adminRoles}>
                  <AcademicSetup />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/bulk-import"
              element={
                <ProtectedRoute allowedRoles={adminRoles}>
                  <BulkImport />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/audit"
              element={
                <ProtectedRoute allowedRoles={adminRoles}>
                  <AuditLogs />
                </ProtectedRoute>
              }
            />

            {/* Academic Coordinator Routes */}
            <Route
              path="/coordinator/dashboard"
              element={
                <ProtectedRoute allowedRoles={coordinatorRoles}>
                  <CoordinatorDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/coordinator/assignments"
              element={
                <ProtectedRoute allowedRoles={coordinatorRoles}>
                  <AssignmentMatrix />
                </ProtectedRoute>
              }
            />

            {/* Teacher Routes */}
            <Route
              path="/teacher/dashboard"
              element={
                <ProtectedRoute allowedRoles={teacherRoles}>
                  <TeacherDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/classes"
              element={
                <ProtectedRoute allowedRoles={teacherRoles}>
                  <TeacherClasses />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/ai-studio"
              element={
                <ProtectedRoute allowedRoles={teacherRoles}>
                  <AIStudio />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/assessments/:assessmentId"
              element={
                <ProtectedRoute allowedRoles={teacherRoles}>
                  <AssessmentEditor />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/assessments"
              element={
                <ProtectedRoute allowedRoles={teacherRoles}>
                  <TeacherAssessments />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/evaluations"
              element={
                <ProtectedRoute allowedRoles={teacherRoles}>
                  <TeacherEvaluationQueue />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/analytics"
              element={
                <ProtectedRoute allowedRoles={teacherRoles}>
                  <TeacherAnalytics />
                </ProtectedRoute>
              }
            />

            {/* Student Routes */}
            <Route
              path="/student/dashboard"
              element={
                <ProtectedRoute allowedRoles={studentRoles}>
                  <StudentDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/student/assessments"
              element={
                <ProtectedRoute allowedRoles={studentRoles}>
                  <StudentUpcomingTests />
                </ProtectedRoute>
              }
            />
            <Route
              path="/student/player/:assessmentId"
              element={
                <ProtectedRoute allowedRoles={studentRoles}>
                  <AssessmentPlayer />
                </ProtectedRoute>
              }
            />
            <Route
              path="/student/results"
              element={
                <ProtectedRoute allowedRoles={studentRoles}>
                  <StudentResults />
                </ProtectedRoute>
              }
            />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
