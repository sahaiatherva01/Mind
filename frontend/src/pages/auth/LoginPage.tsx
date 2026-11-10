import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Lock, Mail, AlertCircle, ArrowRight, Sparkles } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const setDemoAccount = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-12 h-12 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-extrabold text-2xl shadow-md">
            M
          </div>
        </div>
        <h2 className="mt-4 text-center text-3xl font-bold tracking-tight text-slate-900">
          Mind
        </h2>
        <p className="mt-1 text-center text-sm text-slate-600">
          Intelligence for Better Learning
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm rounded-xl border border-slate-200 sm:px-10">
          <form className="space-y-5" onSubmit={handleSubmit}>
            {error && (
              <div className="p-3 rounded-lg bg-red-50 border border-red-200 flex items-start text-sm text-red-700">
                <AlertCircle className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0 text-red-500" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Email Address
              </label>
              <div className="mt-1.5 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 outline-none"
                  placeholder="name@school.edu"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Password
              </label>
              <div className="mt-1.5 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 outline-none"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors"
            >
              {isLoading ? 'Signing In...' : 'Sign In to Workspace'}
              <ArrowRight className="ml-2 w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Credentials for Manual Testing */}
          <div className="mt-8 pt-6 border-t border-slate-200">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 text-center mb-3 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 mr-1 text-indigo-500" />
              Quick Demo Logins
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
              <button
                type="button"
                onClick={() => setDemoAccount('platform.admin@mind.local', 'PlatformPass123!')}
                className="px-2.5 py-1.5 rounded border border-purple-200 hover:border-purple-500 hover:bg-purple-50/50 text-slate-700 text-left transition-colors truncate"
              >
                <span className="font-semibold block text-purple-900">Platform Admin</span>
                platform.admin@mind.local
              </button>
              <button
                type="button"
                onClick={() => setDemoAccount('admin@mind.local', 'AdminPass123!')}
                className="px-2.5 py-1.5 rounded border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/50 text-slate-700 text-left transition-colors truncate"
              >
                <span className="font-semibold block text-slate-900">School Admin</span>
                admin@mind.local
              </button>
              <button
                type="button"
                onClick={() => setDemoAccount('coord.senior@mind.local', 'CoordPass123!')}
                className="px-2.5 py-1.5 rounded border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/50 text-slate-700 text-left transition-colors truncate"
              >
                <span className="font-semibold block text-slate-900">Coordinator (11-12)</span>
                coord.senior@mind.local
              </button>
              <button
                type="button"
                onClick={() => setDemoAccount('maths.teacher@mind.local', 'TeacherPass123!')}
                className="px-2.5 py-1.5 rounded border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/50 text-slate-700 text-left transition-colors truncate"
              >
                <span className="font-semibold block text-slate-900">Maths Teacher</span>
                maths.teacher@mind.local
              </button>
              <button
                type="button"
                onClick={() => setDemoAccount('physics.teacher@mind.local', 'TeacherPass123!')}
                className="px-2.5 py-1.5 rounded border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/50 text-slate-700 text-left transition-colors truncate"
              >
                <span className="font-semibold block text-slate-900">Physics Teacher</span>
                physics.teacher@mind.local
              </button>
              <button
                type="button"
                onClick={() => setDemoAccount('student.aarav@mind.local', 'StudentPass123!')}
                className="px-2.5 py-1.5 rounded border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50/50 text-slate-700 text-left transition-colors truncate"
              >
                <span className="font-semibold block text-slate-900">Student (11E)</span>
                Aarav Gupta
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

