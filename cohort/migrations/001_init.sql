-- Cohort — initial schema
-- Postgres 14+. Run with: npm run db:migrate
--
-- Design notes:
--   * Identity lives in Firebase; `users.firebase_uid` is the join key. All DB
--     access goes through Next.js route handlers using the service credential,
--     so there is no RLS here — the server is the only client.
--   * Timing is server-authoritative. `attempts.expires_at` is computed on the
--     server at start and is the sole source of truth for "is this attempt over".
--   * Scoring always excludes questions voided for that test, so a bad item can
--     be pulled and the whole cohort rescored without touching responses.

begin;

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------- users

create type user_role as enum ('student', 'reviewer', 'admin');

create table users (
  id            uuid primary key default gen_random_uuid(),
  firebase_uid  text unique not null,
  phone         text unique,
  email         text,
  name          text,
  college       text,
  grad_year     int,
  role          user_role not null default 'student',
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index users_role_idx on users (role) where role <> 'student';

-- ------------------------------------------------------------- concepts
-- The concept ledger mined from 13 years of PYQs. `pyq_frequency` is how many
-- times NBE has asked this concept — the weight used when blueprinting a test.

create table concepts (
  id             uuid primary key default gen_random_uuid(),
  name           text not null,
  subject        text not null,
  parent_id      uuid references concepts (id) on delete set null,
  pyq_frequency  int not null default 0,
  first_seen_year int,
  last_seen_year  int,
  created_at     timestamptz not null default now(),
  unique (subject, name)
);

create index concepts_subject_freq_idx on concepts (subject, pyq_frequency desc);

-- ------------------------------------------------------------ questions

create type question_status  as enum ('draft', 'needs_review', 'approved', 'rejected', 'retired');
create type question_source  as enum ('generated', 'pyq', 'pool');
create type difficulty_level as enum ('easy', 'moderate', 'hard');

create table questions (
  id              uuid primary key default gen_random_uuid(),
  stem            text not null,
  option_a        text not null,
  option_b        text not null,
  option_c        text not null,
  option_d        text not null,
  correct_option  char(1) not null check (correct_option in ('A', 'B', 'C', 'D')),
  explanation     text not null default '',
  subject         text not null,
  topic           text,
  concept_id      uuid references concepts (id) on delete set null,
  difficulty      difficulty_level,
  -- diagnosis | next_step | investigation | treatment | mechanism | recall
  archetype       text,
  source          question_source not null,
  -- generator model, prompt version, source concept, citations
  generation_meta jsonb not null default '{}'::jsonb,
  -- cold-consensus results: votes, agreement, adversarial flags
  verification    jsonb not null default '{}'::jsonb,
  status          question_status not null default 'draft',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index questions_status_idx  on questions (status);
create index questions_subject_idx on questions (subject, status);
create index questions_concept_idx on questions (concept_id);

-- ---------------------------------------------------------------- tests

create type test_status as enum ('draft', 'scheduled', 'live', 'closed');

create table tests (
  id              uuid primary key default gen_random_uuid(),
  slug            text unique not null,
  title           text not null,
  description     text,
  opens_at        timestamptz not null,
  closes_at       timestamptz not null,
  duration_s      int not null default 12600,          -- 3h 30m
  total_questions int not null default 200,
  marks_correct   numeric(4, 2) not null default 4,
  marks_wrong     numeric(4, 2) not null default -1,
  is_free         boolean not null default true,
  status          test_status not null default 'draft',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  constraint tests_window_valid check (closes_at > opens_at)
);

create index tests_window_idx on tests (opens_at, closes_at);

create table test_questions (
  test_id     uuid not null references tests (id) on delete cascade,
  question_id uuid not null references questions (id) on delete restrict,
  position    int  not null,
  primary key (test_id, position),
  unique (test_id, question_id)
);

-- ------------------------------------------------------------- attempts

create type attempt_mode as enum ('ranked', 'practice');

create table attempts (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references users (id) on delete cascade,
  test_id        uuid not null references tests (id) on delete cascade,
  mode           attempt_mode not null,
  started_at     timestamptz not null default now(),
  -- server-computed at start; the only clock that counts
  expires_at     timestamptz not null,
  submitted_at   timestamptz,
  auto_submitted boolean not null default false,
  score          numeric(7, 2),
  correct        int,
  wrong          int,
  skipped        int,
  scored_at      timestamptz
);

-- Exactly one ranked attempt per student per test. Enforced by the database,
-- not by application logic.
create unique index attempts_one_ranked_per_user
  on attempts (user_id, test_id) where mode = 'ranked';

create index attempts_test_scored_idx on attempts (test_id, score desc)
  where mode = 'ranked' and submitted_at is not null;
create index attempts_user_idx on attempts (user_id, started_at desc);

-- ------------------------------------------------------------ responses

create table responses (
  id                uuid primary key default gen_random_uuid(),
  attempt_id        uuid not null references attempts (id) on delete cascade,
  question_id       uuid not null references questions (id) on delete restrict,
  -- null means seen but not answered
  selected_option   char(1) check (selected_option in ('A', 'B', 'C', 'D')),
  marked_for_review boolean not null default false,
  time_ms           int not null default 0,
  change_count      int not null default 0,
  updated_at        timestamptz not null default now(),
  unique (attempt_id, question_id)
);

create index responses_question_idx on responses (question_id);

-- --------------------------------------------------------------- voids
-- A row here removes the question from scoring for that test. Rescoring the
-- cohort is then just re-running score_attempt() for every attempt.

create table question_voids (
  test_id     uuid not null references tests (id) on delete cascade,
  question_id uuid not null references questions (id) on delete cascade,
  reason      text not null,
  voided_by   uuid references users (id),
  voided_at   timestamptz not null default now(),
  primary key (test_id, question_id)
);

-- -------------------------------------------------------------- reports

create type report_status as enum ('open', 'accepted', 'rejected');

create table question_reports (
  id          uuid primary key default gen_random_uuid(),
  question_id uuid not null references questions (id) on delete cascade,
  test_id     uuid references tests (id) on delete set null,
  user_id     uuid references users (id) on delete set null,
  reason      text not null,
  detail      text,
  status      report_status not null default 'open',
  created_at  timestamptz not null default now(),
  resolved_at timestamptz,
  resolved_by uuid references users (id)
);

create index question_reports_open_idx on question_reports (status, created_at)
  where status = 'open';

-- --------------------------------------------------------- review queue

create type review_decision as enum ('pending', 'accepted', 'edited', 'rejected');

create table review_items (
  id          uuid primary key default gen_random_uuid(),
  question_id uuid not null references questions (id) on delete cascade,
  -- why it was flagged: consensus_split, adversarial_flag, duplicate, reported
  reason      text not null,
  priority    int not null default 0,
  assigned_to uuid references users (id) on delete set null,
  decision    review_decision not null default 'pending',
  notes       text,
  created_at  timestamptz not null default now(),
  decided_at  timestamptz,
  decided_by  uuid references users (id)
);

create index review_items_pending_idx on review_items (decision, priority desc, created_at)
  where decision = 'pending';

-- ----------------------------------------------------------- item stats
-- Recomputed after each test closes. This table is the compounding asset:
-- difficulty and discrimination for every item, from real students.

create table item_stats (
  test_id        uuid not null references tests (id) on delete cascade,
  question_id    uuid not null references questions (id) on delete cascade,
  n              int not null,
  n_correct      int not null,
  -- difficulty index: fraction correct. <0.2 or >0.9 carries little information
  p_value        numeric(5, 4),
  -- discrimination: correlation between getting this right and total score.
  -- Near zero or negative means the item is broken, whoever wrote it.
  point_biserial numeric(5, 4),
  pct_a          numeric(5, 2),
  pct_b          numeric(5, 2),
  pct_c          numeric(5, 2),
  pct_d          numeric(5, 2),
  pct_blank      numeric(5, 2),
  median_time_ms int,
  computed_at    timestamptz not null default now(),
  primary key (test_id, question_id)
);

-- ------------------------------------------------------- updated_at trigger

create or replace function touch_updated_at() returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger users_touch     before update on users     for each row execute function touch_updated_at();
create trigger questions_touch before update on questions for each row execute function touch_updated_at();
create trigger tests_touch     before update on tests     for each row execute function touch_updated_at();

commit;
