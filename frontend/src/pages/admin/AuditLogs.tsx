import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../api/client';

export const AuditLogs: React.FC = () => {
  const [events, setEvents] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadAudit() {
      try {
        const res = await apiRequest<{ items: any[]; total: number }>('/audit-events?limit=100');
        setEvents(res.items);
      } catch (err) {
        console.error('Failed to load audit logs', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadAudit();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Security & Administrative Audit Trail</h2>
        <p className="text-sm text-slate-500 mt-1">
          Immutable log of all authorization, configuration, publishing, and security events.
        </p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider">
            <tr>
              <th className="px-6 py-3 text-left">Timestamp (UTC)</th>
              <th className="px-6 py-3 text-left">Action</th>
              <th className="px-6 py-3 text-left">Entity</th>
              <th className="px-6 py-3 text-left">Metadata</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {isLoading ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-slate-400">
                  Loading audit events...
                </td>
              </tr>
            ) : events.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-slate-400">
                  No audit events recorded yet.
                </td>
              </tr>
            ) : (
              events.map((e) => (
                <tr key={e.id} className="hover:bg-slate-50/50">
                  <td className="px-6 py-3.5 text-xs font-mono text-slate-500 whitespace-nowrap">
                    {new Date(e.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-3.5">
                    <span className="px-2 py-0.5 rounded text-xs font-semibold bg-indigo-50 text-indigo-700 font-mono">
                      {e.action}
                    </span>
                  </td>
                  <td className="px-6 py-3.5 text-xs text-slate-700">
                    <span className="font-semibold">{e.entity_type}</span>
                    {e.entity_id && <span className="font-mono text-slate-400 ml-1.5 text-[11px]">({e.entity_id.slice(0, 8)}...)</span>}
                  </td>
                  <td className="px-6 py-3.5 text-xs font-mono text-slate-500 max-w-xs truncate">
                    {JSON.stringify(e.metadata_json || {})}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
