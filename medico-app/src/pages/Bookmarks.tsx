import { useState, useMemo } from 'react';
import { useQuestions, usePracticeQuestions } from '../hooks/useQuestions';
import { useProgress } from '../hooks/useProgress';
import { useNotes } from '../hooks/useNotes';
import { QuestionCard } from '../components/QuestionCard';
import type { OptionKey } from '../types';
import { BookmarkIcon } from 'lucide-react';

export function Bookmarks() {
  const { questions, loading } = useQuestions();
  const { progress, bookmark, isBookmarked } = useProgress();
  const { notes, saveNote } = useNotes();
  const [selectedOptions, setSelectedOptions] = useState<Record<string, OptionKey | null>>({});
  const [revealedQuestions, setRevealedQuestions] = useState<Set<string>>(new Set());

  // Determine which practice subjects we need to load (from stored subject map)
  const practiceSubjectsToLoad = useMemo(() => {
    const subjectMap = progress.practiceBookmarkSubjects ?? {};
    const subjects = new Set<string>();
    progress.bookmarks.forEach((id) => {
      if (id.startsWith('medmcqa-') && subjectMap[id]) {
        subjects.add(subjectMap[id]);
      }
    });
    return [...subjects];
  }, [progress.bookmarks, progress.practiceBookmarkSubjects]);

  const { questions: practiceQuestions, loading: practiceLoading } =
    usePracticeQuestions(practiceSubjectsToLoad);

  // Combine PYQ + practice bookmarked questions
  const bookmarkedQuestions = useMemo(() => {
    const ids = new Set(progress.bookmarks);
    const pyqBookmarked = questions.filter((q) => ids.has(q.id));
    const practiceBookmarked = practiceQuestions.filter((q) => ids.has(q.id));
    return [...pyqBookmarked, ...practiceBookmarked];
  }, [questions, practiceQuestions, progress.bookmarks]);

  const isAnyLoading = loading || practiceLoading;

  if (isAnyLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (progress.bookmarks.length === 0) {
    return (
      <div className="text-center py-20">
        <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
          <BookmarkIcon className="w-8 h-8 text-gray-400 dark:text-gray-500" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No Bookmarks Yet</h2>
        <p className="text-gray-500 dark:text-gray-400 text-sm max-w-sm mx-auto">
          Bookmark questions while browsing or practicing to save them here for later review.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Bookmarks</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{bookmarkedQuestions.length} saved questions</p>
        </div>
      </div>

      <div className="space-y-4">
        {bookmarkedQuestions.map((q, idx) => (
          <QuestionCard
            key={q.id}
            question={q}
            questionIndex={idx}
            totalQuestions={bookmarkedQuestions.length}
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
    </div>
  );
}
