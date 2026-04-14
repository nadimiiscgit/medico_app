import { useState, useMemo } from 'react';
import { useNotes } from '../hooks/useNotes';
import { useQuestions } from '../hooks/useQuestions';
import { SearchIcon, XIcon, TrashIcon, PencilIcon } from 'lucide-react';
import { cn } from '../lib/utils';

const SUBJECT_COLORS: Record<string, string> = {
  Anatomy: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  Physiology: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  Biochemistry: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300',
  Pathology: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
  Pharmacology: 'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300',
  Microbiology: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  Medicine: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  Surgery: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
};

export function Notes() {
  const { notes, saveNote } = useNotes();
  const { questions } = useQuestions();
  const [search, setSearch] = useState('');
  const [filterSubject, setFilterSubject] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');

  const questionMap = useMemo(() => {
    const m: Record<string, typeof questions[0]> = {};
    questions.forEach((q) => { m[q.id] = q; });
    return m;
  }, [questions]);

  const noteEntries = useMemo(() => {
    const entries = Object.entries(notes)
      .map(([id, text]) => ({ id, text, question: questionMap[id] }))
      .filter((e) => e.text.trim());

    return entries.filter((e) => {
      if (filterSubject && e.question?.subject !== filterSubject) return false;
      if (search) {
        const s = search.toLowerCase();
        const inNote = e.text.toLowerCase().includes(s);
        const inQuestion = e.question?.question.toLowerCase().includes(s);
        if (!inNote && !inQuestion) return false;
      }
      return true;
    });
  }, [notes, questionMap, search, filterSubject]);

  const subjects = useMemo(() => {
    const set = new Set<string>();
    Object.keys(notes).forEach((id) => {
      const q = questionMap[id];
      if (q?.subject) set.add(q.subject);
    });
    return [...set].sort();
  }, [notes, questionMap]);

  const totalNotes = Object.keys(notes).filter((id) => notes[id]?.trim()).length;

  const startEdit = (id: string, text: string) => {
    setEditingId(id);
    setEditText(text);
  };

  const saveEdit = () => {
    if (!editingId) return;
    saveNote(editingId, editText);
    setEditingId(null);
  };

  if (totalNotes === 0) {
    return (
      <div className="text-center py-20">
        <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
          <PencilIcon className="w-7 h-7 text-gray-400" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No Notes Yet</h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Add notes to questions while browsing or reviewing — they'll appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">My Notes</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
          {totalNotes} note{totalNotes !== 1 ? 's' : ''} saved
        </p>
      </div>

      {/* Search */}
      <div className="relative">
        <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search your notes…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-10 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <XIcon className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Subject filter */}
      {subjects.length > 1 && (
        <div className="flex flex-wrap gap-1.5">
          <button
            onClick={() => setFilterSubject('')}
            className={cn(
              'px-3 py-1 rounded-full text-xs font-medium transition-colors',
              !filterSubject
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            )}
          >
            All
          </button>
          {subjects.map((s) => (
            <button
              key={s}
              onClick={() => setFilterSubject(filterSubject === s ? '' : s)}
              className={cn(
                'px-3 py-1 rounded-full text-xs font-medium transition-colors',
                filterSubject === s
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              )}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Notes list */}
      {noteEntries.length === 0 ? (
        <p className="text-center py-10 text-sm text-gray-500 dark:text-gray-400">
          No notes match your search.
        </p>
      ) : (
        <div className="space-y-3">
          {noteEntries.map(({ id, text, question }) => (
            <div
              key={id}
              className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden"
            >
              {/* Question context */}
              {question && (
                <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className={cn(
                        'inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold',
                        SUBJECT_COLORS[question.subject] ?? 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                      )}>
                        {question.subject}
                      </span>
                      {question.source !== 'practice' && question.year > 0 && (
                        <span className="text-[10px] text-gray-400 dark:text-gray-500">
                          NEET PG {question.year}
                        </span>
                      )}
                      {question.source === 'practice' && (
                        <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
                          Practice
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 leading-relaxed">
                      {question.question}
                    </p>
                  </div>
                </div>
              )}

              {/* Note body */}
              <div className="px-4 py-3">
                {editingId === id ? (
                  <div className="space-y-2">
                    <textarea
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      rows={3}
                      autoFocus
                      className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={saveEdit}
                        className="px-3 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        className="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap flex-1">
                      {text}
                    </p>
                    <div className="flex gap-1.5 flex-shrink-0">
                      <button
                        onClick={() => startEdit(id, text)}
                        className="p-1.5 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors rounded"
                        title="Edit note"
                      >
                        <PencilIcon className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => {
                          if (window.confirm('Delete this note?')) saveNote(id, '');
                        }}
                        className="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors rounded"
                        title="Delete note"
                      >
                        <TrashIcon className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
