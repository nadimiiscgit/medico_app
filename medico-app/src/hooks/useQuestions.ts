import { useState, useEffect, useMemo } from 'react';
import type { Question, Filters } from '../types';

interface UseQuestionsReturn {
  questions: Question[];
  loading: boolean;
  error: string | null;
  years: number[];
  subjects: string[];
}

let questionsCache: Question[] | null = null;

export function useQuestions(): UseQuestionsReturn {
  const [questions, setQuestions] = useState<Question[]>(questionsCache ?? []);
  const [loading, setLoading] = useState(questionsCache === null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (questionsCache) {
      setQuestions(questionsCache);
      setLoading(false);
      return;
    }

    fetch('/questions.json')
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load questions');
        return r.json();
      })
      .then((data: Question[]) => {
        questionsCache = data;
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

export function useFilteredQuestions(
  questions: Question[],
  filters: Filters,
  bookmarks: string[]
) {
  return useMemo(() => {
    return questions.filter((q) => {
      if (filters.years.length > 0 && !filters.years.includes(q.year)) return false;
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
