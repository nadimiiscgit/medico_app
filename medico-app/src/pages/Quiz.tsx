import { useState, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuestions } from '../hooks/useQuestions';
import { useProgress } from '../hooks/useProgress';
import { QuestionCard } from '../components/QuestionCard';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Progress } from '../components/ui/Progress';
import type { Question, OptionKey, TestSession } from '../types';
import { shuffleArray, generateId, percentage } from '../lib/utils';
import {
  PlayIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckCircleIcon,
  RotateCcwIcon,
  HomeIcon,
  ListIcon,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { createSession } from '../store/userProgress';

type QuizStep = 'setup' | 'quiz' | 'results';

interface QuizAnswer {
  selectedOption: OptionKey | null;
  isCorrect: boolean;
  revealed: boolean;
}

export function Quiz() {
  const [searchParams] = useSearchParams();
  const { questions, loading, years, subjects } = useQuestions();
  const { progress, bookmark, isBookmarked, recordQuestionAnswer, completeSession } = useProgress();

  const [step, setStep] = useState<QuizStep>('setup');
  const [quizQuestions, setQuizQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, QuizAnswer>>({});
  const [currentIdx, setCurrentIdx] = useState(0);
  const [session, setSession] = useState<TestSession | null>(null);
  const startTimeRef = useRef<number>(Date.now());

  // Setup options
  const [selectedSubject, setSelectedSubject] = useState(searchParams.get('subject') ?? 'All');
  const [selectedYear, setSelectedYear] = useState(
    searchParams.get('year') ? parseInt(searchParams.get('year')!) : 0
  );
  const [questionCount, setQuestionCount] = useState(20);

  const startQuiz = useCallback(() => {
    let pool = questions;
    if (selectedSubject !== 'All') pool = pool.filter((q) => q.subject === selectedSubject);
    if (selectedYear > 0) pool = pool.filter((q) => q.year === selectedYear);

    const shuffled = shuffleArray(pool).slice(0, questionCount);
    if (shuffled.length === 0) return;

    setQuizQuestions(shuffled);
    setAnswers({});
    setCurrentIdx(0);
    startTimeRef.current = Date.now();

    const newSession = createSession(
      'quiz',
      shuffled.map((q) => q.id),
      {
        subject: selectedSubject !== 'All' ? selectedSubject : undefined,
        year: selectedYear > 0 ? selectedYear : undefined,
      }
    );
    setSession(newSession);
    setStep('quiz');
  }, [questions, selectedSubject, selectedYear, questionCount]);

  const handleSelectOption = (opt: OptionKey) => {
    const q = quizQuestions[currentIdx];
    if (!q || answers[q.id]?.revealed) return;
    setAnswers((prev) => ({
      ...prev,
      [q.id]: { selectedOption: opt, isCorrect: false, revealed: false },
    }));
  };

  const handleSubmit = () => {
    const q = quizQuestions[currentIdx];
    if (!q || !answers[q.id]?.selectedOption) return;

    const isCorrect = answers[q.id].selectedOption === q.correctAnswer;
    const timeTaken = Math.round((Date.now() - startTimeRef.current) / 1000);

    setAnswers((prev) => ({
      ...prev,
      [q.id]: { ...prev[q.id], isCorrect, revealed: true },
    }));

    recordQuestionAnswer(q.id, q.subject, q.year, isCorrect, timeTaken);
    startTimeRef.current = Date.now();
  };

  const handleNext = () => {
    if (currentIdx < quizQuestions.length - 1) {
      setCurrentIdx((i) => i + 1);
    } else {
      finishQuiz();
    }
  };

  const handlePrev = () => {
    setCurrentIdx((i) => Math.max(0, i - 1));
  };

  const finishQuiz = () => {
    if (!session) return;
    const completedSession: TestSession = {
      ...session,
      completedAt: new Date().toISOString(),
      answers: Object.fromEntries(
        Object.entries(answers).map(([id, a]) => [
          id,
          {
            questionId: id,
            selectedOption: a.selectedOption,
            isCorrect: a.isCorrect,
            timeTaken: 0,
            answeredAt: new Date().toISOString(),
          },
        ])
      ),
    };
    completeSession(completedSession);
    setStep('results');
  };

  const currentQ = quizQuestions[currentIdx];
  const currentAnswer = currentQ ? answers[currentQ.id] : null;
  const answeredCount = Object.values(answers).filter((a) => a.revealed).length;
  const correctCount = Object.values(answers).filter((a) => a.isCorrect).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (step === 'setup') {
    return (
      <div className="max-w-xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Quiz Mode</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Practice questions at your own pace</p>
        </div>

        <Card>
          <CardContent className="space-y-5">
            {/* Subject */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Subject</label>
              <select
                value={selectedSubject}
                onChange={(e) => setSelectedSubject(e.target.value)}
                className="w-full border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value="All">All Subjects</option>
                {subjects.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {/* Year */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Year</label>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                className="w-full border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              >
                <option value={0}>All Years</option>
                {years.map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>

            {/* Question count */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Number of Questions: <span className="text-blue-600">{questionCount}</span>
              </label>
              <input
                type="range"
                min={5}
                max={100}
                step={5}
                value={questionCount}
                onChange={(e) => setQuestionCount(parseInt(e.target.value))}
                className="w-full accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-400 dark:text-gray-500 mt-1">
                <span>5</span>
                <span>50</span>
                <span>100</span>
              </div>
            </div>

            <Button className="w-full" size="lg" onClick={startQuiz}>
              <PlayIcon className="w-4 h-4" />
              Start Quiz
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (step === 'results') {
    const pct = percentage(correctCount, quizQuestions.length);
    return (
      <div className="max-w-xl mx-auto space-y-5">
        <Card>
          <CardContent className="text-center py-8">
            <div className={`text-5xl font-bold mb-2 ${pct >= 80 ? 'text-green-600' : pct >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
              {pct}%
            </div>
            <p className="text-gray-600 dark:text-gray-400 text-lg font-medium">
              {correctCount} / {quizQuestions.length} correct
            </p>
            <div className="mt-6 flex gap-3 justify-center">
              <Button variant="outline" onClick={startQuiz}>
                <RotateCcwIcon className="w-4 h-4" />
                Try Again
              </Button>
              <Link to="/">
                <Button variant="secondary">
                  <HomeIcon className="w-4 h-4" />
                  Home
                </Button>
              </Link>
              <Link to="/browse">
                <Button>
                  <ListIcon className="w-4 h-4" />
                  Browse
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Results breakdown */}
        <div className="space-y-3">
          {quizQuestions.map((q, idx) => {
            const ans = answers[q.id];
            return (
              <div
                key={q.id}
                className={`flex items-center gap-3 p-3 rounded-lg border ${
                  ans?.isCorrect
                    ? 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-900'
                    : 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900'
                }`}
              >
                <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold ${
                  ans?.isCorrect ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
                }`}>
                  {idx + 1}
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 flex-1 truncate">{q.question}</p>
                <span className="text-xs font-medium flex-shrink-0 text-gray-600 dark:text-gray-400">
                  {ans?.selectedOption ?? '—'} {ans?.isCorrect ? '✓' : `✗ (${q.correctAnswer})`}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Quiz in progress
  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4">
        <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
          <span className="font-medium">Question {currentIdx + 1} of {quizQuestions.length}</span>
          <span>{answeredCount} answered · {correctCount} correct</span>
        </div>
        <Progress value={((currentIdx + 1) / quizQuestions.length) * 100} />
      </div>

      {currentQ && (
        <QuestionCard
          question={currentQ}
          questionIndex={currentIdx}
          totalQuestions={quizQuestions.length}
          isBookmarked={isBookmarked(currentQ.id)}
          onBookmark={() => bookmark(currentQ.id)}
          selectedOption={currentAnswer?.selectedOption ?? null}
          onSelectOption={handleSelectOption}
          onSubmit={handleSubmit}
          showAnswer={currentAnswer?.revealed ?? false}
          isAnswered={currentAnswer?.revealed ?? false}
          mode="quiz"
        />
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between gap-3">
        <Button variant="outline" onClick={handlePrev} disabled={currentIdx === 0}>
          <ChevronLeftIcon className="w-4 h-4" />
          Previous
        </Button>

        <Button variant="ghost" onClick={finishQuiz} className="text-gray-500 dark:text-gray-400 text-sm">
          Finish Quiz
        </Button>

        <Button
          onClick={handleNext}
          disabled={!currentAnswer?.revealed && !currentAnswer?.selectedOption}
        >
          {currentIdx === quizQuestions.length - 1 ? (
            <>Finish <CheckCircleIcon className="w-4 h-4" /></>
          ) : (
            <>Next <ChevronRightIcon className="w-4 h-4" /></>
          )}
        </Button>
      </div>
    </div>
  );
}
