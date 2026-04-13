import { useState } from 'react';
import type { Question, OptionKey } from '../types';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { cn } from '../lib/utils';
import { BookmarkIcon, ChevronDownIcon, ChevronUpIcon, CheckCircleIcon, XCircleIcon } from 'lucide-react';

interface QuestionCardProps {
  question: Question;
  questionIndex?: number;
  totalQuestions?: number;
  isBookmarked?: boolean;
  onBookmark?: () => void;
  showAnswer?: boolean;
  selectedOption?: OptionKey | null;
  onSelectOption?: (opt: OptionKey) => void;
  onSubmit?: () => void;
  mode?: 'quiz' | 'review' | 'browse';
  isAnswered?: boolean;
}

const OPTION_KEYS: OptionKey[] = ['A', 'B', 'C', 'D'];

const SUBJECT_COLORS: Record<string, string> = {
  Anatomy: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
  Physiology: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  Biochemistry: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300',
  Pathology: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
  Pharmacology: 'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300',
  Microbiology: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  Medicine: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  Surgery: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
  'Obstetrics & Gynaecology': 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300',
  Paediatrics: 'bg-lime-100 text-lime-700 dark:bg-lime-900/40 dark:text-lime-300',
  Psychiatry: 'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300',
  Radiology: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300',
  Orthopaedics: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  ENT: 'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300',
  Ophthalmology: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300',
  Dermatology: 'bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900/40 dark:text-fuchsia-300',
  Anaesthesia: 'bg-slate-100 text-slate-700 dark:bg-slate-900/40 dark:text-slate-300',
  'Forensic Medicine': 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800/60 dark:text-zinc-300',
  'Community Medicine': 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  'General Medicine': 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
};

