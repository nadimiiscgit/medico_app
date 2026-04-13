import { useState, useEffect, useMemo } from 'react';
import type { Question, Filters } from '../types';

interface UseQuestionsReturn {
  questions: Question[];
  loading: boolean;
  error: string | null;
  years: number[];
  subjects: string[];
}

// ---------------------------------------------------------------------------
// PYQ questions — loaded once, cached globally
// ---------------------------------------------------------------------------

let pyqCache: Question[] | null = null;

export function useQuestions(): UseQuestionsReturn {
  const [questions, setQuestions] = useState<Question[]>(pyqCache ?? []);
  const [loading, setLoading] = useState(pyqCache === null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (pyqCache) {
      setQuestions(pyqCache);
      setLoading(false);
      return;
    }

    fetch('/questions.json')
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load questions');
        return r.json();
      })
      .then((data: Question[]) => {
        pyqCache = data;
        setQuestions(data);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  const years = useMemo(
    () => [...new Set(questions.map((q) => q.year))].sort((a, b) => b - a),
    [questions]
  );

  const subjects = useMemo(
    () => [...new Set(questions.map((q) => q.subject))].sort(),
    [questions]
  );

  return { questions, loading, error, years, subjects };
}

// ---------------------------------------------------------------------------
// Practice questions — lazy loaded per subject, cached globally
// ---------------------------------------------------------------------------

/** Convert a subject name to the filename slug (must match split_practice_by_subject.py) */
function subjectSlug(subject: string): string {
  return subject.replace(/[^A-Za-z0-9]+/g, '_').replace(/^_|_$/, '');
}

// Global per-subject cache so each file is only fetched once per session
const practiceCache: Record<string, Question[]> = {};

interface UsePracticeQuestionsReturn {
  questions: Question[];
  loading: boolean;
  error: string | null;
}

/**
 * Lazy-loads practice questions for the given subjects.
 * - Pass an empty array to load nothing (e.g. when "All" is selected).
 * - Each subject file is fetched at most once per session (cached in module scope).
 */
export function usePracticeQuestions(subjects: string[]): UsePracticeQuestionsReturn {
  const subjectsKey = useMemo(() => subjects.slice().sort().join(','), [subjects]);

  const [state, setState] = useState<{
    loaded: Record<string, Question[]>;
    loading: boolean;
    error: string | null;
  }>({ loaded: {}, loading: false, error: null });

  useEffect(() => {
    if (subjects.length === 0) {
      setState({ loaded: {}, loading: false, error: null });
      return;
    }

    const toFetch = subjects.filter((s) => !(s in practiceCache));

    if (toFetch.length === 0) {
      // All already cached — just update state
      const loaded: Record<string, Question[]> = {};
      subjects.forEach((s) => { loaded[s] = practiceCache[s]; });
      setState({ loaded, loading: false, error: null });
      return;
    }

    setState((prev) => ({ ...prev, loading: true, error: null }));

    Promise.all(
      toFetch.map((s) =>
        fetch(`/practice_${subjectSlug(s)}.json`)
          .then((r) => {
            if (!r.ok) throw new Error(`Failed to load practice questions for ${s}`);
            return r.json() as Promise<Question[]>;
          })
          .then((data) => {
            practiceCache[s] = data;
            return s;
          })
      )
    )
      .then(() => {
        const loaded: Record<string, Question[]> = {};
        subjects.forEach((s) => { loaded[s] = practiceCache[s] ?? []; });
        setState({ loaded, loading: false, error: null });
      })
      .catch((e) => {
        setState((prev) => ({ ...prev, loading: false, error: e.message }));
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subjectsKey]);

  const questions = useMemo(
    () => subjects.flatMap((s) => state.loaded[s] ?? []),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [state.loaded, subjectsKey]
  );

  return { questions, loading: state.loading, error: state.error };
}

// ---------------------------------------------------------------------------
// Filtering — works on any question array regardless of source
// ---------------------------------------------------------------------------

export function useFilteredQuestions(
  questions: Question[],
  filters: Filters,
  bookmarks: string[]
) {
  return useMemo(() => {
    return questions.filter((q) => {
      // Year filter only applies to PYQ (practice questions have year=0)
      if (filters.years.length > 0 && q.year > 0 && !filters.years.includes(q.year)) return false;
      if (filters.subjects.length > 0 && !filters.subjects.includes(q.subject)) return false;
      if (filters.difficulty.length > 0 && !filters.difficulty.includes(q.difficulty)) return false;
      if (filters.onlyBookmarked && !bookmarks.includes(q.id)) return false;
      if (filters.search) {
        const s = filters.search.toLowerCase();
        const inQ = q.question.toLowerCase().includes(s);
        const inOpts = Object.values(q.options).some((o) => o.toLowerCase().includes(s));
        if (!inQ && !inOpts) return false;
      }
      return true;
    });
  }, [questions, filters, bookmarks]);
}
