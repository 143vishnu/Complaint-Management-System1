import React, { useState } from 'react';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { exportAPI } from '../../lib/featureUtils';

export default function ExportButton({ token, variant = 'default' }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleExport = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await exportAPI.exportCSV(token);
      setSuccess('✅ Complaints exported successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('❌ Failed to export complaints');
    } finally {
      setLoading(false);
    }
  };

  const buttonClasses =
    variant === 'icon'
      ? 'p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors'
      : 'px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition-colors flex items-center gap-2';

  return (
    <div className="relative">
      <button
        onClick={handleExport}
        disabled={loading}
        className={buttonClasses}
        title="Export complaints to CSV"
      >
        {loading ? (
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-current"></div>
        ) : (
          <>
            <ArrowDownTrayIcon className="h-5 w-5" />
            {variant !== 'icon' && <span>Export CSV</span>}
          </>
        )}
      </button>

      {error && (
        <div className="absolute top-full right-0 mt-2 px-3 py-2 bg-red-600 text-white text-sm rounded-lg whitespace-nowrap z-10">
          {error}
        </div>
      )}

      {success && (
        <div className="absolute top-full right-0 mt-2 px-3 py-2 bg-green-600 text-white text-sm rounded-lg whitespace-nowrap z-10">
          {success}
        </div>
      )}
    </div>
  );
}
