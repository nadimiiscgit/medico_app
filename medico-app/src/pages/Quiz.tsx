import { useState, useCallback, useRef, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuestions, usePracticeQuestions } from '../hooks/useQuestions';
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
  InfoIcon,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { createSession } from '../store/userProgress';

type QuizStep = 'setup' | 'quiz' | 'results' | 'review';
type QuizSource = 'pyq' | 'practice' | 'both';

interface QuizAnswer {
  selectedOption: OptionKey | null;
}

export function Quiz() {
  const [searchParams] = useSearchParams();
  const { questions: pyqQuestions, loading: pyqLoading, years, subjects } = useQuestions();
  const { progress, bookmark, isBookmarked, recordQuestionAnswer, completeSession } = useProgress();

  const [step, setStep] = useState<QuizStep>('setup');
  const [quizQuestions, setQuizQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, QuizAnswer>>({});
  const [currentIdx, setCurrentIdx] = useState(0);
  const [session, setSession] = useState<TestSession | null>(null);
  const startTimeRef = useRef<number>(Date.now());

  // Setup options
  const [selectedSource, setSelectedSource] = useState<QuizSource>('pyq');
  const [selectedSubject, setSelectedSubject] = useState(searchParams.get('subject') ?? 'All');
  const [selectedYear, setSelectedYear] = useState(
    searchParams.get('year') ? parseInt(searchParams.get('year')!) : 0
  );
  const [questionCount, setQuestionCount] = useState(20);
  const [reviseWrong, setReviseWrong] = useState(searchParams.get('mode') === 'revise');

  // Lazy-load practice questions only when a specific subject is selected
  const practiceSubjectsToLoad = useMemo(() => {
    if (selectedSource === 'pyq') return [];
    if (selectedSubject === 'All') return [];
    return [selectedSubject];
  }, [selectedSource, selectedSubject]);

  const { questions: practiceQuestions, loading: practiceLoading } =
    usePracticeQuestions(practiceSubjectsToLoad);

  // Combined pool for quiz setup preview
  const allQuestions = useMemo(() => {
    if (selectedSource === 'pyq') return pyqQuestions;
    if (selectedSource === 'practice') return practiceQuestions;
    return [...pyqQuestions, ...practiceQuestions];
  }, [selectedSource, pyqQuestions, practiceQuestions]);

  // Whether the user needs to pick a subject before practice can load
  const needsSubjectForPractice =
    selectedSource !== 'pyq' && selectedSubject === 'All';

  // In revise mode we can only reliably access PYQ wrong answers (always loaded).
  // Practice wrong answers require subject selection (lazy-loaded), so we separate them.
  const pyqWrongIds = useMemo(
    () => (progress.incorrectQuestionIds ?? []).filter((id) => !id.startsWith('medmcqa-')),
    [progress.incorrectQuestionIds]
  );
  const practiceWrongCount = useMemo(
    () => (progress.incorrectQuestionIds ?? []).filter((id) => id.startsWith('medmcqa-')).length,
    [progress.incorrectQuestionIds]
  );

  const startQuiz = useCallback(() => {
    let pool = allQuestions;
    if (reviseWrong) {
      const incorrectIds = new Set(pyqWrongIds);
      pool = pool.filter((q) => incorrectIds.has(q.id));
    }
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
        source: selectedSource,
      }
    );
    setSession(newSession);
    setStep('quiz');
  }, [allQuestions, selectedSubject, selectedYear, questionCount, selectedSource, reviseWrong, pyqWrongIds]);

  const handleSelectOption = (opt: OptionKey) => {
    const q = quizQuestions[currentIdx];
    if (!q) return;
    setAnswers((prev) => ({
      ...prev,
      [q.id]: { selectedOption: opt },
    }));
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

    quizQuestions.forEach((q) => {
      const sel = answers[q.id]?.selectedOption;
      if (sel) {
        const isCorrect = sel === q.correctAnswer;
        const timeTaken = Math.round((Date.now() - startTimeRef.current) / 1000);
        const qSource = q.source ?? 'pyq';
        recordQuestionAnswer(q.id, q.subject, q.year, isCorrect, timeTaken, qSource);
      }
    });

    const completedSession: TestSession = {
      ...session,
      completedAt: new Date().toISOString(),
      answers: Object.fromEntries(
        quizQuestions
          .filter((q) => answers[q.id]?.selectedOption)
          .map((q) => [
            q.id,
            {
              questionId: q.id,
              selectedOption: answers[q.id].selectedOption,
              isCorrect: answers[q.id].selectedOption === q.correctAnswer,
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
  const answeredCount = Object.values(answers).filter((a) => a.selectedOption).length;
  const correctCount = quizQuestions.filter(
    (q) => answers[q.id]?.selectedOption === q.correctAnswer
  ).length;

  if (pyqLoading) {
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
            {/* Source toggle */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Question Bank</label>
              <div className="flex rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden text-sm font-medium">
                {(['pyq', 'practice', 'both'] as const).map((src) => (
                  <button
                    key={src}
                    onClick={() => setSelectedSource(src)}
                    className={`flex-1 py-2 px-3 transition-colors ${
                      selectedSource === src
                        ? 'bg-blue-600 text-white'
                        : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-750'
                    }`}
                  >
                    {src === 'pyq' ? 'PYQ' : src === 'practice' ? 'Practice' : 'Both'}
                  </button>
                ))}
              </div>
              {selectedSource === 'pyq' && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">
                  {pyqQuestions.length.toLocaleString()} NEET PG previous year questions (2012–2024)
                </p>
              )}
              {selectedSource === 'practice' && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">
                  117,003 practice questions from MedMCQA — select a subject below
                </p>
              )}
              {selectedSource === 'both' && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">
                  PYQ + practice questions mixed — select a subject to include practice
                </p>
              )}
            </div>

            {/* Hint when practice needs a subject */}
            {needsSubjectForPractice && (
              <div className="flex items-start gap-2.5 px-3 py-2.5 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-xs text-amber-800 dark:text-amber-300">
                <InfoIcon className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
                <span>Select a specific <strong>Subject</strong> to load practice questions. "All Subjects" would load too much data.</span>
              </div>
            )}

            {/* Practice loading indicator */}
            {practiceLoading && (
              <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
                <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                Loading practice questions…
              </div>
            )}

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

            {/* Year — only for PYQ */}
            {selectedSource !== 'practice' && (
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
            )}

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

            {/* Revise Wrong Answers */}
            {pyqWrongIds.length > 0 && (
              <div>
                <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border-2 transition-all border-gray-200 dark:border-gray-700 hover:border-orange-400 has-[:checked]:border-orange-500 has-[:checked]:bg-orange-50 dark:has-[:checked]:bg-orange-950/30">
                  <input
                    type="checkbox"
                    checked={reviseWrong}
                    onChange={(e) => setReviseWrong(e.target.checked)}
                    className="w-4 h-4 accent-orange-600"
                  />
                  <div>
                    <p className="text-sm font-semibold text-gray-800 dark:text-gray-200">Revise Wrong Answers</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Practice {pyqWrongIds.length} PYQ questions you got wrong
                      {practiceWrongCount > 0 && ` · ${practiceWrongCount} practice wrongs: select subject above`}
                    </p>
                  </div>
                </label>
              </div>
            )}

            <Button
              className="w-full"
              size="lg"
              onClick={startQuiz}
              disabled={!reviseWrong && needsSubjectForPractice && selectedSource === 'practice'}
            >
              <PlayIcon className="w-4 h-4" />
              {!reviseWrong && needsSubjectForPractice && selectedSource === 'practice'
                ? 'Select a subject first'
                : 'Start Quiz'}
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
            <div className="mt-6 flex gap-3 justify-center flex-wrap">
              <Button variant="outline" onClick={() => setStep('review')}>
                <ListIcon className="w-4 h-4" />
                Review Answers
              </Button>
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
            </div>
          </CardContent>
        </Card>

        {/* Results breakdown */}
        <div className="space-y-3">
          {quizQuestions.map((q, idx) => {
            const sel = answers[q.id]?.selectedOption;
            const isCorrect = sel === q.correctAnswer;
            const unattempted = !sel;
            return (
              <div
                key={q.id}
                className={`flex items-center gap-3 p-3 rounded-lg border ${
                  unattempted
                    ? 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'
                    : isCorrect
                    ? 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-900'
                    : 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900'
                }`}
              >
                <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold ${
                  unattempted ? 'bg-gray-400 text-white' : isCorrect ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
                }`}>
                  {idx + 1}
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 flex-1 truncate">{q.question}</p>
                <span className="text-xs font-medium flex-shrink-0 text-gray-600 dark:text-gray-400">
                  {sel ?? '—'} {unattempted ? '' : isCorrect ? '✓' : `✗ (${q.correctAnswer})`}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Review all answers after quiz
  if (step === 'review') {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Answer Review</h1>
          <Button variant="outline" size="sm" onClick={() => setStep('results')}>
            Back to Results
          </Button>
        </div>
        {quizQuestions.map((q, idx) => {
          const sel = answers[q.id]?.selectedOption ?? null;
          return (
            <QuestionCard
              key={q.id}
              question={q}
              questionIndex={idx}
              totalQuestions={quizQuestions.length}
              isBookmarked={isBookmarked(q.id)}
              onBookmark={() => bookmark(q)}
              selectedOption={sel}
              showAnswer
              isAnswered
              mode="review"
            />
          );
        })}
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
          onBookmark={() => bookmark(currentQ)}
          selectedOption={currentAnswer?.selectedOption ?? null}
          onSelectOption={handleSelectOption}
          showAnswer={false}
          isAnswered={false}
          mode="browse"
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
          disabled={!currentAnswer?.selectedOption}
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
