/**
 * SM-2 Spaced Repetition Algorithm (same as Anki)
 *
 * grade: 0 = total blackout, 1 = wrong, 2 = wrong but familiar,
 *        3 = correct with difficulty, 4 = correct, 5 = perfect recall
 *
 * For flashcards: "Knew it" → grade 4, "Didn't know" → grade 1
 */

export interface SRCard {
  questionId: string;
  repetitions: number;  // how many consecutive correct reviews
  interval: number;     // days until next review
  easeFactor: number;   // >= 1.3, starts at 2.5
  dueDate: string;      // YYYY-MM-DD
  lastReviewed: string; // YYYY-MM-DD
}

const DEFAULT_EASE = 2.5;
const MIN_EASE = 1.3;

export function todayStr(): string {
  return new Date().toISOString().split('T')[0];
}

function addDays(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + Math.max(1, days));
  return d.toISOString().split('T')[0];
}

export function createSRCard(questionId: string): SRCard {
  return {
    questionId,
    repetitions: 0,
    interval: 1,
    easeFactor: DEFAULT_EASE,
    dueDate: todayStr(),
    lastReviewed: todayStr(),
  };
}

/**
 * Update a card after review.
 * @param card  existing SR data
 * @param knew  true = "Knew it" (grade 4), false = "Didn't know" (grade 1)
 */
export function reviewCard(card: SRCard, knew: boolean): SRCard {
  const grade = knew ? 4 : 1;

  let { repetitions, interval, easeFactor } = card;

  if (grade >= 3) {
    if (repetitions === 0) {
      interval = 1;
    } else if (repetitions === 1) {
      interval = 6;
    } else {
      interval = Math.round(interval * easeFactor);
    }
    repetitions += 1;
  } else {
    // Wrong — reset
    repetitions = 0;
    interval = 1;
  }

  easeFactor = easeFactor + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02));
  easeFactor = Math.max(MIN_EASE, easeFactor);

  return {
    ...card,
    repetitions,
    interval,
    easeFactor,
    dueDate: addDays(interval),
    lastReviewed: todayStr(),
  };
}

export function isDue(card: SRCard): boolean {
  return card.dueDate <= todayStr();
}

export function getDueCount(cards: Record<string, SRCard>): number {
  return Object.values(cards).filter(isDue).length;
}

export function getNewCount(allIds: string[], cards: Record<string, SRCard>): number {
  return allIds.filter((id) => !cards[id]).length;
}
