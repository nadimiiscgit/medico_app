export interface Question {
  id: string;
  source?: 'pyq' | 'practice'; // optional — existing questions.json has no field, defaults to 'pyq'
  year: number;
  shift: number;
  questionNumber: number;
  question: string;
  options: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  correctAnswer: 'A' | 'B' | 'C' | 'D';
  explanation: string;
  subject: string;
  topic: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  tags: string[];
}

export type OptionKey = 'A' | 'B' | 'C' | 'D';

export interface UserAnswer {
  questionId: string;
  selectedOption: OptionKey | null;
  isCorrect: boolean;
  timeTaken: number; // seconds
  answeredAt: string; // ISO date
}

export interface TestSession {
  id: string;
  mode: 'practice' | 'quiz';
  source?: 'pyq' | 'practice' | 'both';
  startedAt: string;
  completedAt?: string;
  questionIds: string[];
  answers: Record<string, UserAnswer>;
  timeLimit?: number; // seconds
  subject?: string;
  year?: number;
  score?: number;
  totalQuestions?: number;
}

export interface UserProgress {
  totalAttempted: number;
  totalCorrect: number;
  subjectStats: Record<string, { attempted: number; correct: number }>;       // PYQ only
  practiceSubjectStats: Record<string, { attempted: number; correct: number }>; // practice only
  yearStats: Record<number, { attempted: number; correct: number }>;           // PYQ only
  streak: number;
  lastStudied?: string;
  totalStudyTime: number; // seconds
  sessions: TestSession[];
  bookmarks: string[]; // question IDs
  incorrectQuestionIds: string[]; // questions last answered incorrectly
  dailyGoal: number; // target questions per day
  dailyStats: { date: string; attempted: number }; // resets each day
}

export interface Filters {
  source: 'pyq' | 'practice' | 'both';
  years: number[];
  subjects: string[];
  difficulty: string[];
  search: string;
  onlyBookmarked: boolean;
  onlyUnanswered: boolean;
}

export type SortOrder = 'year-asc' | 'year-desc' | 'difficulty' | 'subject';
