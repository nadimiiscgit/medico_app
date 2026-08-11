import type { Question } from '../types';
import { subjectSlug } from '../hooks/useQuestions';

interface ExplanationEntry {
  text: string;
  ai?: boolean;
}

type ExplanationsMap = Record<string, ExplanationEntry>;

// ---------------------------------------------------------------------------
// PYQ — one global map, loaded once
// ---------------------------------------------------------------------------

let pyqCache: ExplanationsMap | null = null;
let pyqPromise: Promise<ExplanationsMap> | null = null;

function loadPyq(): Promise<ExplanationsMap> {
  if (!pyqPromise) {
    pyqPromise = fetch('/explanations.json')
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load explanations');
        return r.json() as Promise<ExplanationsMap>;
      })
      .then((data) => {
        pyqCache = data;
        return data;
      });
  }
  return pyqPromise;
}

// ---------------------------------------------------------------------------
// Practice — sharded per subject by split_practice_explanations.py, so
// revealing an answer fetches only that subject's explanations ({id: text}).
// ---------------------------------------------------------------------------

const practiceCache: Record<string, Record<string, string>> = {};
const practicePromises: Record<string, Promise<Record<string, string>>> = {};

function loadPractice(subject: string): Promise<Record<string, string>> {
  const slug = subjectSlug(subject);
  if (!practicePromises[slug]) {
    practicePromises[slug] = fetch(`/practice_expl_${slug}.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load explanations for ${subject}`);
        return r.json() as Promise<Record<string, string>>;
      })
      .then((data) => {
        practiceCache[slug] = data;
        return data;
      })
      .catch(() => ({}));
  }
  return practicePromises[slug];
}

/**
 * Look up a question's explanation, fetching whichever source file it lives in.
 * Takes the whole question rather than just the id because practice
 * explanations are sharded by subject.
 */
export async function getExplanation(question: Question): Promise<ExplanationEntry | null> {
  const isPractice = question.source === 'practice' || question.id.startsWith('medmcqa-');

  if (isPractice) {
    const slug = subjectSlug(question.subject);
    const map = practiceCache[slug] ?? (await loadPractice(question.subject));
    const text = map[question.id];
    return text ? { text } : null;
  }

  const map = pyqCache ?? (await loadPyq());
  return map[question.id] ?? null;
}
