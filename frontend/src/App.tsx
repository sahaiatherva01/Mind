import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './pages/auth/LoginPage';
import { DashboardLayout } from './layouts/DashboardLayout';

// Admin Pages
import { AdminDashboard } from './pages/admin/AdminDashboard';
import { AcademicSetup } from './pages/admin/AcademicSetup';
import { BulkImport } from './pages/admin/BulkImport';
import { AuditLogs } from './pages/admin/AuditLogs';

// Teacher Pages
import { TeacherDashboard } from './pages/teacher/TeacherDashboard';
import { TeacherClasses } from './pages/teacher/TeacherClasses';
import { AIStudio } from './pages/teacher/AIStudio';
import { AssessmentEditor } from './pages/teacher/AssessmentEditor';
import { TeacherAssessments } from './pages/teacher/TeacherAssessments';
import { TeacherEvaluationQueue } from './pages/teacher/TeacherEvaluationQueue';

// Student Pages
import { StudentDashboard } from './pages/student/StudentDashboard';
import { StudentUpcomingTests } from './pages/student/StudentUpcomingTests';
import { AssessmentPlayer } from './pages/student/AssessmentPlayer';
import { StudentResults } from './pages/student/StudentResults';

// Common Placeholder
import { PlaceholderPage } from './pages/common/PlaceholderPage';

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

  if (user.role === 'admin') return <Navigate to="/admin/dashboard" replace />;
  if (user.role === 'teacher') return <Navigate to="/teacher/dashboard" replace />;
  if (user.role === 'student') return <Navigate to="/student/dashboard" replace />;

  return <Navigate to="/login" replace />;
};

export const App: React.FC = () => {
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
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/academic-setup"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AcademicSetup />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/bulk-import"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <BulkImport />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/audit"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AuditLogs />
                </ProtectedRoute>
              }
            />

            {/* Teacher Routes */}
            <Route
              path="/teacher/dashboard"
              element={
                <ProtectedRoute allowedRoles={['teacher', 'admin']}>
                  <TeacherDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/classes"
              element={
                <ProtectedRoute allowedRoles={['teacher', 'admin']}>
                  <TeacherClasses />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/ai-studio"
              element={
                <ProtectedRoute allowedRoles={['teacher', 'admin']}>
                  <AIStudio />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/assessments/:assessmentId"
              element={
                <ProtectedRoute allowedRoles={['teacher', 'admin']}>
                  <AssessmentEditor />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/assessments"
              element={
                <ProtectedRoute allowedRoles={['teacher', 'admin']}>
                  <TeacherAssessments />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/evaluations"
              element={
                <ProtectedRoute allowedRoles={['teacher', 'admin']}>
                  <TeacherEvaluationQueue />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/analytics"
              element={
                <ProtectedRoute allowedRoles={['teacher', 'admin']}>
                  <PlaceholderPage
                    title="Academic Performance Analytics"
                    description="Class-level averages, question discrimination, and topic-level mastery insights."
                    phase="Phase 4"
                  />
                </ProtectedRoute>
              }
            />

            {/* Student Routes */}
            <Route
              path="/student/dashboard"
              element={
                <ProtectedRoute allowedRoles={['student']}>
                  <StudentDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/student/assessments"
              element={
                <ProtectedRoute allowedRoles={['student']}>
                  <StudentUpcomingTests />
                </ProtectedRoute>
              }
            />
            <Route
              path="/student/player/:assessmentId"
              element={
                <ProtectedRoute allowedRoles={['student']}>
                  <AssessmentPlayer />
                </ProtectedRoute>
              }
            />
            <Route
              path="/student/results"
              element={
                <ProtectedRoute allowedRoles={['student']}>
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
