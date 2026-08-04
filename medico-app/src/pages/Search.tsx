import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuestions, usePracticeQuestions, useFilteredQuestions } from '../hooks/useQuestions';
import { useProgress } from '../hooks/useProgress';
import { useNotes } from '../hooks/useNotes';
import { findQuestionById } from '../lib/questionLookup';
import { QuestionCard } from '../components/QuestionCard';
import { Card, CardContent } from '../components/ui/Card';
import type { Filters, OptionKey, Question } from '../types';
import { cn } from '../lib/utils';
import { SearchIcon, XIcon, InfoIcon, ArrowRightIcon } from 'lucide-react';

/** Rendering every match would jank the page — 10k PYQ + 11k practice is possible. */
const MAX_RESULTS = 50;

/** Matches the stable ID formats: neetpg-2012-s1-q0001 and medmcqa-000006 */
const ID_PATTERN = /^(neetpg|medmcqa)-[\w-]+$/i;

export function Search() {
  const { questions: pyqQuestions, loading, subjects } = useQuestions();
  const { progress, bookmark, isBookmarked } = useProgress();
  const { notes, saveNote } = useNotes();

  const [rawQuery, setRawQuery] = useState('');
  const [query, setQuery] = useState('');
  const [practiceSubject, setPracticeSubject] = useState('');
  const [selectedOptions, setSelectedOptions] = useState<Record<string, OptionKey | null>>({});
  const [revealedQuestions, setRevealedQuestions] = useState<Set<string>>(new Set());
  const [idLookup, setIdLookup] = useState<{ query: string; question: Question | null } | null>(null);

  // Debounce so we don't re-filter 10k+ questions on every keystroke
  useEffect(() => {
    const t = setTimeout(() => setQuery(rawQuery.trim()), 250);
    return () => clearTimeout(t);
  }, [rawQuery]);

  // An ID-shaped query resolves against the whole bank (both sources) via the
  // shared lookup — no subject selection needed, and it loads the practice
  // index only when the user actually types an ID.
  useEffect(() => {
    if (!ID_PATTERN.test(query)) return;
    let cancelled = false;
    findQuestionById(query).then((found) => {
      if (!cancelled) setIdLookup({ query, question: found });
    });
    return () => { cancelled = true; };
  }, [query]);

  // Derived so a result from a previous query never lingers on screen
  const idMatch =
    ID_PATTERN.test(query) && idLookup?.query === query ? idLookup.question : null;

  // Practice bank is opt-in: the per-subject files are multi-MB, so we can't
  // hold all 19 at once (same constraint as Quiz Mode).
  const { questions: practiceQuestions, loading: practiceLoading } =
    usePracticeQuestions(practiceSubject ? [practiceSubject] : []);

  const pool = useMemo(
    () => (practiceSubject ? [...pyqQuestions, ...practiceQuestions] : pyqQuestions),
    [pyqQuestions, practiceQuestions, practiceSubject]
  );

  const filters: Filters = useMemo(
    () => ({
      source: practiceSubject ? 'both' : 'pyq',
      years: [],
      subjects: [],
      difficulty: [],
      search: query,
      onlyBookmarked: false,
      onlyUnanswered: false,
    }),
    [query, practiceSubject]
  );

  const results = useFilteredQuestions(pool, filters, progress.bookmarks);
  const shown = useMemo(() => results.slice(0, MAX_RESULTS), [results]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Search</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
          Search {pyqQuestions.length.toLocaleString()} PYQs by keyword or question ID
        </p>
      </div>

      {/* Search input */}
      <div className="relative">
        <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={rawQuery}
          onChange={(e) => setRawQuery(e.target.value)}
          placeholder="Search question text, options, or paste a question ID…"
          className="w-full border border-gray-200 dark:border-gray-700 rounded-lg pl-9 pr-9 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        />
        {rawQuery && (
          <button
            onClick={() => setRawQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            aria-label="Clear search"
          >
            <XIcon className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Practice bank opt-in */}
      <div>
        <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
          Also search practice questions
        </label>
        <select
          value={practiceSubject}
          onChange={(e) => setPracticeSubject(e.target.value)}
          className="w-full border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        >
          <option value="">PYQ only</option>
          {subjects.map((s) => (
            <option key={s} value={s}>{s} (practice)</option>
          ))}
        </select>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">
          Practice questions load one subject at a time — the full bank is too large to search at once.
        </p>
      </div>

      {practiceLoading && (
        <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          Loading {practiceSubject} practice questions…
        </div>
      )}

      {/* Exact ID hit — works across both banks regardless of the subject picker */}
      {idMatch && (
        <Link
          to={`/question/${idMatch.id}`}
          className="flex items-center justify-between gap-3 px-4 py-3 rounded-xl border border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/30 hover:bg-blue-100 dark:hover:bg-blue-950/50 transition-colors"
        >
          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-blue-600 dark:text-blue-400">
              Exact ID match
            </p>
            <p className="text-sm text-gray-900 dark:text-gray-100 truncate mt-0.5">
              {idMatch.question}
            </p>
          </div>
          <ArrowRightIcon className="w-4 h-4 flex-shrink-0 text-blue-600 dark:text-blue-400" />
        </Link>
      )}

      {/* Results */}
      {!query ? (
        <Card>
          <CardContent className="flex items-start gap-2.5 text-sm text-gray-500 dark:text-gray-400">
            <InfoIcon className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>
              Type to search. Keywords match the question text and all four options; you can also paste
              an exact question ID to jump straight to it.
            </span>
          </CardContent>
        </Card>
      ) : results.length === 0 && !idMatch ? (
        <div className="text-center py-16">
          <div className="w-14 h-14 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-3">
            <SearchIcon className="w-7 h-7 text-gray-400 dark:text-gray-500" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">No matches</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
            Nothing matched "{query}". Try a different keyword, or pick a practice subject above to
            widen the search.
          </p>
        </div>
      ) : results.length === 0 ? null : (
        <>
          <p className={cn('text-sm text-gray-500 dark:text-gray-400')}>
            {results.length > MAX_RESULTS
              ? `Showing first ${MAX_RESULTS} of ${results.length.toLocaleString()} matches`
              : `${results.length} match${results.length !== 1 ? 'es' : ''}`}
          </p>

          <div className="space-y-4">
            {shown.map((q, idx) => (
              <QuestionCard
                key={q.id}
                question={q}
                questionIndex={idx}
                totalQuestions={shown.length}
                isBookmarked={isBookmarked(q.id)}
                onBookmark={() => bookmark(q)}
                showAnswer={revealedQuestions.has(q.id)}
                selectedOption={selectedOptions[q.id] ?? null}
                onSelectOption={(opt) => setSelectedOptions((prev) => ({ ...prev, [q.id]: opt }))}
                onSubmit={() => setRevealedQuestions((prev) => new Set([...prev, q.id]))}
                mode={selectedOptions[q.id] && !revealedQuestions.has(q.id) ? 'quiz' : 'browse'}
                isAnswered={revealedQuestions.has(q.id)}
                note={notes[q.id] ?? ''}
                onSaveNote={(n) => saveNote(q.id, n)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
