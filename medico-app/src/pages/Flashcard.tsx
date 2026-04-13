import { useState, useCallback } from 'react';
import { useQuestions } from '../hooks/useQuestions';
import { useProgress } from '../hooks/useProgress';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Progress } from '../components/ui/Progress';
import { shuffleArray } from '../lib/utils';
import type { Question } from '../types';
import { cn } from '../lib/utils';
import {
  PlayIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckCircleIcon,
  XCircleIcon,
  RotateCcwIcon,
  HomeIcon,
  EyeIcon,
} from 'lucide-react';
import { Link } from 'react-router-dom';

type FlashStep = 'setup' | 'flash' | 'results';

interface FlashResult {
  questionId: string;
  knew: boolean;
}

export function Flashcard() {
  const { questions, loading, years, subjects } = useQuestions();
  const { progress } = useProgress();

  const [step, setStep] = useState<FlashStep>('setup');
  const [cards, setCards] = useState<Question[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [results, setResults] = useState<FlashResult[]>([]);

  // Setup options
  const [selectedSubject, setSelectedSubject] = useState('All');
  const [selectedYear, setSelectedYear] = useState(0);
  const [cardCount, setCardCount] = useState(20);
  const [onlyWrong, setOnlyWrong] = useState(false);

  const wrongCount = progress.incorrectQuestionIds?.length ?? 0;

  const startSession = useCallback(() => {
    let pool = questions;
    if (onlyWrong && (progress.incorrectQuestionIds?.length ?? 0) > 0) {
      const wrongIds = new Set(progress.incorrectQuestionIds);
      pool = pool.filter((q) => wrongIds.has(q.id));
    }
    if (selectedSubject !== 'All') pool = pool.filter((q) => q.subject === selectedSubject);
    if (selectedYear > 0) pool = pool.filter((q) => q.year === selectedYear);

    const shuffled = shuffleArray(pool).slice(0, cardCount);
    if (shuffled.length === 0) return;

    setCards(shuffled);
    setCurrentIdx(0);
    setRevealed(false);
    setResults([]);
    setStep('flash');
  }, [questions, selectedSubject, selectedYear, cardCount, onlyWrong, progress.incorrectQuestionIds]);

  const handleKnew = (knew: boolean) => {
    const q = cards[currentIdx];
    const newResults = [...results, { questionId: q.id, knew }];
    setResults(newResults);

    if (currentIdx < cards.length - 1) {
      setCurrentIdx((i) => i + 1);
      setRevealed(false);
    } else {
      setStep('results');
    }
  };

  const knewCount = results.filter((r) => r.knew).length;

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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Flashcard Mode</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Quick revision — read the question, then reveal the answer</p>
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
                {subjects.map((s) => <option key={s} value={s}>{s}</option>)}
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
                {years.map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>

            {/* Card count */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Number of Cards: <span className="text-blue-600">{cardCount}</span>
              </label>
              <input
                type="range" min={5} max={100} step={5} value={cardCount}
                onChange={(e) => setCardCount(parseInt(e.target.value))}
                className="w-full accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-400 dark:text-gray-500 mt-1">
                <span>5</span><span>50</span><span>100</span>
              </div>
            </div>

            {/* Wrong only */}
            {wrongCount > 0 && (
              <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-orange-400 has-[:checked]:border-orange-500 has-[:checked]:bg-orange-50 dark:has-[:checked]:bg-orange-950/30">
                <input
                  type="checkbox"
                  checked={onlyWrong}
                  onChange={(e) => setOnlyWrong(e.target.checked)}
                  className="w-4 h-4 accent-orange-600"
                />
                <div>
                  <p className="text-sm font-semibold text-gray-800 dark:text-gray-200">Wrong answers only</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{wrongCount} questions</p>
                </div>
              </label>
            )}

            <Button className="w-full" size="lg" onClick={startSession}>
              <PlayIcon className="w-4 h-4" />
              Start Flashcards
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (step === 'results') {
    const pct = Math.round((knewCount / cards.length) * 100);
    return (
      <div className="max-w-xl mx-auto space-y-5">
        <Card>
          <CardContent className="text-center py-8">
            <div className={`text-5xl font-bold mb-2 ${pct >= 80 ? 'text-green-600' : pct >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
              {pct}%
            </div>
            <p className="text-gray-500 dark:text-gray-400">Knew it</p>
            <div className="grid grid-cols-2 gap-4 mt-6">
              <div>
                <div className="text-2xl font-bold text-green-600">{knewCount}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Knew it</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-600">{cards.length - knewCount}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Need to review</div>
              </div>
            </div>
            <div className="mt-6 flex gap-3 justify-center">
              <Button variant="outline" onClick={startSession}>
                <RotateCcwIcon className="w-4 h-4" />
                Again
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
      </div>
    );
  }

  // Flashcard in progress
  const currentCard = cards[currentIdx];
  const progressPct = ((currentIdx) / cards.length) * 100;

  return (
    <div className="max-w-xl mx-auto space-y-4">
      {/* Progress */}
      <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
        <span className="font-medium">{currentIdx + 1} / {cards.length}</span>
        <span>{knewCount} knew · {currentIdx - knewCount} missed</span>
      </div>
      <Progress value={progressPct} />

      {/* Card */}
      <div className="min-h-[320px] flex flex-col">
        <Card className="flex-1">
          <CardContent className="py-6 flex flex-col gap-4 h-full">
            {/* Meta */}
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="secondary" className="text-xs">{currentCard.subject}</Badge>
              <span className="text-xs text-gray-400 dark:text-gray-500">
                NEET PG {currentCard.year}{currentCard.shift > 1 ? ` S${currentCard.shift}` : ''}
              </span>
              {currentCard.topic && (
                <span className="text-xs text-gray-400 dark:text-gray-500">· {currentCard.topic}</span>
              )}
            </div>

            {/* Question */}
            <p className="text-gray-900 dark:text-gray-100 font-medium leading-relaxed text-[15px] flex-1">
              {currentCard.question}
            </p>

            {/* Answer (revealed) */}
            {revealed ? (
              <div className="space-y-3">
                <div className="space-y-2">
                  {(['A', 'B', 'C', 'D'] as const).map((key) => {
                    const isCorrect = key === currentCard.correctAnswer;
                    return (
                      <div
                        key={key}
                        className={cn(
                          'flex items-center gap-3 px-4 py-2.5 rounded-lg border-2',
                          isCorrect
                            ? 'border-green-500 bg-green-50 dark:bg-green-950/50'
                            : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 opacity-60'
                        )}
                      >
                        <span className={cn(
                          'flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold',
                          isCorrect ? 'bg-green-600 text-white' : 'bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300'
                        )}>{key}</span>
                        <span className="text-sm text-gray-800 dark:text-gray-200">{currentCard.options[key]}</span>
                        {isCorrect && <CheckCircleIcon className="w-4 h-4 text-green-600 ml-auto flex-shrink-0" />}
                      </div>
                    );
                  })}
                </div>
                {currentCard.explanation && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 px-1 leading-relaxed">
                    {currentCard.explanation.slice(0, 200)}{currentCard.explanation.length > 200 ? '…' : ''}
                  </p>
                )}
              </div>
            ) : (
              <Button
                className="w-full"
                variant="outline"
                onClick={() => setRevealed(true)}
              >
                <EyeIcon className="w-4 h-4" />
                Reveal Answer
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Know it / Didn't know buttons */}
        {revealed && (
          <div className="grid grid-cols-2 gap-3 mt-3">
            <button
              onClick={() => handleKnew(false)}
              className="flex items-center justify-center gap-2 py-3 rounded-xl border-2 border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400 font-semibold text-sm hover:bg-red-100 dark:hover:bg-red-950/60 transition-colors"
            >
              <XCircleIcon className="w-5 h-5" />
              Didn't Know
            </button>
            <button
              onClick={() => handleKnew(true)}
              className="flex items-center justify-center gap-2 py-3 rounded-xl border-2 border-green-300 dark:border-green-700 bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-400 font-semibold text-sm hover:bg-green-100 dark:hover:bg-green-950/60 transition-colors"
            >
              <CheckCircleIcon className="w-5 h-5" />
              Knew It
            </button>
          </div>
        )}

        {/* Skip (before reveal) */}
        {!revealed && (
          <div className="flex justify-between mt-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => { setCurrentIdx((i) => Math.max(0, i - 1)); setRevealed(false); }}
              disabled={currentIdx === 0}
            >
              <ChevronLeftIcon className="w-4 h-4" /> Prev
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleKnew(false)}
            >
              Skip <ChevronRightIcon className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
