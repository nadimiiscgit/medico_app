import type { Question } from '../types';
import { fetchPyqQuestions, fetchPracticeQuestionsForSubject } from '../hooks/useQuestions';

let practiceIdIndex: Record<string, string> | null = null;
let practiceIdIndexPromise: Promise<Record<string, string>> | null = null;

function getPracticeIdIndex(): Promise<Record<string, string>> {
  if (practiceIdIndex) return Promise.resolve(practiceIdIndex);
  if (!practiceIdIndexPromise) {
    practiceIdIndexPromise = fetch('/practice_id_index.json')
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load practice question index');
        return r.json() as Promise<Record<string, string>>;
      })
      .then((data) => {
        practiceIdIndex = data;
        return data;
      });
  }
  return practiceIdIndexPromise;
}

/** Finds a single question by its stable ID, loading whichever source file(s) are needed. */
export async function findQuestionById(rawId: string): Promise<Question | null> {
  const id = rawId.trim();
  if (!id) return null;

  if (id.startsWith('neetpg-')) {
    const questions = await fetchPyqQuestions();
    return questions.find((q) => q.id === id) ?? null;
  }

  const index = await getPracticeIdIndex();
  const subject = index[id];
  if (!subject) return null;

  const questions = await fetchPracticeQuestionsForSubject(subject);
  return questions.find((q) => q.id === id) ?? null;
}
