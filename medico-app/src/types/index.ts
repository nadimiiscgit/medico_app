import type { SRCard } from '../lib/spacedRepetition';
export type { SRCard };

export type OptionKey = 'A' | 'B' | 'C' | 'D';

/**
 * Set on the twelve questions that are defective as printed — two options equally
 * correct, no correct option offered, a self-contradictory stem, or evidence lost
 * from a memory-based recall. Absent on every other question.
 */
export interface DataQuality {
  status: 'defective';
  defect:
    | 'multiple_correct_options'
    | 'no_correct_option'
    | 'contradictory_stem'
    | 'evidence_lost'
    | 'contested_answer';
  /** Every option that counts as correct. Omitted when none can be defended. */
  acceptableAnswers?: OptionKey[];
  note: string;
  reviewedOn: string;
}

export interface Question {
  id: string;
  source?: 'pyq' | 'practice'; // optional — existing questions.json has no field, defaults to 'pyq'
  exam?: string;               // 'NEET PG' | 'INI CET' | 'AIPGMEE'
  section?: string;
  topicId?: string;
  dataQuality?: DataQuality;
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
  subject: string;
  topic: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  tags: string[];
  imageUrl?: string;    // primary question image (2022–2024 papers)
  imageUrls?: string[]; // additional images if more than one
}

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
  practiceBookmarkSubjects: Record<string, string>; // questionId → subject, for practice bookmarks only
  incorrectQuestionIds: string[]; // questions last answered incorrectly
  srCards: Record<string, SRCard>;  // spaced repetition data keyed by questionId
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
