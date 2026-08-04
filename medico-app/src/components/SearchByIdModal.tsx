import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SearchIcon, XIcon } from 'lucide-react';
import { findQuestionById } from '../lib/questionLookup';
import { Button } from './ui/Button';

interface SearchByIdModalProps {
  onClose: () => void;
}

export function SearchByIdModal({ onClose }: SearchByIdModalProps) {
  const navigate = useNavigate();
  const [value, setValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    const id = value.trim();
    if (!id || loading) return;

    setLoading(true);
    setError(null);
    try {
      const found = await findQuestionById(id);
      if (found) {
        onClose();
        navigate(`/question/${encodeURIComponent(found.id)}`);
      } else {
        setError('No question found with that ID.');
      }
    } catch {
      setError('Something went wrong while searching. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-start sm:items-center justify-center px-4 pt-20 sm:pt-4">
        <div className="w-full max-w-sm bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-xl overflow-hidden">
          <div className="flex items-center justify-between px-5 pt-4 pb-3 border-b border-gray-100 dark:border-gray-800">
            <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">Jump to Question</span>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <XIcon className="w-4 h-4" />
            </button>
          </div>

          <div className="p-5 space-y-3">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Paste or type a question ID to open it directly.
            </p>
            <div className="relative">
              <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                autoFocus
                value={value}
                onChange={(e) => { setValue(e.target.value); setError(null); }}
                onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
                placeholder="e.g. neetpg-2019-s1-q0042"
                className="w-full pl-9 pr-3 py-2.5 text-sm font-mono border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            {error && (
              <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
            )}
            <Button onClick={handleSubmit} disabled={!value.trim() || loading} className="w-full">
              {loading ? (
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                'Go'
              )}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}
