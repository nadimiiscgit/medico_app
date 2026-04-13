import { useState, useMemo } from 'react';
import { useQuestions, useFilteredQuestions } from '../hooks/useQuestions';
import { useProgress } from '../hooks/useProgress';
import { QuestionCard } from '../components/QuestionCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import type { Filters, OptionKey } from '../types';
import {
  SearchIcon,
  FilterIcon,
  XIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  SlidersIcon,
} from 'lucide-react';

const PAGE_SIZE = 20;

const DEFAULT_FILTERS: Filters = {
  years: [],
  subjects: [],
  difficulty: [],
  search: '',
  onlyBookmarked: false,
  onlyUnanswered: false,
};

export function Browse() {
  const { questions, loading, years, subjects } = useQuestions();
  const { progress, bookmark, isBookmarked } = useProgress();
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [page, setPage] = useState(0);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedOptions, setSelectedOptions] = useState<Record<string, OptionKey | null>>({});
  const [revealedQuestions, setRevealedQuestions] = useState<Set<string>>(new Set());

  const filtered = useFilteredQuestions(questions, filters, progress.bookmarks);
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
    setFilters(DEFAULT_FILTERS);
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

  if (loading) {
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
            {filtered.length.toLocaleString()} of {questions.length.toLocaleString()} questions
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
          {/* Year filter */}
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

          {/* Subject filter */}
          <div>
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Subject</p>
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
      {paginated.length === 0 ? (
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
              />
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
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
