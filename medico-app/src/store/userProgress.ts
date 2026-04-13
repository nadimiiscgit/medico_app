import type { UserProgress, TestSession } from '../types';
import { generateId } from '../lib/utils';

const STORAGE_KEY = 'neetpg_progress';

const DEFAULT_PROGRESS: UserProgress = {
  totalAttempted: 0,
  totalCorrect: 0,
  subjectStats: {},
  yearStats: {},
  streak: 0,
  lastStudied: undefined,
  totalStudyTime: 0,
  sessions: [],
  bookmarks: [],
};

export function loadProgress(): UserProgress {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_PROGRESS };
    return { ...DEFAULT_PROGRESS, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULT_PROGRESS };
  }
}

export function saveProgress(progress: UserProgress): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  } catch {
    // Storage quota exceeded or unavailable
  }
}

export function updateStreak(progress: UserProgress): UserProgress {
  const today = new Date().toDateString();
  const last = progress.lastStudied ? new Date(progress.lastStudied).toDateString() : null;
  const yesterday = new Date(Date.now() - 86400000).toDateString();

  let streak = progress.streak;
  if (last === today) {
    // Already studied today
  } else if (last === yesterday) {
    streak += 1;
  } else {
    streak = 1;
  }

  return { ...progress, streak, lastStudied: new Date().toISOString() };
}

export function recordAnswer(
  progress: UserProgress,
  questionId: string,
  subject: string,
  year: number,
  isCorrect: boolean,
  timeTaken: number
): UserProgress {
  const subjectStats = { ...progress.subjectStats };
  const yearStats = { ...progress.yearStats };

  subjectStats[subject] = {
    attempted: (subjectStats[subject]?.attempted ?? 0) + 1,
    correct: (subjectStats[subject]?.correct ?? 0) + (isCorrect ? 1 : 0),
  };

  yearStats[year] = {
    attempted: (yearStats[year]?.attempted ?? 0) + 1,
    correct: (yearStats[year]?.correct ?? 0) + (isCorrect ? 1 : 0),
  };

  return {
    ...progress,
    totalAttempted: progress.totalAttempted + 1,
    totalCorrect: progress.totalCorrect + (isCorrect ? 1 : 0),
    totalStudyTime: progress.totalStudyTime + timeTaken,
    subjectStats,
    yearStats,
  };
}

export function saveSession(progress: UserProgress, session: TestSession): UserProgress {
  const sessions = [session, ...progress.sessions].slice(0, 50);
  return { ...progress, sessions };
}

export function createSession(
  mode: 'practice' | 'quiz',
  questionIds: string[],
  options?: { subject?: string; year?: number; timeLimit?: number }
): TestSession {
  return {
    id: generateId(),
    mode,
    startedAt: new Date().toISOString(),
    questionIds,
    answers: {},
    ...options,
  };
}

export function toggleBookmark(progress: UserProgress, questionId: string): UserProgress {
  const bookmarks = progress.bookmarks.includes(questionId)
    ? progress.bookmarks.filter((id) => id !== questionId)
    : [...progress.bookmarks, questionId];
  return { ...progress, bookmarks };
}

export function isBookmarked(progress: UserProgress, questionId: string): boolean {
  return progress.bookmarks.includes(questionId);
}
