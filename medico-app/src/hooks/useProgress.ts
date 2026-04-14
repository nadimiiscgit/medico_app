import { useState, useCallback } from 'react';
import type { UserProgress, TestSession, Question } from '../types';
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
    (question: Question) => {
      update((p) => toggleBookmark(p, question));
    },
    [update]
  );

  const completeSession = useCallback(
    (session: TestSession) => {
      update((p) => {
        let updated = updateStreak(p);
        updated = saveSession(updated, session);
        return updated;
      });
    },
    [update]
  );

  const recordQuestionAnswer = useCallback(
    (
      questionId: string,
      subject: string,
      year: number,
      isCorrect: boolean,
      timeTaken: number,
      source: 'pyq' | 'practice' = 'pyq'
    ) => {
      update((p) => {
        let updated = updateStreak(p);
        updated = recordAnswer(updated, questionId, subject, year, isCorrect, timeTaken, source);
        return updated;
      });
    },
    [update]
  );

  const resetProgress = useCallback(() => {
    update((p) => {
      const fresh: UserProgress = {
        totalAttempted: 0,
        totalCorrect: 0,
        subjectStats: {},
        practiceSubjectStats: {},
        yearStats: {},
        streak: 0,
        totalStudyTime: 0,
        sessions: [],
        bookmarks: p.bookmarks,
        practiceBookmarkSubjects: p.practiceBookmarkSubjects ?? {},
        incorrectQuestionIds: [],
        dailyGoal: p.dailyGoal,
        dailyStats: { date: '', attempted: 0 },
      };
      return fresh;
    });
  }, [update]);

  const setDailyGoal = useCallback(
    (goal: number) => {
      update((p) => ({ ...p, dailyGoal: goal }));
    },
    [update]
  );

  return {
    progress,
    bookmark,
    completeSession,
    recordQuestionAnswer,
    resetProgress,
    setDailyGoal,
    isBookmarked: (id: string) => progress.bookmarks.includes(id),
  };
}
