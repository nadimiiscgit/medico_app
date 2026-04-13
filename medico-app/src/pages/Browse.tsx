import { useState, useMemo } from 'react';
import { useQuestions, useFilteredQuestions, usePracticeQuestions } from '../hooks/useQuestions';
import { useProgress } from '../hooks/useProgress';
import { useNotes } from '../hooks/useNotes';
import { QuestionCard } from '../components/QuestionCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import type { Filters, OptionKey } from '../types';
import {
  SearchIcon,
  XIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  SlidersIcon,
  InfoIcon,
} from 'lucide-react';

const PAGE_SIZE = 20;

const DEFAULT_FILTERS: Filters = {
  source: 'pyq',
  years: [],
  subjects: [],
  difficulty: [],
  search: '',
  onlyBookmarked: false,
  onlyUnanswered: false,
};

export function Browse() {
  const { questions: pyqQuestions, loading: pyqLoading, years, subjects } = useQuestions();
  const { progress, bookmark, isBookmarked } = useProgress();
  const { notes, saveNote } = useNotes();
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [page, setPage] = useState(0);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedOptions, setSelectedOptions] = useState<Record<string, OptionKey | null>>({});
  const [revealedQuestions, setRevealedQuestions] = useState<Set<string>>(new Set());

  // Only load practice subjects that are explicitly filtered (avoids loading 100MB all at once)
  const practiceSubjectsToLoad = useMemo(() => {
    if (filters.source === 'pyq') return [];
    // Require at least one subject to be selected before loading practice questions
    return filters.subjects.length > 0 ? filters.subjects : [];
  }, [filters.source, filters.subjects]);

  const { questions: practiceQuestions, loading: practiceLoading } =
    usePracticeQuestions(practiceSubjectsToLoad);

  // Build the question pool based on the source toggle
  const pool = useMemo(() => {
    if (filters.source === 'pyq') return pyqQuestions;
    if (filters.source === 'practice') return practiceQuestions;
    return [...pyqQuestions, ...practiceQuestions];
  }, [filters.source, pyqQuestions, practiceQuestions]);

  const loading = pyqLoading || practiceLoading;

  const filtered = useFilteredQuestions(pool, filters, progress.bookmarks);
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const activeFilterCount = [
    filters.years.length > 0,
    filters.subjects.length > 0,
    filters.difficulty.length > 0,
    filters.onlyBookmarked,
    filters.onlyUnanswered,
  ].filter(Boolean).length;

  const updateFilter = <K extends keyof Filters>(key: K, value: Filters[K]) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0);
  };

  const toggleArrayFilter = (key: 'years' | 'subjects' | 'difficulty', value: string | number) => {
    setFilters((prev) => {
      const arr = prev[key] as (string | number)[];
      const next = arr.includes(value as never)
        ? arr.filter((v) => v !== value)
        : [...arr, value];
      return { ...prev, [key]: next };
    });
    setPage(0);
  };

  const clearFilters = () => {
    setFilters((prev) => ({ ...DEFAULT_FILTERS, source: prev.source }));
    setPage(0);
  };

  const handleSelectOption = (questionId: string, opt: OptionKey) => {
    setSelectedOptions((prev) => ({ ...prev, [questionId]: opt }));
  };

  const handleReveal = (questionId: string) => {
    setRevealedQuestions((prev) => {
      const next = new Set(prev);
      next.add(questionId);
      return next;
    });
  };

  // Whether to show a hint that a subject must be selected for practice
  const needsSubjectSelect =
    filters.source !== 'pyq' && filters.subjects.length === 0;

  if (pyqLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Browse Questions</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            {needsSubjectSelect
              ? `${pyqQuestions.length.toLocaleString()} PYQ questions`
              : `${filtered.length.toLocaleString()} of ${pool.length.toLocaleString()} questions`}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
          className="relative"
        >
          <SlidersIcon className="w-4 h-4" />
          Filters
          {activeFilterCount > 0 && (
            <span className="absolute -top-1.5 -right-1.5 w-4.5 h-4.5 bg-blue-600 text-white text-[10px] rounded-full flex items-center justify-center font-bold">
              {activeFilterCount}
            </span>
          )}
        </Button>
      </div>

      {/* Source toggle */}
      <div className="flex rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden text-xs font-semibold">
        {(['pyq', 'practice', 'both'] as const).map((src) => (
          <button
            key={src}
            onClick={() => { updateFilter('source', src); }}
            className={`flex-1 py-2 px-3 transition-colors ${
              filters.source === src
                ? 'bg-blue-600 text-white'
                : 'bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
            }`}
          >
            {src === 'pyq' ? 'PYQ Only' : src === 'practice' ? 'Practice' : 'Both'}
          </button>
        ))}
      </div>

      {/* Hint when practice selected but no subject chosen */}
      {needsSubjectSelect && (
        <div className="flex items-start gap-2.5 px-4 py-3 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-sm text-amber-800 dark:text-amber-300">
          <InfoIcon className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>Select a <strong>Subject</strong> below to load practice questions. Loading all at once is too large.</span>
        </div>
      )}

      {/* Practice loading indicator */}
      {practiceLoading && (
        <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          Loading practice questions…
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search questions..."
          value={filters.search}
          onChange={(e) => updateFilter('search', e.target.value)}
          className="w-full pl-9 pr-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
        />
        {filters.search && (
          <button
            onClick={() => updateFilter('search', '')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <XIcon className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 space-y-4">
          {/* Year filter — only relevant for PYQ */}
          {filters.source !== 'practice' && (
            <div>
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Year</p>
              <div className="flex flex-wrap gap-1.5">
                {years.map((y) => (
                  <button
                    key={y}
                    onClick={() => toggleArrayFilter('years', y)}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                      filters.years.includes(y)
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                    }`}
                  >
                    {y}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Subject filter */}
          <div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
              Subject {filters.source !== 'pyq' && <span className="text-amber-600 dark:text-amber-400 normal-case font-normal">(required for practice)</span>}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {subjects.map((s) => (
                <button
                  key={s}
                  onClick={() => toggleArrayFilter('subjects', s)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                    filters.subjects.includes(s)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Difficulty filter */}
          <div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Difficulty</p>
            <div className="flex gap-2">
              {(['Easy', 'Medium', 'Hard'] as const).map((d) => (
                <button
                  key={d}
                  onClick={() => toggleArrayFilter('difficulty', d)}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                    filters.difficulty.includes(d)
                      ? d === 'Easy' ? 'bg-green-600 text-white'
                        : d === 'Medium' ? 'bg-yellow-500 text-white'
                        : 'bg-red-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          {/* Special filters */}
          <div className="flex gap-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.onlyBookmarked}
                onChange={(e) => updateFilter('onlyBookmarked', e.target.checked)}
                className="w-4 h-4 accent-blue-600"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">Bookmarked only</span>
            </label>
          </div>

          {activeFilterCount > 0 && (
            <Button variant="ghost" size="sm" onClick={clearFilters} className="text-red-600 hover:text-red-800 hover:bg-red-50 dark:hover:bg-red-950/30">
              <XIcon className="w-3.5 h-3.5" />
              Clear all filters
            </Button>
          )}
        </div>
      )}

      {/* Active filter badges */}
      {activeFilterCount > 0 && !showFilters && (
        <div className="flex items-center gap-2 flex-wrap">
          {filters.years.map((y) => (
            <Badge key={y} variant="default" className="cursor-pointer" onClick={() => toggleArrayFilter('years', y)}>
              {y} ×
            </Badge>
          ))}
          {filters.subjects.map((s) => (
            <Badge key={s} variant="secondary" className="cursor-pointer" onClick={() => toggleArrayFilter('subjects', s)}>
              {s} ×
            </Badge>
          ))}
          {filters.difficulty.map((d) => (
            <Badge key={d} variant="outline" className="cursor-pointer" onClick={() => toggleArrayFilter('difficulty', d)}>
              {d} ×
            </Badge>
          ))}
          {filters.onlyBookmarked && (
            <Badge variant="default" className="cursor-pointer" onClick={() => updateFilter('onlyBookmarked', false)}>
              Bookmarked ×
            </Badge>
          )}
        </div>
      )}

      {/* Questions */}
      {needsSubjectSelect ? null : paginated.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-500 dark:text-gray-400">No questions match your filters.</p>
          <Button variant="ghost" onClick={clearFilters} className="mt-3 text-blue-600 dark:text-blue-400">
            Clear filters
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {paginated.map((q, idx) => (
            <div key={q.id}>
              <QuestionCard
                question={q}
                questionIndex={page * PAGE_SIZE + idx}
                totalQuestions={filtered.length}
                isBookmarked={isBookmarked(q.id)}
                onBookmark={() => bookmark(q.id)}
                showAnswer={revealedQuestions.has(q.id)}
                selectedOption={selectedOptions[q.id] ?? null}
                onSelectOption={(opt) => handleSelectOption(q.id, opt)}
                onSubmit={() => handleReveal(q.id)}
                mode={selectedOptions[q.id] && !revealedQuestions.has(q.id) ? 'quiz' : 'browse'}
                isAnswered={revealedQuestions.has(q.id)}
                note={notes[q.id] ?? ''}
                onSaveNote={(n) => saveNote(q.id, n)}
              />
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {!needsSubjectSelect && totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
          >
            <ChevronLeftIcon className="w-4 h-4" />
          </Button>
          <span className="text-sm text-gray-600 dark:text-gray-400 font-medium px-3">
            Page {page + 1} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={page === totalPages - 1}
          >
            <ChevronRightIcon className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
