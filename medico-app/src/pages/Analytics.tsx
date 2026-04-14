import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useProgress } from '../hooks/useProgress';
import { useQuestions } from '../hooks/useQuestions';
import { Progress as ProgressBar } from '../components/ui/Progress';
import { useTheme } from '../hooks/useTheme';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Progress } from '../components/ui/Progress';
import { percentage, getScoreColor } from '../lib/utils';
import {
  BarChart3Icon,
  FlameIcon,
  ZapIcon,
  BookOpenIcon,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { CalendarIcon, ClockIcon, TrendingUpIcon } from 'lucide-react';

export function Analytics() {
  const { progress } = useProgress();
  const { questions } = useQuestions();
  const { isDark } = useTheme();

  const totalPct = percentage(progress.totalCorrect, progress.totalAttempted);

  const subjectData = Object.entries(progress.subjectStats)
    .map(([subject, stats]) => ({
      subject: subject.length > 12 ? subject.slice(0, 12) + '…' : subject,
      fullSubject: subject,
      attempted: stats.attempted,
      correct: stats.correct,
      accuracy: percentage(stats.correct, stats.attempted),
    }))
    .sort((a, b) => b.attempted - a.attempted)
    .slice(0, 10);

  const yearData = Object.entries(progress.yearStats)
    .map(([year, stats]) => ({
      year,
      attempted: stats.attempted,
      correct: stats.correct,
      accuracy: percentage(stats.correct, stats.attempted),
    }))
    .sort((a, b) => parseInt(a.year) - parseInt(b.year));

  const sessions = progress.sessions;

  // Avg time per question
  const avgTimePerQ = progress.totalAttempted > 0
    ? Math.round(progress.totalStudyTime / progress.totalAttempted)
    : 0;

  // Performance trend — last 20 completed sessions with answers
  const trendData = useMemo(() => {
    return sessions
      .filter((s) => Object.keys(s.answers).length > 0)
      .slice(0, 20)
      .reverse()
      .map((s, i) => {
        const total = Object.keys(s.answers).length;
        const correct = Object.values(s.answers).filter((a) => a.isCorrect).length;
        return {
          index: i + 1,
          accuracy: percentage(correct, total),
          date: new Date(s.startedAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }),
        };
      });
  }, [sessions]);

  // 90-day study planner — allocate days by weakness × question volume
  const studyPlan = useMemo(() => {
    const totalBySubject: Record<string, number> = {};
    questions.forEach((q) => {
      totalBySubject[q.subject] = (totalBySubject[q.subject] ?? 0) + 1;
    });

    const subjectList = Object.entries(totalBySubject).map(([subject, total]) => {
      const stats = progress.subjectStats[subject];
      const accuracy = stats ? percentage(stats.correct, stats.attempted) : 0;
      const attempted = stats?.attempted ?? 0;
      // Weight: (100 - accuracy) × sqrt(total) — weak subjects with many questions get more days
      const coverageGap = 1 - Math.min(attempted / total, 1);
      const weakness = (100 - accuracy) / 100;
      const weight = (weakness * 0.6 + coverageGap * 0.4) * Math.sqrt(total);
      return { subject, total, attempted, accuracy, weight };
    });

    const totalWeight = subjectList.reduce((a, s) => a + s.weight, 0);
    const TOTAL_DAYS = 90;

    return subjectList
      .map((s) => ({
        ...s,
        days: Math.max(1, Math.round((s.weight / totalWeight) * TOTAL_DAYS)),
      }))
      .sort((a, b) => b.days - a.days);
  }, [questions, progress.subjectStats]);

  // Build 12-week activity heatmap
  const heatmap = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dayOfWeek = today.getDay(); // 0=Sun
    // Start from the Sunday of 11 weeks ago
    const startDate = new Date(today);
    startDate.setDate(today.getDate() - dayOfWeek - 11 * 7);

    const countByDate: Record<string, number> = {};
    sessions.forEach((s) => {
      const d = new Date(s.startedAt);
      const key = d.toDateString();
      countByDate[key] = (countByDate[key] ?? 0) + 1;
    });

    const weeks: { date: Date; count: number }[][] = [];
    let week: { date: Date; count: number }[] = [];
    const d = new Date(startDate);
    while (d <= today) {
      week.push({ date: new Date(d), count: countByDate[d.toDateString()] ?? 0 });
      if (week.length === 7) {
        weeks.push(week);
        week = [];
      }
      d.setDate(d.getDate() + 1);
    }
    if (week.length > 0) {
      while (week.length < 7) week.push({ date: new Date(d), count: -1 }); // padding
      weeks.push(week);
    }
    return weeks;
  }, [sessions]);

  // Weakest subjects (lowest accuracy, at least 3 attempted)
  const weakestSubjects = useMemo(() => {
    return Object.entries(progress.subjectStats)
      .filter(([, s]) => s.attempted >= 3)
      .map(([subject, s]) => ({ subject, accuracy: percentage(s.correct, s.attempted), attempted: s.attempted }))
      .sort((a, b) => a.accuracy - b.accuracy)
      .slice(0, 3);
  }, [progress.subjectStats]);

  // Subject coverage: attempted vs total available
  const subjectCoverage = useMemo(() => {
    const totalBySubject: Record<string, number> = {};
    questions.forEach((q) => {
      totalBySubject[q.subject] = (totalBySubject[q.subject] ?? 0) + 1;
    });
    return Object.entries(totalBySubject)
      .map(([subject, total]) => ({
        subject,
        total,
        attempted: progress.subjectStats[subject]?.attempted ?? 0,
        coveragePct: Math.round(((progress.subjectStats[subject]?.attempted ?? 0) / total) * 100),
      }))
      .sort((a, b) => b.attempted - a.attempted);
  }, [questions, progress.subjectStats]);

  // Chart colors for dark mode
  const axisColor = isDark ? '#9ca3af' : '#6b7280';
  const gridColor = isDark ? '#374151' : '#f0f0f0';
  const tooltipBg = isDark ? '#1f2937' : '#ffffff';
  const tooltipBorder = isDark ? '#374151' : '#e5e7eb';
  const tooltipText = isDark ? '#f3f4f6' : '#111827';

  if (progress.totalAttempted === 0) {
    return (
      <div className="text-center py-20">
        <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
          <BarChart3Icon className="w-8 h-8 text-gray-400 dark:text-gray-500" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No Data Yet</h2>
        <p className="text-gray-500 dark:text-gray-400 text-sm">Complete a quiz or practice test to see analytics.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Performance Analytics</h1>

      {/* Overview stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card>
          <CardContent className="py-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Total Attempted</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{progress.totalAttempted.toLocaleString()}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Overall Accuracy</div>
            <div className={`text-2xl font-bold ${getScoreColor(totalPct)}`}>{totalPct}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Study Streak</div>
            <div className="text-2xl font-bold text-orange-500 flex items-center gap-1">
              <FlameIcon className="w-5 h-5" />
              {progress.streak}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Sessions Done</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{sessions.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Avg Time / Q</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-1">
              <ClockIcon className="w-4 h-4 text-gray-400" />
              {avgTimePerQ}s
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Activity heatmap */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <FlameIcon className="w-4 h-4 text-orange-500" />
            Study Activity (Last 12 Weeks)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <div className="flex gap-1 min-w-max">
              {heatmap.map((week, wi) => (
                <div key={wi} className="flex flex-col gap-1">
                  {week.map((day, di) => {
                    if (day.count < 0) return <div key={di} className="w-3 h-3" />;
                    const isFuture = day.date > new Date();
                    return (
                      <div
                        key={di}
                        title={`${day.date.toDateString()}: ${day.count} session${day.count !== 1 ? 's' : ''}`}
                        className={`w-3 h-3 rounded-sm ${
                          isFuture ? 'bg-transparent' :
                          day.count === 0 ? 'bg-gray-100 dark:bg-gray-800' :
                          day.count === 1 ? 'bg-blue-200 dark:bg-blue-900' :
                          day.count === 2 ? 'bg-blue-400 dark:bg-blue-700' :
                          'bg-blue-600 dark:bg-blue-500'
                        }`}
                      />
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2 mt-3 text-xs text-gray-400 dark:text-gray-500">
            <span>Less</span>
            <div className="w-3 h-3 rounded-sm bg-gray-100 dark:bg-gray-800" />
            <div className="w-3 h-3 rounded-sm bg-blue-200 dark:bg-blue-900" />
            <div className="w-3 h-3 rounded-sm bg-blue-400 dark:bg-blue-700" />
            <div className="w-3 h-3 rounded-sm bg-blue-600 dark:bg-blue-500" />
            <span>More</span>
          </div>
        </CardContent>
      </Card>

      {/* Performance trend */}
      {trendData.length >= 3 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUpIcon className="w-4 h-4 text-blue-500" />
              Performance Trend (Last {trendData.length} Sessions)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={trendData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: axisColor }} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 11, fill: axisColor }} domain={[0, 100]} unit="%" />
                <Tooltip
                  contentStyle={{ backgroundColor: tooltipBg, border: `1px solid ${tooltipBorder}`, borderRadius: '8px', color: tooltipText }}
                  formatter={(v) => [`${v}%`, 'Accuracy']}
                />
                <Line type="monotone" dataKey="accuracy" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Focus areas */}
      {weakestSubjects.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <ZapIcon className="w-4 h-4 text-yellow-500" />
              Focus Areas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">Subjects with the lowest accuracy — practice these to improve your score.</p>
            <div className="space-y-3">
              {weakestSubjects.map((s) => (
                <div key={s.subject} className="flex items-center gap-3">
                  <div className="flex-1 space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium text-gray-700 dark:text-gray-300">{s.subject}</span>
                      <span className={`text-xs font-semibold ${getScoreColor(s.accuracy)}`}>{s.accuracy}%</span>
                    </div>
                    <Progress value={s.accuracy} color={s.accuracy >= 60 ? 'yellow' : 'red'} />
                  </div>
                  <Link
                    to={`/quiz?subject=${encodeURIComponent(s.subject)}`}
                    className="flex-shrink-0 px-3 py-1.5 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Practice
                  </Link>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Subject accuracy bar chart */}
      {subjectData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Subject-wise Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={subjectData} margin={{ top: 5, right: 20, left: 0, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis
                  dataKey="subject"
                  tick={{ fontSize: 11, fill: axisColor }}
                  angle={-35}
                  textAnchor="end"
                  interval={0}
                />
                <YAxis tick={{ fontSize: 11, fill: axisColor }} domain={[0, 100]} unit="%" />
                <Tooltip
                  contentStyle={{ backgroundColor: tooltipBg, border: `1px solid ${tooltipBorder}`, borderRadius: '8px', color: tooltipText }}
                  formatter={(value, name) => [
                    name === 'accuracy' ? `${value}%` : value,
                    name === 'accuracy' ? 'Accuracy' : name === 'attempted' ? 'Attempted' : 'Correct',
                  ]}
                />
                <Bar dataKey="accuracy" fill="#3b82f6" radius={[4, 4, 0, 0]} name="accuracy" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Year performance */}
      {yearData.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Performance by Year</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={yearData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis dataKey="year" tick={{ fontSize: 11, fill: axisColor }} />
                <YAxis tick={{ fontSize: 11, fill: axisColor }} domain={[0, 100]} unit="%" />
                <Tooltip
                  contentStyle={{ backgroundColor: tooltipBg, border: `1px solid ${tooltipBorder}`, borderRadius: '8px', color: tooltipText }}
                  formatter={(v) => [`${v}%`, 'Accuracy']}
                />
                <Bar dataKey="accuracy" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Subject breakdown table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Detailed Subject Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {subjectData.map((d) => (
              <div key={d.fullSubject} className="space-y-1">
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium text-gray-700 dark:text-gray-300">{d.fullSubject}</span>
                  <span className="text-gray-500 dark:text-gray-400 text-xs">
                    {d.correct}/{d.attempted} · <span className={getScoreColor(d.accuracy)}>{d.accuracy}%</span>
                  </span>
                </div>
                <Progress
                  value={d.accuracy}
                  color={d.accuracy >= 80 ? 'green' : d.accuracy >= 60 ? 'yellow' : 'red'}
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Subject coverage */}
      {subjectCoverage.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BookOpenIcon className="w-4 h-4 text-blue-500" />
              Subject Coverage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
              Questions attempted out of total available per subject.
            </p>
            <div className="space-y-3">
              {subjectCoverage.map((s) => (
                <div key={s.subject} className="space-y-1">
                  <div className="flex justify-between items-center text-sm">
                    <span className="font-medium text-gray-700 dark:text-gray-300">{s.subject}</span>
                    <span className="text-gray-500 dark:text-gray-400 text-xs">
                      {s.attempted} / {s.total} · <span className="font-medium">{s.coveragePct}%</span>
                    </span>
                  </div>
                  <ProgressBar value={s.coveragePct} color="blue" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 90-day study planner */}
      {studyPlan.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <CalendarIcon className="w-4 h-4 text-indigo-500" />
              90-Day Study Planner
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
              Days allocated per subject based on your current accuracy and coverage gaps. Weak subjects with more questions get more time.
            </p>
            <div className="space-y-2.5">
              {studyPlan.map((s) => (
                <div key={s.subject} className="flex items-center gap-3">
                  <div className="w-32 flex-shrink-0">
                    <span className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate block">{s.subject}</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <div
                        className="h-5 rounded bg-indigo-500 dark:bg-indigo-600 flex items-center justify-end pr-1.5 min-w-[2rem] transition-all"
                        style={{ width: `${Math.max(8, (s.days / 90) * 100)}%` }}
                      >
                        <span className="text-[10px] font-bold text-white">{s.days}d</span>
                      </div>
                    </div>
                  </div>
                  <div className="w-16 flex-shrink-0 text-right">
                    <span className={`text-xs font-semibold ${getScoreColor(s.accuracy)}`}>
                      {s.attempted > 0 ? `${s.accuracy}%` : 'Not started'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-4">
              Tip: Start with your weakest subjects. Revisit the plan monthly as your accuracy improves.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Practice performance */}
      {Object.keys(progress.practiceSubjectStats ?? {}).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
                Practice
              </span>
              Practice Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(progress.practiceSubjectStats)
                .map(([subject, stats]) => ({
                  subject,
                  accuracy: percentage(stats.correct, stats.attempted),
                  attempted: stats.attempted,
                  correct: stats.correct,
                }))
                .sort((a, b) => b.attempted - a.attempted)
                .map((d) => (
                  <div key={d.subject} className="space-y-1">
                    <div className="flex justify-between items-center text-sm">
                      <span className="font-medium text-gray-700 dark:text-gray-300">{d.subject}</span>
                      <span className="text-gray-500 dark:text-gray-400 text-xs">
                        {d.correct}/{d.attempted} · <span className={getScoreColor(d.accuracy)}>{d.accuracy}%</span>
                      </span>
                    </div>
                    <Progress
                      value={d.accuracy}
                      color={d.accuracy >= 80 ? 'green' : d.accuracy >= 60 ? 'yellow' : 'red'}
                    />
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent sessions */}
      {sessions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Session History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {sessions.slice(0, 10).map((s) => {
                const c = Object.values(s.answers).filter((a) => a.isCorrect).length;
                const t = Object.keys(s.answers).length;
                const pct = percentage(c, t);
                return (
                  <div key={s.id} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                      pct >= 80 ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400' :
                      pct >= 60 ? 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400' :
                      'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400'
                    }`}>
                      {pct}%
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 flex items-center gap-1.5 flex-wrap">
                        {s.mode === 'practice' ? 'Practice Test' : 'Quiz'}
                        {s.subject && ` · ${s.subject}`}
                        {s.year && ` · ${s.year}`}
                        {s.source === 'practice' && (
                          <span className="inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
                            Practice
                          </span>
                        )}
                        {s.source === 'both' && (
                          <span className="inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                            Mixed
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {c}/{t} correct · {new Date(s.startedAt).toLocaleDateString()}
                      </p>
                    </div>
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
