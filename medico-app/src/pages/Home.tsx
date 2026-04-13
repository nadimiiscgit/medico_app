import { Link } from 'react-router-dom';
import { useQuestions } from '../hooks/useQuestions';
import { useProgress } from '../hooks/useProgress';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Progress } from '../components/ui/Progress';
import { Button } from '../components/ui/Button';
import { percentage, formatDuration } from '../lib/utils';
import {
  ClockIcon,
  BookmarkIcon,
  BarChart3Icon,
  TrophyIcon,
  FlameIcon,
  BookOpenIcon,
  ZapIcon,
  ArrowRightIcon,
  CheckCircleIcon,
} from 'lucide-react';

export function Home() {
  const { questions, loading } = useQuestions();
  const { progress } = useProgress();

  const totalPct = percentage(progress.totalCorrect, progress.totalAttempted);
  const recentSessions = progress.sessions.slice(0, 3);
  const topSubjects = Object.entries(progress.subjectStats)
    .sort((a, b) => b[1].attempted - a[1].attempted)
    .slice(0, 4);

  const years = [...new Set(questions.map((q) => q.year))].sort((a, b) => b - a);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-10 h-10 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">Loading 10,368 questions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome banner */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-6 text-white">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-1">NEET PG Question Bank</h1>
            <p className="text-blue-100 text-sm">
              {questions.length.toLocaleString()} questions · 2012–2024 · Practice smart
            </p>
            {progress.streak > 0 && (
              <div className="flex items-center gap-1 mt-2 text-sm">
                <FlameIcon className="w-4 h-4 text-orange-300" />
                <span className="text-blue-100">{progress.streak}-day streak</span>
              </div>
            )}
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold">{totalPct}%</div>
            <div className="text-blue-200 text-xs">Overall accuracy</div>
          </div>
        </div>
        <div className="mt-4 flex gap-3">
          <Link to="/practice">
            <Button className="bg-white text-blue-700 hover:bg-blue-50 font-semibold">
              <ZapIcon className="w-4 h-4" />
              Start Practice Test
            </Button>
          </Link>
          <Link to="/quiz">
            <Button className="bg-blue-500 text-white hover:bg-blue-400 border border-blue-400">
              <BookOpenIcon className="w-4 h-4" />
              Quick Quiz
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-blue-100 dark:bg-blue-900/40 rounded-lg flex items-center justify-center">
                <CheckCircleIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <div className="text-xl font-bold text-gray-900 dark:text-gray-100">{progress.totalAttempted.toLocaleString()}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Attempted</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-green-100 dark:bg-green-900/40 rounded-lg flex items-center justify-center">
                <TrophyIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <div className="text-xl font-bold text-gray-900 dark:text-gray-100">{totalPct}%</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Accuracy</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-orange-100 dark:bg-orange-900/40 rounded-lg flex items-center justify-center">
                <FlameIcon className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <div className="text-xl font-bold text-gray-900 dark:text-gray-100">{progress.streak}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Day streak</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-purple-100 dark:bg-purple-900/40 rounded-lg flex items-center justify-center">
                <BookmarkIcon className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <div className="text-xl font-bold text-gray-900 dark:text-gray-100">{progress.bookmarks.length}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Bookmarks</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Quick start by year */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <ClockIcon className="w-4 h-4 text-blue-600" />
              Practice by Year
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {years.slice(0, 6).map((year) => {
                const yearQs = questions.filter((q) => q.year === year);
                const stats = progress.yearStats[year];
                const pct = stats ? percentage(stats.correct, stats.attempted) : 0;
                return (
                  <Link
                    key={year}
                    to={`/quiz?year=${year}`}
                    className="flex items-center justify-between p-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <span className="text-sm font-semibold text-gray-900 dark:text-gray-100 w-10">
                        {year}
                      </span>
                      <div className="flex-1">
                        <Progress value={stats ? pct : 0} className="h-1.5" />
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-3">
                      <span className="text-xs text-gray-400 dark:text-gray-500">{yearQs.length} Qs</span>
                      {stats && (
                        <span className="text-xs font-medium text-gray-600 dark:text-gray-400">{pct}%</span>
                      )}
                      <ArrowRightIcon className="w-3.5 h-3.5 text-gray-400 group-hover:text-blue-600 transition-colors" />
                    </div>
                  </Link>
                );
              })}
              <Link to="/browse" className="block text-center text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 pt-1 font-medium">
                View all years →
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Recent sessions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3Icon className="w-4 h-4 text-blue-600" />
              Recent Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            {recentSessions.length === 0 ? (
              <div className="text-center py-8">
                <BookOpenIcon className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
                <p className="text-sm text-gray-500 dark:text-gray-400">No sessions yet</p>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Start a quiz or practice test</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentSessions.map((session) => {
                  const correct = Object.values(session.answers).filter((a) => a.isCorrect).length;
                  const total = Object.keys(session.answers).length;
                  const pct = percentage(correct, total);
                  return (
                    <div key={session.id} className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                        pct >= 80 ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400' :
                        pct >= 60 ? 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400' :
                        'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400'
                      }`}>
                        {pct}%
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                          {session.mode === 'practice' ? 'Practice Test' : 'Quiz Mode'}
                          {session.subject && ` · ${session.subject}`}
                          {session.year && ` · ${session.year}`}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {correct}/{total} correct · {new Date(session.startedAt).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  );
                })}
                <Link to="/analytics" className="block text-center text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 pt-1 font-medium">
                  View all analytics →
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Subject performance */}
      {topSubjects.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Subject Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 gap-4">
              {topSubjects.map(([subject, stats]) => {
                const pct = percentage(stats.correct, stats.attempted);
                return (
                  <div key={subject} className="space-y-1.5">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-700 dark:text-gray-300 font-medium truncate">{subject}</span>
                      <span className="text-gray-500 dark:text-gray-400 ml-2 flex-shrink-0">
                        {stats.correct}/{stats.attempted} · {pct}%
                      </span>
                    </div>
                    <Progress
                      value={pct}
                      color={pct >= 80 ? 'green' : pct >= 60 ? 'yellow' : 'red'}
                    />
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
