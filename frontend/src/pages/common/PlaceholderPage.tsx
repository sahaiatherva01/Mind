import React from 'react';
import { Sparkles, Construction } from 'lucide-react';

interface Props {
  title: string;
  description: string;
  phase: string;
}

export const PlaceholderPage: React.FC<Props> = ({ title, description, phase }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm space-y-4">
      <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-xl flex items-center justify-center mx-auto">
        <Sparkles className="w-6 h-6" />
      </div>
      <div>
        <h2 className="text-xl font-bold text-slate-900">{title}</h2>
        <p className="text-sm text-slate-500 mt-1 max-w-lg mx-auto">{description}</p>
      </div>
      <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
        <Construction className="w-3.5 h-3.5 mr-1.5" />
        Scheduled for Delivery in {phase}
      </div>
    </div>
  );
};
