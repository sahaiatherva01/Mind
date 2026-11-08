import React, { useState } from 'react';
import { apiRequest } from '../../api/client';
import { FileSpreadsheet, Upload, CheckCircle2, AlertTriangle, Download } from 'lucide-react';

export const BulkImport: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await apiRequest<any>('/academics/bulk-import', {
        method: 'POST',
        body: formData,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Bulk import failed');
    } finally {
      setIsUploading(false);
    }
  };

  const sampleCsv = `full_name,email,role,designation,class,section,subject,roll_number
Mrs. Ananya Sen,ananya.sen@school.edu,Teacher,Senior Faculty,Class 11,E,MATH,
Dr. Rajesh Gupta,rajesh.gupta@school.edu,Academic Coordinator,Coordinator,,,
Aarav Sharma,aarav.sharma@school.edu,Student,,Class 11,E,,11E-01
Diya Mukherjee,diya.m@school.edu,Student,,Class 12,A,,12A-05`;

  const downloadSampleCsv = () => {
    const blob = new Blob([sampleCsv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'mind_bulk_import_template.csv';
    a.click();
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Bulk Excel / CSV Import</h2>
        <p className="text-sm text-slate-500 mt-1">
          Import Institute Administrators, Academic Coordinators, Teachers, and Students with automated class enrollments.
        </p>
      </div>

      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Spreadsheet Template</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Supports .xlsx (Excel) and .csv formats with columns: <code>full_name, email, role, designation, class, section, subject, roll_number</code>
            </p>
          </div>
          <button
            onClick={downloadSampleCsv}
            type="button"
            className="inline-flex items-center px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
          >
            <Download className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
            Download Sample CSV
          </button>
        </div>

        <form onSubmit={handleUpload} className="space-y-4">
          <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-indigo-500 transition-colors bg-slate-50/50">
            <FileSpreadsheet className="w-10 h-10 text-indigo-500 mx-auto mb-3" />
            <div className="text-sm font-medium text-slate-700">
              {file ? file.name : 'Select an Excel (.xlsx) or CSV file'}
            </div>
            <p className="text-xs text-slate-400 mt-1">Files up to 10MB supported</p>
            <label className="mt-4 inline-flex items-center px-4 py-2 bg-white border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer shadow-sm transition-colors">
              <Upload className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
              Browse File
              <input
                type="file"
                accept=".xlsx,.csv"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
          </div>

          <button
            type="submit"
            disabled={!file || isUploading}
            className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm rounded-lg transition-colors shadow-sm disabled:opacity-50"
          >
            {isUploading ? 'Validating and Importing...' : 'Execute Bulk Import'}
          </button>
        </form>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-800 flex items-start">
            <AlertTriangle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Import Error</p>
              <p className="text-xs mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {result && (
          <div className="space-y-4 pt-2">
            <div
              className={`p-4 rounded-xl border flex items-center justify-between ${
                result.success
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                  : 'bg-amber-50 border-amber-200 text-amber-900'
              }`}
            >
              <div className="flex items-center space-x-3">
                {result.success ? (
                  <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
                ) : (
                  <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0" />
                )}
                <div>
                  <h4 className="font-semibold text-sm">
                    {result.success ? 'Import Completed Successfully' : 'Import Completed with Row Warnings'}
                  </h4>
                  <p className="text-xs opacity-90 mt-0.5">
                    {result.imported_count} of {result.total_rows} records imported successfully.
                  </p>
                </div>
              </div>
              <div className="text-right text-xs font-mono font-bold">
                Errors: {result.error_count}
              </div>
            </div>

            {result.errors?.length > 0 && (
              <div className="border border-red-200 rounded-xl overflow-hidden">
                <div className="bg-red-50 px-4 py-2 border-b border-red-200 text-xs font-bold text-red-800 uppercase tracking-wider">
                  Row Error Report
                </div>
                <div className="max-h-60 overflow-y-auto divide-y divide-red-100 text-xs">
                  {result.errors.map((err: any, idx: number) => (
                    <div key={idx} className="p-3 bg-white flex justify-between items-start">
                      <div>
                        <span className="font-bold text-red-700">Row {err.row_number}: </span>
                        <span className="text-slate-800">{err.error}</span>
                      </div>
                      <div className="font-mono text-[11px] text-slate-400">
                        {err.data?.email || JSON.stringify(err.data)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
