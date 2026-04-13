import { useState } from 'react';
import { useProgress } from '../hooks/useProgress';
import { useQuestions } from '../hooks/useQuestions';
import { useTheme } from '../hooks/useTheme';
import type { Theme } from '../hooks/useTheme';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { percentage } from '../lib/utils';
import { AlertTriangleIcon, DownloadIcon, Trash2Icon, SunIcon, MoonIcon, MonitorIcon, TargetIcon } from 'lucide-react';
import { cn } from '../lib/utils';

const THEME_OPTIONS: { value: Theme; label: string; icon: React.ElementType }[] = [
  { value: 'light', label: 'Light', icon: SunIcon },
  { value: 'dark', label: 'Dark', icon: MoonIcon },
  { value: 'system', label: 'System', icon: MonitorIcon },
];

export function Settings() {
  const { progress, resetProgress, setDailyGoal } = useProgress();
  const { questions } = useQuestions();
  const { theme, setTheme } = useTheme();
  const [confirmReset, setConfirmReset] = useState(false);
  const [goalInput, setGoalInput] = useState(String(progress.dailyGoal ?? 20));

  const exportData = () => {
    const data = {
      exportedAt: new Date().toISOString(),
      totalAttempted: progress.totalAttempted,
      totalCorrect: progress.totalCorrect,
      accuracy: percentage(progress.totalCorrect, progress.totalAttempted),
      streak: progress.streak,
      subjectStats: progress.subjectStats,
      yearStats: progress.yearStats,
      bookmarksCount: progress.bookmarks.length,
      sessionsCount: progress.sessions.length,
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `neetpg-progress-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportWrongAnswers = () => {
    const incorrectIds = new Set(progress.incorrectQuestionIds ?? []);
    const wrongQuestions = questions.filter((q) => incorrectIds.has(q.id));
    const rows = [
      ['ID', 'Year', 'Subject', 'Topic', 'Question', 'A', 'B', 'C', 'D', 'Correct Answer'],
      ...wrongQuestions.map((q) => [
        q.id, q.year, q.subject, q.topic,
        `"${q.question.replace(/"/g, '""')}"`,
        `"${q.options.A}"`, `"${q.options.B}"`, `"${q.options.C}"`, `"${q.options.D}"`,
        q.correctAnswer,
      ]),
    ];
    const csv = rows.map((r) => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `neetpg-wrong-answers-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleReset = () => {
    resetProgress();
    setConfirmReset(false);
  };

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>

      {/* Theme */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Appearance</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">Choose your preferred color theme.</p>
          <div className="flex gap-2">
            {THEME_OPTIONS.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                onClick={() => setTheme(value)}
                className={cn(
                  'flex-1 flex flex-col items-center gap-1.5 py-3 px-2 rounded-lg border-2 text-sm font-medium transition-all',
                  theme === value
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300'
                    : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600'
                )}
              >
                <Icon className="w-5 h-5" />
                {label}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Progress Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Your Progress Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between py-1.5 border-b border-gray-100 dark:border-gray-800">
            <span className="text-gray-600 dark:text-gray-400">Total Attempted</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">{progress.totalAttempted.toLocaleString()}</span>
          </div>
          <div className="flex justify-between py-1.5 border-b border-gray-100 dark:border-gray-800">
            <span className="text-gray-600 dark:text-gray-400">Correct</span>
            <span className="font-medium text-green-600">{progress.totalCorrect.toLocaleString()}</span>
          </div>
          <div className="flex justify-between py-1.5 border-b border-gray-100 dark:border-gray-800">
            <span className="text-gray-600 dark:text-gray-400">Accuracy</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">{percentage(progress.totalCorrect, progress.totalAttempted)}%</span>
          </div>
          <div className="flex justify-between py-1.5 border-b border-gray-100 dark:border-gray-800">
            <span className="text-gray-600 dark:text-gray-400">Bookmarks</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">{progress.bookmarks.length}</span>
          </div>
          <div className="flex justify-between py-1.5">
            <span className="text-gray-600 dark:text-gray-400">Sessions Completed</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">{progress.sessions.length}</span>
          </div>
        </CardContent>
      </Card>

      {/* Daily Goal */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <TargetIcon className="w-4 h-4 text-blue-600" />
            Daily Goal
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
            Set a daily target for how many questions to attempt.
          </p>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min={1}
              max={500}
              value={goalInput}
              onChange={(e) => setGoalInput(e.target.value)}
              className="w-24 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            />
            <span className="text-sm text-gray-500 dark:text-gray-400">questions / day</span>
            <Button
              size="sm"
              onClick={() => {
                const val = parseInt(goalInput);
                if (val > 0) setDailyGoal(val);
              }}
            >
              Save
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Export */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Export Data</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Export your performance data or download a list of questions you got wrong.
          </p>
          <div className="flex gap-3 flex-wrap">
            <Button variant="outline" onClick={exportData}>
              <DownloadIcon className="w-4 h-4" />
              Export Progress Report
            </Button>
            {(progress.incorrectQuestionIds?.length ?? 0) > 0 && (
              <Button variant="outline" onClick={exportWrongAnswers}>
                <DownloadIcon className="w-4 h-4" />
                Export Wrong Answers ({progress.incorrectQuestionIds.length})
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* About */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">About</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          <p><strong className="text-gray-900 dark:text-gray-100">NEET PG Question Bank</strong></p>
          <p>10,368 questions from NEET PG papers (2012–2024)</p>
          <p>Includes detailed explanations for 2012–2020 papers</p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
            Note: 2021 paper not included (image-only PDF). 2024 papers are recall-based (partial).
          </p>
        </CardContent>
      </Card>

      {/* Reset */}
      <Card className="border-red-200 dark:border-red-900">
        <CardHeader>
          <CardTitle className="text-base text-red-700 dark:text-red-400 flex items-center gap-2">
            <AlertTriangleIcon className="w-4 h-4" />
            Danger Zone
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Reset all progress data. Your bookmarks will be preserved. This cannot be undone.
          </p>
          {!confirmReset ? (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setConfirmReset(true)}
            >
              <Trash2Icon className="w-4 h-4" />
              Reset Progress
            </Button>
          ) : (
            <div className="flex gap-3">
              <Button variant="destructive" size="sm" onClick={handleReset}>
                Yes, Reset Everything
              </Button>
              <Button variant="outline" size="sm" onClick={() => setConfirmReset(false)}>
                Cancel
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
