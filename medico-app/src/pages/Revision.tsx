import { useState, useMemo } from 'react';
import { REVISION_NOTES } from '../data/revisionNotes';
import { cn } from '../lib/utils';
import { SearchIcon, XIcon, ChevronDownIcon, ChevronUpIcon } from 'lucide-react';

export function Revision() {
  const [search, setSearch] = useState('');
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    return REVISION_NOTES
      .filter((n) => !selectedSubject || n.subject === selectedSubject)
      .map((note) => {
        if (!q) return note;
        const sections = note.sections
          .map((s) => ({
            ...s,
            points: s.points.filter((p) => p.toLowerCase().includes(q)),
          }))
          .filter((s) => s.points.length > 0 || s.title.toLowerCase().includes(q));
        return { ...note, sections };
      })
      .filter((n) => n.sections.length > 0);
  }, [search, selectedSubject]);

  const toggleSection = (key: string) => {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const totalPoints = REVISION_NOTES.reduce(
    (acc, n) => acc + n.sections.reduce((a, s) => a + s.points.length, 0),
    0
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Revision Notes</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
          {totalPoints} high-yield NEET PG points across {REVISION_NOTES.length} subjects
        </p>
      </div>

      {/* Search */}
      <div className="relative">
        <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search any topic, drug, sign…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-10 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <XIcon className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Subject pills */}
      <div className="flex flex-wrap gap-1.5">
        <button
          onClick={() => setSelectedSubject(null)}
          className={cn(
            'px-3 py-1 rounded-full text-xs font-medium transition-colors',
            !selectedSubject
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
          )}
        >
          All
        </button>
        {REVISION_NOTES.map((n) => (
          <button
            key={n.subject}
            onClick={() => setSelectedSubject(selectedSubject === n.subject ? null : n.subject)}
            className={cn(
              'px-3 py-1 rounded-full text-xs font-medium transition-colors',
              selectedSubject === n.subject
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            )}
          >
            {n.subject}
          </button>
        ))}
      </div>

      {/* Results count when searching */}
      {search && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {filtered.reduce((acc, n) => acc + n.sections.reduce((a, s) => a + s.points.length, 0), 0)} matching points
        </p>
      )}

      {/* Notes */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-500 dark:text-gray-400">
          No results for "{search}"
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((note) => (
            <div
              key={note.subject}
              className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden"
            >
              {/* Subject header */}
              <div className="px-5 py-3 border-b border-gray-100 dark:border-gray-800">
                <span className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold', note.color)}>
                  {note.subject}
                </span>
              </div>

              {/* Sections */}
              <div className="divide-y divide-gray-100 dark:divide-gray-800">
                {note.sections.map((section) => {
                  const key = `${note.subject}::${section.title}`;
                  const isOpen = search ? true : (expandedSections[key] ?? false);
                  return (
                    <div key={section.title}>
                      <button
                        onClick={() => !search && toggleSection(key)}
                        className={cn(
                          'w-full flex items-center justify-between px-5 py-3 text-left',
                          !search && 'hover:bg-gray-50 dark:hover:bg-gray-800/60 transition-colors'
                        )}
                      >
                        <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                          {section.title}
                          <span className="ml-2 text-xs font-normal text-gray-400 dark:text-gray-500">
                            {section.points.length} points
                          </span>
                        </span>
                        {!search && (
                          isOpen
                            ? <ChevronUpIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            : <ChevronDownIcon className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        )}
                      </button>

                      {isOpen && (
                        <ul className="px-5 pb-4 space-y-2">
                          {section.points.map((point, i) => {
                            const highlighted = search
                              ? point.replace(
                                  new RegExp(`(${search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'),
                                  '<mark class="bg-yellow-200 dark:bg-yellow-800/60 rounded px-0.5">$1</mark>'
                                )
                              : point;
                            return (
                              <li key={i} className="flex items-start gap-2.5">
                                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0" />
                                <span
                                  className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed"
                                  dangerouslySetInnerHTML={{ __html: highlighted }}
                                />
                              </li>
                            );
                          })}
                        </ul>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
