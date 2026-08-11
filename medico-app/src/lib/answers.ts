import type { OptionKey, Question } from '../types';

/**
 * Is this option acceptable as a correct answer?
 *
 * Twelve questions in the corpus are defective as printed — usually two options are
 * equally correct (Mucor and Rhizopus are both Mucorales; TSC1 hamartin and TSC2
 * tuberin both cause tuberous sclerosis; all four options of one pharyngeal-arch
 * question are arch derivatives). Marking a student wrong for choosing a genuinely
 * correct option teaches them a false distinction, so those questions carry a
 * `dataQuality.acceptableAnswers` list and every one of them counts.
 *
 * Questions without that field — the overwhelming majority — behave exactly as before.
 */
export function isAcceptableAnswer(question: Question, choice: OptionKey | null): boolean {
  if (!choice) return false;
  if (choice === question.correctAnswer) return true;
  return question.dataQuality?.acceptableAnswers?.includes(choice) ?? false;
}

/** Every option that counts as correct, for highlighting all of them at once. */
export function acceptableAnswers(question: Question): OptionKey[] {
  const extra = question.dataQuality?.acceptableAnswers ?? [];
  return Array.from(new Set<OptionKey>([question.correctAnswer, ...extra]));
}

/** True when more than one option is defensible, so the UI can say so. */
export function hasMultipleAnswers(question: Question): boolean {
  return acceptableAnswers(question).length > 1;
}