export function QuestionCard({
  question,
  questionIndex,
  totalQuestions,
  isBookmarked = false,
  onBookmark,
  showAnswer = false,
  selectedOption = null,
  onSelectOption,
  onSubmit,
  mode = 'browse',
  isAnswered = false,
}: QuestionCardProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const subjectColor = SUBJECT_COLORS[question.subject] ?? 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';

  const getOptionStyle = (key: OptionKey) => {
    if (!showAnswer && !isAnswered) {
      if (selectedOption === key) {
        return 'border-blue-500 bg-blue-50 dark:bg-blue-950/50 text-blue-900 dark:text-blue-200';
      }
      return 'border-gray-200 dark:border-gray-700 hover:border-blue-300 hover:bg-blue-50 dark:hover:bg-blue-950/30 cursor-pointer';
    }
    if (key === question.correctAnswer) {
      return 'border-green-500 bg-green-50 dark:bg-green-950/50 text-green-900 dark:text-green-200';
    }
    if (selectedOption === key && key !== question.correctAnswer) {
      return 'border-red-500 bg-red-50 dark:bg-red-950/50 text-red-900 dark:text-red-200';
    }
    return 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-gray-600 dark:text-gray-400';
  };

  const getOptionIcon = (key: OptionKey) => {
    if (!showAnswer && !isAnswered) return null;
    if (key === question.correctAnswer) {
      return <CheckCircleIcon className="w-4 h-4 text-green-600 flex-shrink-0" />;
    }
    if (selectedOption === key && key !== question.correctAnswer) {
      return <XCircleIcon className="w-4 h-4 text-red-600 flex-shrink-0" />;
    }
    return null;
  };

  const isRevealed = showAnswer || isAnswered;
  const userGotCorrect = selectedOption === question.correctAnswer;

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100 dark:border-gray-800 flex items-start justify-between gap-4">
        <div className="flex items-center gap-2 flex-wrap">
          {questionIndex !== undefined && totalQuestions !== undefined && (
            <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
              {questionIndex + 1} / {totalQuestions}
            </span>
          )}
          <span className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold', subjectColor)}>
            {question.subject}
          </span>
          <span className={cn(
            'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold',
            question.difficulty === 'Easy' && 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
            question.difficulty === 'Medium' && 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
            question.difficulty === 'Hard' && 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
          )}>
            {question.difficulty}
          </span>
          <span className="text-xs text-gray-400 dark:text-gray-500 font-medium">
            NEET PG {question.year}{question.shift > 1 ? ` Shift ${question.shift}` : ''}
          </span>
          {question.topic && (
            <span className="text-xs text-gray-400 dark:text-gray-500">· {question.topic}</span>
          )}
        </div>
        {onBookmark && (
          <button
            onClick={onBookmark}
            className="text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors flex-shrink-0"
            title={isBookmarked ? 'Remove bookmark' : 'Bookmark question'}
          >
            <BookmarkIcon
              className={cn('w-5 h-5', isBookmarked && 'fill-blue-500 text-blue-500')}
            />
          </button>
        )}
      </div>

      {/* Question */}
      <div className="px-5 py-4">
        <p className="text-gray-900 dark:text-gray-100 font-medium leading-relaxed text-[15px]">
          {question.question}
        </p>
      </div>

      {/* Options */}
      <div className="px-5 pb-4 space-y-2.5">
        {OPTION_KEYS.map((key) => {
          const optText = question.options[key];
          if (!optText) return null;
          return (
            <div
              key={key}
              onClick={() => !isRevealed && onSelectOption?.(key)}
              className={cn(
                'flex items-center gap-3 px-4 py-3 rounded-lg border-2 transition-all',
                getOptionStyle(key),
                !isRevealed && onSelectOption ? 'cursor-pointer' : 'cursor-default'
              )}
            >
              <span className={cn(
                'flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold',
                selectedOption === key && !isRevealed && 'bg-blue-600 text-white',
                key === question.correctAnswer && isRevealed && 'bg-green-600 text-white',
                selectedOption === key && key !== question.correctAnswer && isRevealed && 'bg-red-600 text-white',
                !((selectedOption === key && !isRevealed) || (key === question.correctAnswer && isRevealed) || (selectedOption === key && key !== question.correctAnswer && isRevealed)) && 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300',
              )}>
                {key}
              </span>
              <span className="flex-1 text-sm">{optText}</span>
              {getOptionIcon(key)}
            </div>
          );
        })}
      </div>

      {/* Result banner */}
      {isRevealed && selectedOption && (
        <div className={cn(
          'mx-5 mb-4 px-4 py-2.5 rounded-lg text-sm font-medium flex items-center gap-2',
          userGotCorrect
            ? 'bg-green-100 dark:bg-green-950/60 text-green-800 dark:text-green-300'
            : 'bg-red-100 dark:bg-red-950/60 text-red-800 dark:text-red-300'
        )}>
          {userGotCorrect ? (
            <><CheckCircleIcon className="w-4 h-4" /> Correct! Well done.</>
          ) : (
            <><XCircleIcon className="w-4 h-4" /> Incorrect. The correct answer is <strong>{question.correctAnswer}</strong>.</>
          )}
        </div>
      )}

      {/* Explanation */}
      {isRevealed && question.explanation && (
        <div className="mx-5 mb-4">
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 font-medium hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
          >
            {showExplanation ? <ChevronUpIcon className="w-4 h-4" /> : <ChevronDownIcon className="w-4 h-4" />}
            {showExplanation ? 'Hide' : 'Show'} Explanation
          </button>
          {showExplanation && (
            <div className="mt-2 px-4 py-3 bg-blue-50 dark:bg-blue-950/40 rounded-lg text-sm text-gray-700 dark:text-gray-300 leading-relaxed border border-blue-100 dark:border-blue-900">
              {question.explanation}
            </div>
          )}
        </div>
      )}

      {/* Submit button */}
      {mode === 'quiz' && !isRevealed && selectedOption && onSubmit && (
        <div className="px-5 pb-4">
          <Button onClick={onSubmit} className="w-full">
            Submit Answer
          </Button>
        </div>
      )}
    </div>
  );
}
