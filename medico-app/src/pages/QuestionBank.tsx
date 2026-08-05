import { useState, useEffect, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { usePracticeQuestions } from '../hooks/useQuestions';
import { useProgress } from '../hooks/useProgress';
import { useNotes } from '../hooks/useNotes';
import { QuestionCard } from '../components/QuestionCard';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import type { OptionKey } from '../types';
import { cn } from '../lib/utils';
import { ArrowLeftIcon, ChevronRightIcon, LibraryIcon, PlayIcon } from 'lucide-react';

interface SubjectEntry {
  subject: string;
  count: number;
}

const PAGE_SIZE = 20;

export function QuestionBank() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedSubject = searchParams.get('subject');

  const { bookmark, isBookmarked } = useProgress();
  const { notes, saveNote } = useNotes();

  // Tiny manifest (<1 KB) so the landing grid shows counts without pulling
  // any question data.
  const [subjects, setSubjects] = useState<SubjectEntry[]>([]);
  const [manifestError, setManifestError] = useState(false);

  useEffect(() => {
    fetch('/practice_subjects.json')
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load subjects');
        return r.json() as Promise<SubjectEntry[]>;
      })
      .then(setSubjects)
      .catch(() => setManifestError(true));
  }, []);

  const totalQuestions = useMemo(
    () => subjects.reduce((sum, s) => sum + s.count, 0),
    [subjects]
  );

  const { questions, loading } = usePracticeQuestions(selectedSubject ? [selectedSubject] : []);

  const [selectedOptions, setSelectedOptions] = useState<Record<string, OptionKey | null>>({});
  const [revealedQuestions, setRevealedQuestions] = useState<Set<string>>(new Set());

  // Pagination is scoped to the subject it was set on, so switching subjects
  // falls back to page 0 without an effect resetting it after a render.
  const [pageState, setPageState] = useState<{ subject: string | null; page: number }>({
    subject: selectedSubject,
    page: 0,
  });
  const page = pageState.subject === selectedSubject ? pageState.page : 0;
  const setPage = (next: number | ((p: number) => number)) =>
    setPageState({
      subject: selectedSubject,
      page: typeof next === 'function' ? next(page) : next,
    });

  const pageQuestions = useMemo(
    () => questions.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE),
    [questions, page]
  );
  const pageCount = Math.ceil(questions.length / PAGE_SIZE);

  // ── Landing: subject grid ────────────────────────────────────────────
  if (!selectedSubject) {
    return (
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Question Bank</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            {totalQuestions > 0
              ? `${totalQuestions.toLocaleString()} practice questions across ${subjects.length} subjects`
              : 'Browse practice questions by subject'}
          </p>
        </div>

        {manifestError && (
          <Card>
            <CardContent className="text-sm text-gray-500 dark:text-gray-400">
              Couldn't load the subject list. Please refresh and try again.
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {subjects.map(({ subject, count }) => (
            <button
              key={subject}
              onClick={() => setSearchParams({ subject })}
              className="flex items-center justify-between px-4 py-3.5 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 hover:border-blue-400 dark:hover:border-blue-600 transition-colors text-left"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-9 h-9 flex-shrink-0 bg-blue-100 dark:bg-blue-900/40 rounded-lg flex items-center justify-center">
                  <LibraryIcon className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                    {subject}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {count.toLocaleString()} questions
                  </p>
                </div>
              </div>
              <ChevronRightIcon className="w-4 h-4 flex-shrink-0 text-gray-400" />
            </button>
          ))}
        </div>
      </div>
    );
  }

  // ── Subject view: browse questions ───────────────────────────────────
  return (
    <div className="space-y-4">
      <button
        onClick={() => setSearchParams({})}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
      >
        <ArrowLeftIcon className="w-4 h-4" />
        All subjects
      </button>

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">{selectedSubject}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            {loading ? 'Loading…' : `${questions.length.toLocaleString()} questions`}
          </p>
        </div>
        <Link to={`/quiz?subject=${encodeURIComponent(selectedSubject)}`}>
          <Button size="sm">
            <PlayIcon className="w-4 h-4" />
            Quiz me
          </Button>
        </Link>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {pageQuestions.map((q, idx) => (
              <QuestionCard
                key={q.id}
                question={q}
                questionIndex={page * PAGE_SIZE + idx}
                totalQuestions={questions.length}
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

          {pageCount > 1 && (
            <div className="flex items-center justify-between gap-3 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
              >
                Previous
              </Button>
              <span className={cn('text-sm text-gray-500 dark:text-gray-400')}>
                Page {page + 1} of {pageCount.toLocaleString()}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
                disabled={page >= pageCount - 1}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
