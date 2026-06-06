import { useState, useCallback, useMemo } from 'react';
import { useQuestions } from '../hooks/useQuestions';
import { useProgress } from '../hooks/useProgress';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Progress } from '../components/ui/Progress';
import { shuffleArray } from '../lib/utils';
import type { Question } from '../types';
import { cn } from '../lib/utils';
import { isDue, getDueCount, getNewCount } from '../lib/spacedRepetition';
import {
  PlayIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckCircleIcon,
  XCircleIcon,
  RotateCcwIcon,
  HomeIcon,
  EyeIcon,
  BrainIcon,
  StarIcon,
  CalendarClockIcon,
  SparklesIcon,
} from 'lucide-react';
import { Link } from 'react-router-dom';

type FlashStep = 'setup' | 'flash' | 'results';
type FlashMode = 'spaced' | 'classic';

interface FlashResult {
  questionId: string;
  knew: boolean;
}

export function Flashcard() {
  const { questions, loading, years, subjects } = useQuestions();
  const { progress, reviewSRCard } = useProgress();

  const [step, setStep] = useState<FlashStep>('setup');
  const [mode, setMode] = useState<FlashMode>('spaced');
  const [cards, setCards] = useState<Question[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [results, setResults] = useState<FlashResult[]>([]);

  // Classic mode setup options
  const [selectedSubject, setSelectedSubject] = useState('All');
  const [selectedYear, setSelectedYear] = useState(0);
  const [cardCount, setCardCount] = useState(20);

  const srCards = progress.srCards ?? {};

  // SR stats
  const dueCount = useMemo(() => getDueCount(srCards), [srCards]);
  const newCount = useMemo(
    () => getNewCount(questions.map((q) => q.id), srCards),
    [questions, srCards]
  );

  // Due cards sorted: overdue first, then new
  const dueQuestions = useMemo(() => {
    const dueIds = new Set(
      Object.values(srCards)
        .filter(isDue)
        .map((c) => c.questionId)
    );
    const newIds = questions
      .filter((q) => !srCards[q.id])
      .map((q) => q.id);

    const due = questions.filter((q) => dueIds.has(q.id));
    const newCards = questions.filter((q) => newIds.includes(q.id));

    return [...shuffleArray(due), ...shuffleArray(newCards)].slice(0, 50);
  }, [questions, srCards]);

  const startSession = useCallback(
    (sessionMode: FlashMode) => {
      let pool: Question[] = [];

      if (sessionMode === 'spaced') {
        pool = dueQuestions;
      } else {
        pool = questions;
        if (selectedSubject !== 'All') pool = pool.filter((q) => q.subject === selectedSubject);
        if (selectedYear > 0) pool = pool.filter((q) => q.year === selectedYear);
        pool = shuffleArray(pool).slice(0, cardCount);
      }

      if (pool.length === 0) return;

      setCards(pool);
      setCurrentIdx(0);
      setRevealed(false);
      setResults([]);
      setMode(sessionMode);
      setStep('flash');
    },
    [questions, dueQuestions, selectedSubject, selectedYear, cardCount]
  );

  const handleKnew = (knew: boolean) => {
    const q = cards[currentIdx];
    const newResults = [...results, { questionId: q.id, knew }];
    setResults(newResults);

    // Always update SR data regardless of mode
    reviewSRCard(q.id, knew);

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

  // ── Setup ──────────────────────────────────────────────────────────────────
  if (step === 'setup') {
    return (
      <div className="max-w-xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Flashcard Mode</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">
            Quick revision — read the question, then reveal the answer
          </p>
        </div>

        {/* ── Spaced Repetition Card ── */}
        <div
          className={cn(
            'rounded-2xl border-2 p-5 transition-all cursor-pointer',
            'border-violet-400 bg-gradient-to-br from-violet-50 to-indigo-50 dark:from-violet-950/40 dark:to-indigo-950/40 dark:border-violet-600'
          )}
          onClick={() => startSession('spaced')}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-violet-600 flex items-center justify-center flex-shrink-0">
                <BrainIcon className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                  Smart Review
                  <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-violet-200 dark:bg-violet-800 text-violet-800 dark:text-violet-200">
                    SM-2 Algorithm
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Reviews cards at the optimal time — just like Anki
                </p>
              </div>
            </div>
            <PlayIcon className="w-5 h-5 text-violet-600 dark:text-violet-400 flex-shrink-0 mt-1" />
          </div>

          <div className="grid grid-cols-3 gap-3 mt-4">
            <div className="text-center px-3 py-2 rounded-xl bg-white/70 dark:bg-gray-900/50">
              <div className="text-xl font-bold text-red-600">{dueCount}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center justify-center gap-1 mt-0.5">
                <CalendarClockIcon className="w-3 h-3" /> Due today
              </div>
            </div>
            <div className="text-center px-3 py-2 rounded-xl bg-white/70 dark:bg-gray-900/50">
              <div className="text-xl font-bold text-blue-600">{Math.min(newCount, 999)}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center justify-center gap-1 mt-0.5">
                <SparklesIcon className="w-3 h-3" /> New
              </div>
            </div>
            <div className="text-center px-3 py-2 rounded-xl bg-white/70 dark:bg-gray-900/50">
              <div className="text-xl font-bold text-green-600">
                {Object.values(srCards).filter((c) => !isDue(c)).length}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center justify-center gap-1 mt-0.5">
                <StarIcon className="w-3 h-3" /> Learned
              </div>
            </div>
          </div>

          {dueCount + Math.min(newCount, 50) === 0 && (
            <p className="text-center text-sm text-green-600 dark:text-green-400 font-medium mt-3">
              🎉 All caught up! Come back tomorrow.
            </p>
          )}
        </div>

        <div className="relative flex items-center gap-3">
          <div className="flex-1 border-t border-gray-200 dark:border-gray-700" />
          <span className="text-xs text-gray-400 dark:text-gray-500 font-medium">OR</span>
          <div className="flex-1 border-t border-gray-200 dark:border-gray-700" />
        </div>

        {/* ── Classic Mode ── */}
        <Card>
          <CardContent className="space-y-5">
            <div className="flex items-center gap-2">
              <RotateCcwIcon className="w-4 h-4 text-gray-500" />
              <span className="font-semibold text-gray-800 dark:text-gray-200 text-sm">Classic Mode</span>
              <span className="text-xs text-gray-400 dark:text-gray-500">Custom selection</span>
            </div>

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

            <Button className="w-full" size="lg" onClick={() => startSession('classic')}>
              <PlayIcon className="w-4 h-4" />
              Start Classic Flashcards
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── Results ────────────────────────────────────────────────────────────────
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

            {mode === 'spaced' && (
              <div className="mt-3 px-4 py-2 bg-violet-50 dark:bg-violet-950/30 rounded-xl inline-block">
                <p className="text-xs text-violet-700 dark:text-violet-400 font-medium">
                  🧠 Cards scheduled for optimal review — next due dates updated
                </p>
              </div>
            )}

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
            <div className="mt-6 flex gap-3 justify-center flex-wrap">
              <Button variant="outline" onClick={() => startSession(mode)}>
                <RotateCcwIcon className="w-4 h-4" />
                Again
              </Button>
              <Button variant="outline" onClick={() => setStep('setup')}>
                Change Mode
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

  // ── Flash in progress ──────────────────────────────────────────────────────
  const currentCard = cards[currentIdx];
  const progressPct = (currentIdx / cards.length) * 100;
  const srData = srCards[currentCard?.id];

  return (
    <div className="max-w-xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
        <div className="flex items-center gap-2">
          {mode === 'spaced' && (
            <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300 font-medium">
              <BrainIcon className="w-3 h-3" /> Smart Review
            </span>
          )}
          <span className="font-medium">{currentIdx + 1} / {cards.length}</span>
        </div>
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
              {/* SR info for this card */}
              {mode === 'spaced' && srData && (
                <span className="ml-auto text-xs text-violet-500 dark:text-violet-400">
                  interval: {srData.interval}d · ease: {srData.easeFactor.toFixed(1)}
                </span>
              )}
              {mode === 'spaced' && !srData && (
                <span className="ml-auto text-xs text-blue-500 dark:text-blue-400">
                  ✨ New card
                </span>
              )}
            </div>

            {/* Question */}
            <p className="text-gray-900 dark:text-gray-100 font-medium leading-relaxed text-[15px] flex-1">
              {currentCard.question}
            </p>

            {/* Options — always visible; highlighted only after reveal */}
            <div className="space-y-2">
              {(['A', 'B', 'C', 'D'] as const).map((key) => {
                const isCorrect = key === currentCard.correctAnswer;
                return (
                  <div
                    key={key}
                    className={cn(
                      'flex items-center gap-3 px-4 py-2.5 rounded-lg border-2 transition-all duration-300',
                      revealed && isCorrect
                        ? 'border-green-500 bg-green-50 dark:bg-green-950/50'
                        : revealed && !isCorrect
                        ? 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 opacity-40'
                        : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50'
                    )}
                  >
                    <span className={cn(
                      'flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-colors duration-300',
                      revealed && isCorrect
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300'
                    )}>{key}</span>
                    <span className="text-sm text-gray-800 dark:text-gray-200">{currentCard.options[key]}</span>
                    {revealed && isCorrect && <CheckCircleIcon className="w-4 h-4 text-green-600 ml-auto flex-shrink-0" />}
                  </div>
                );
              })}
            </div>

            {/* Explanation after reveal */}
            {revealed && currentCard.explanation && (
              <p className="text-xs text-gray-500 dark:text-gray-400 px-1 leading-relaxed">
                {currentCard.explanation.slice(0, 200)}{currentCard.explanation.length > 200 ? '…' : ''}
              </p>
            )}

            {/* Reveal button */}
            {!revealed && (
              <Button className="w-full" variant="outline" onClick={() => setRevealed(true)}>
                <EyeIcon className="w-4 h-4" />
                Reveal Answer
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Know it / Didn't know */}
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
