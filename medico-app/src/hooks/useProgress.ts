import { useState, useCallback } from 'react';
import type { UserProgress, TestSession } from '../types';
import {
  loadProgress,
  saveProgress,
  toggleBookmark,
  saveSession,
  updateStreak,
  recordAnswer,
} from '../store/userProgress';

export function useProgress() {
  const [progress, setProgress] = useState<UserProgress>(() => loadProgress());

  const update = useCallback((updater: (p: UserProgress) => UserProgress) => {
    setProgress((prev) => {
      const next = updater(prev);
      saveProgress(next);
      return next;
    });
  }, []);

  const bookmark = useCallback(
    (questionId: string) => {
      update((p) => toggleBookmark(p, questionId));
    },
    [update]
  );

  const completeSession = useCallback(
    (session: TestSession) => {
      update((p) => {
        let updated = updateStreak(p);
        // Record all answers
        for (const answer of Object.values(session.answers)) {
          // Find question details from session – caller must pass subject/year
          // We'll handle that at call site via session metadata
        }
        updated = saveSession(updated, session);
        return updated;
      });
    },
    [update]
  );

  const recordQuestionAnswer = useCallback(
    (questionId: string, subject: string, year: number, isCorrect: boolean, timeTaken: number) => {
      update((p) => {
        let updated = updateStreak(p);
        updated = recordAnswer(updated, questionId, subject, year, isCorrect, timeTaken);
        return updated;
      });
    },
    [update]
  );

  const resetProgress = useCallback(() => {
    update(() => {
      const fresh: UserProgress = {
        totalAttempted: 0,
        totalCorrect: 0,
        subjectStats: {},
        yearStats: {},
        streak: 0,
        totalStudyTime: 0,
        sessions: [],
        bookmarks: progress.bookmarks, // Keep bookmarks on reset
      };
      return fresh;
    });
  }, [update, progress.bookmarks]);

  return {
    progress,
    bookmark,
    completeSession,
    recordQuestionAnswer,
    resetProgress,
    isBookmarked: (id: string) => progress.bookmarks.includes(id),
  };
}
