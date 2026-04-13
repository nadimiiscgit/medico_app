import { useState, useEffect, useRef, useCallback } from 'react';
import { useQuestions } from '../hooks/useQuestions';
import { useProgress } from '../hooks/useProgress';
import { QuestionCard } from '../components/QuestionCard';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Progress } from '../components/ui/Progress';
import type { Question, OptionKey, TestSession } from '../types';
import { shuffleArray, formatTime, percentage } from '../lib/utils';
import { cn } from '../lib/utils';
import {
  PlayIcon,
  ClockIcon,
  FlagIcon,
  RotateCcwIcon,
  CheckCircleIcon,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { createSession } from '../store/userProgress';

type TestStep = 'setup' | 'test' | 'review' | 'results';

const PRESET_CONFIGS = [
  { label: 'Full NEET PG', questions: 200, time: 210 * 60, description: '200 Qs · 3h 30m' },
  { label: 'Half Exam', questions: 100, time: 105 * 60, description: '100 Qs · 1h 45m' },
  { label: 'Quick Mock', questions: 50, time: 50 * 60, description: '50 Qs · 50m' },
  { label: 'Subject Drill', questions: 30, time: 30 * 60, description: '30 Qs · 30m' },
];

export function PracticeTest() {
  const { questions, loading, years, subjects } = useQuestions();
  const { progress, bookmark, isBookmarked, recordQuestionAnswer, completeSession } = useProgress();

  const [step, setStep] = useState<TestStep>('setup');
  const [testQuestions, setTestQuestions] = useState<Question[]>([]);
  const [selectedOptions, setSelectedOptions] = useState<Record<string, OptionKey | null>>({});
  const [markedForReview, setMarkedForReview] = useState<Set<string>>(new Set());
  const [currentIdx, setCurrentIdx] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [session, setSession] = useState<TestSession | null>(null);

  // Setup
  const [selectedConfig, setSelectedConfig] = useState(0);
  const [customYear, setCustomYear] = useState(0);
  const [customSubject, setCustomSubject] = useState('All');

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startTest = useCallback(() => {
    const config = PRESET_CONFIGS[selectedConfig];
    let pool = questions;
    if (customYear > 0) pool = pool.filter((q) => q.year === customYear);
    if (customSubject !== 'All') pool = pool.filter((q) => q.subject === customSubject);

    const shuffled = shuffleArray(pool).slice(0, config.questions);
    if (shuffled.length === 0) return;

    setTestQuestions(shuffled);
    setSelectedOptions({});
    setMarkedForReview(new Set());
    setCurrentIdx(0);
    setTimeLeft(config.time);
    setIsSubmitted(false);

    const newSession = createSession('practice', shuffled.map((q) => q.id), {
      timeLimit: config.time,
      subject: customSubject !== 'All' ? customSubject : undefined,
      year: customYear > 0 ? customYear : undefined,
    });
    setSession(newSession);
    setStep('test');
  }, [questions, selectedConfig, customYear, customSubject]);

  // Timer
  useEffect(() => {
    if (step !== 'test' || isSubmitted) return;

    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(timerRef.current!);
          submitTest();
          return 0;
        }
        return t - 1;
      });
    }, 1000);

    return () => clearInterval(timerRef.current!);
  }, [step, isSubmitted]);

  const submitTest = useCallback(() => {
    setIsSubmitted(true);
    clearInterval(timerRef.current!);

    testQuestions.forEach((q) => {
      const sel = selectedOptions[q.id];
      if (sel) {
        const isCorrect = sel === q.correctAnswer;
        recordQuestionAnswer(q.id, q.subject, q.year, isCorrect, 0);
      }
    });

    if (session) {
      const completedSession: TestSession = {
        ...session,
        completedAt: new Date().toISOString(),
        answers: Object.fromEntries(
          testQuestions
            .filter((q) => selectedOptions[q.id])
            .map((q) => [
              q.id,
              {
                questionId: q.id,
                selectedOption: selectedOptions[q.id] ?? null,
                isCorrect: selectedOptions[q.id] === q.correctAnswer,
                timeTaken: 0,
                answeredAt: new Date().toISOString(),
              },
            ])
        ),
      };
      completeSession(completedSession);
    }

    setStep('results');
  }, [testQuestions, selectedOptions, session, recordQuestionAnswer, completeSession]);

  const handleSelectOption = (questionId: string, opt: OptionKey) => {
    if (isSubmitted) return;
    setSelectedOptions((prev) => ({ ...prev, [questionId]: opt }));
  };

  const toggleMarkForReview = (questionId: string) => {
    setMarkedForReview((prev) => {
      const next = new Set(prev);
      if (next.has(questionId)) next.delete(questionId);
      else next.add(questionId);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (step === 'setup') {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Practice Test</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Simulate the actual NEET PG exam experience</p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {PRESET_CONFIGS.map((config, idx) => {
            const isSelected = selectedConfig === idx;
            return (
              <button
                key={config.label}
                onClick={() => setSelectedConfig(idx)}
                className={cn(
                  'p-4 rounded-xl border-2 text-left transition-all relative',
                  isSelected
                    ? 'border-blue-600 bg-blue-600 text-white shadow-md'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30'
                )}
              >
                {isSelected && (
                  <CheckCircleIcon className="absolute top-2.5 right-2.5 w-4 h-4 text-white/90" />
                )}
                <div className={cn('font-semibold text-sm', isSelected ? 'text-white' : 'text-gray-900 dark:text-gray-100')}>
                  {config.label}
                </div>
                <div className={cn('text-xs mt-0.5', isSelected ? 'text-blue-100' : 'text-gray-500 dark:text-gray-400')}>
                  {config.description}
                </div>
              </button>
            );
          })}
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Customize (Optional)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Year</label>
                <select
                  value={customYear}
                  onChange={(e) => setCustomYear(parseInt(e.target.value))}
                  className="w-full border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                >
                  <option value={0}>All Years</option>
                  {years.map((y) => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Subject</label>
                <select
                  value={customSubject}
                  onChange={(e) => setCustomSubject(e.target.value)}
                  className="w-full border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                >
                  <option value="All">All Subjects</option>
                  {subjects.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>

            <Button className="w-full" size="lg" onClick={startTest}>
              <PlayIcon className="w-4 h-4" />
              Start Practice Test
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (step === 'results') {
    const attempted = Object.values(selectedOptions).filter(Boolean).length;
    const correct = testQuestions.filter(
      (q) => selectedOptions[q.id] === q.correctAnswer
    ).length;
    const pct = percentage(correct, testQuestions.length);
    const unattempted = testQuestions.length - attempted;

    return (
      <div className="max-w-xl mx-auto space-y-5">
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Test Results</h1>

        <Card>
          <CardContent className="text-center py-8">
            <div className={`text-5xl font-bold mb-1 ${pct >= 70 ? 'text-green-600' : pct >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
              {pct}%
            </div>
            <p className="text-gray-500 dark:text-gray-400 text-sm">Score</p>
            <div className="grid grid-cols-3 gap-4 mt-6 text-center">
              <div>
                <div className="text-2xl font-bold text-green-600">{correct}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Correct</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-600">{attempted - correct}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Wrong</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-400 dark:text-gray-500">{unattempted}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Unattempted</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-3">
          <Button variant="outline" onClick={() => setStep('review')} className="flex-1">
            Review Answers
          </Button>
          <Button onClick={startTest} className="flex-1">
            <RotateCcwIcon className="w-4 h-4" />
            New Test
          </Button>
        </div>
        <Link to="/" className="block text-center text-sm text-blue-600 dark:text-blue-400">
          Return to Home
        </Link>
      </div>
    );
  }

  // Review mode
  if (step === 'review') {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Answer Review</h1>
          <Button variant="outline" size="sm" onClick={() => setStep('results')}>
            Back to Results
          </Button>
        </div>
        {testQuestions.map((q, idx) => (
          <QuestionCard
            key={q.id}
            question={q}
            questionIndex={idx}
            totalQuestions={testQuestions.length}
            isBookmarked={isBookmarked(q.id)}
            onBookmark={() => bookmark(q.id)}
            selectedOption={selectedOptions[q.id] ?? null}
            showAnswer
            isAnswered
            mode="review"
          />
        ))}
      </div>
    );
  }

  // Test in progress
  const currentQ = testQuestions[currentIdx];
  const answeredCount = Object.values(selectedOptions).filter(Boolean).length;
  const timerPct = (timeLeft / (PRESET_CONFIGS[selectedConfig]?.time ?? 1)) * 100;
  const isLowTime = timeLeft < 300;

  return (
    <div className="space-y-4">
      {/* Top bar */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 sticky top-0 z-10">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Q {currentIdx + 1}/{testQuestions.length}
            </span>
            <span className="text-xs text-gray-400 dark:text-gray-500">
              · {answeredCount} answered
            </span>
          </div>
          <div className={cn(
            'flex items-center gap-1.5 font-mono font-bold text-sm px-3 py-1 rounded-full',
            isLowTime
              ? 'bg-red-100 dark:bg-red-950/50 text-red-700 dark:text-red-400'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
          )}>
            <ClockIcon className="w-3.5 h-3.5" />
            {formatTime(timeLeft)}
          </div>
        </div>
        <Progress
          value={timerPct}
          color={isLowTime ? 'red' : 'blue'}
          className="h-1.5"
        />
      </div>

      {/* Question */}
      {currentQ && (
        <div>
          <QuestionCard
            question={currentQ}
            questionIndex={currentIdx}
            totalQuestions={testQuestions.length}
            isBookmarked={isBookmarked(currentQ.id)}
            onBookmark={() => bookmark(currentQ.id)}
            selectedOption={selectedOptions[currentQ.id] ?? null}
            onSelectOption={(opt) => handleSelectOption(currentQ.id, opt)}
            mode="browse"
          />
          <div className="mt-2 flex justify-end">
            <button
              onClick={() => toggleMarkForReview(currentQ.id)}
              className={cn(
                'flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full font-medium transition-colors',
                markedForReview.has(currentQ.id)
                  ? 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 hover:text-yellow-600 dark:hover:text-yellow-400'
              )}
            >
              <FlagIcon className="w-3.5 h-3.5" />
              {markedForReview.has(currentQ.id) ? 'Marked for Review' : 'Mark for Review'}
            </button>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex gap-2">
        <Button
          variant="outline"
          onClick={() => setCurrentIdx((i) => Math.max(0, i - 1))}
          disabled={currentIdx === 0}
        >
          ←
        </Button>

        <div className="flex-1 overflow-x-auto">
          <div className="flex gap-1 min-w-max">
            {testQuestions.map((q, idx) => {
              const answered = !!selectedOptions[q.id];
              const isReview = markedForReview.has(q.id);
              return (
                <button
                  key={q.id}
                  onClick={() => setCurrentIdx(idx)}
                  className={cn(
                    'w-7 h-7 rounded text-xs font-semibold flex-shrink-0 transition-colors',
                    idx === currentIdx && 'ring-2 ring-blue-500',
                    isReview && 'bg-yellow-400 text-yellow-900',
                    answered && !isReview && 'bg-green-500 text-white',
                    !answered && !isReview && 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                  )}
                >
                  {idx + 1}
                </button>
              );
            })}
          </div>
        </div>

        <Button
          variant="outline"
          onClick={() => setCurrentIdx((i) => Math.min(testQuestions.length - 1, i + 1))}
          disabled={currentIdx === testQuestions.length - 1}
        >
          →
        </Button>
      </div>

      {/* Submit */}
      <div className="flex justify-end">
        <Button
          variant="destructive"
          onClick={() => {
            if (window.confirm(`Submit test? You've answered ${answeredCount}/${testQuestions.length} questions.`)) {
              submitTest();
            }
          }}
        >
          Submit Test
        </Button>
      </div>
    </div>
  );
}
