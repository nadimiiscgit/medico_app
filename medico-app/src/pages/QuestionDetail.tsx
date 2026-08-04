import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeftIcon, SearchXIcon } from 'lucide-react';
import { findQuestionById } from '../lib/questionLookup';
import { useProgress } from '../hooks/useProgress';
import { useNotes } from '../hooks/useNotes';
import { QuestionCard } from '../components/QuestionCard';
import type { OptionKey, Question } from '../types';

export function QuestionDetail() {
  const { id } = useParams<{ id: string }>();
  const { bookmark, isBookmarked } = useProgress();
  const { notes, saveNote } = useNotes();

  const [question, setQuestion] = useState<Question | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedOption, setSelectedOption] = useState<OptionKey | null>(null);
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setQuestion(null);
    setSelectedOption(null);
    setRevealed(false);

    if (!id) {
      setLoading(false);
      return;
    }

    findQuestionById(id).then((found) => {
      if (!cancelled) {
        setQuestion(found);
        setLoading(false);
      }
    });

    return () => { cancelled = true; };
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!question) {
    return (
      <div className="text-center py-20">
        <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
          <SearchXIcon className="w-8 h-8 text-gray-400 dark:text-gray-500" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Question Not Found</h2>
        <p className="text-gray-500 dark:text-gray-400 text-sm max-w-sm mx-auto mb-4">
          No question exists with the ID "{id}". Double-check the ID and try again.
        </p>
        <Link to="/" className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:underline">
          Back to Home
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Link
        to="/"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
      >
        <ArrowLeftIcon className="w-4 h-4" />
        Back
      </Link>

      <QuestionCard
        question={question}
        questionIndex={0}
        totalQuestions={1}
        isBookmarked={isBookmarked(question.id)}
        onBookmark={() => bookmark(question)}
        selectedOption={selectedOption}
        onSelectOption={setSelectedOption}
        onSubmit={() => setRevealed(true)}
        showAnswer={revealed}
        isAnswered={revealed}
        mode={selectedOption && !revealed ? 'quiz' : 'browse'}
        note={notes[question.id] ?? ''}
        onSaveNote={(n) => saveNote(question.id, n)}
      />
    </div>
  );
}
