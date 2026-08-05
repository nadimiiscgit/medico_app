-- Cohort — scoring, ranking and item statistics
--
-- Three things live here:
--   score_attempt()      one attempt -> score, honouring voided questions
--   test_rankings        rank + percentile across a test's cohort
--   compute_item_stats() difficulty + discrimination per question
--
-- Voided questions are excluded at scoring time rather than deleted, so a bad
-- item can be pulled and the cohort rescored without touching any response.

begin;

-- --------------------------------------------------------- score one attempt

create or replace function score_attempt(p_attempt_id uuid) returns void
language plpgsql as $$
declare
  v_test_id uuid;
  v_marks_correct numeric;
  v_marks_wrong   numeric;
  v_correct int;
  v_wrong   int;
  v_scored  int;
begin
  select a.test_id, t.marks_correct, t.marks_wrong
    into v_test_id, v_marks_correct, v_marks_wrong
  from attempts a
  join tests t on t.id = a.test_id
  where a.id = p_attempt_id;

  if v_test_id is null then
    raise exception 'score_attempt: attempt % not found', p_attempt_id;
  end if;

  select
    count(*) filter (where r.selected_option = q.correct_option),
    count(*) filter (where r.selected_option is not null
                       and r.selected_option <> q.correct_option),
    count(*)
  into v_correct, v_wrong, v_scored
  from test_questions tq
  join questions q on q.id = tq.question_id
  left join responses r
    on r.question_id = tq.question_id
   and r.attempt_id  = p_attempt_id
  where tq.test_id = v_test_id
    and not exists (
      select 1 from question_voids v
      where v.test_id = v_test_id
        and v.question_id = tq.question_id
    );

  update attempts set
    correct   = v_correct,
    wrong     = v_wrong,
    skipped   = v_scored - v_correct - v_wrong,
    score     = (v_correct * v_marks_correct) + (v_wrong * v_marks_wrong),
    scored_at = now()
  where id = p_attempt_id;
end;
$$;

-- ------------------------------------------------------ rescore a whole test
-- Call after voiding a question. Returns how many attempts were rescored.

create or replace function rescore_test(p_test_id uuid) returns int
language plpgsql as $$
declare
  v_attempt uuid;
  v_count int := 0;
begin
  for v_attempt in
    select id from attempts
    where test_id = p_test_id and submitted_at is not null
  loop
    perform score_attempt(v_attempt);
    v_count := v_count + 1;
  end loop;

  perform compute_item_stats(p_test_id);
  return v_count;
end;
$$;

-- ----------------------------------------------------------------- rankings
-- Percentile is the share of the cohort scoring strictly below you, which is
-- what a student means by "percentile". Ties share a rank, as in the real exam.

create or replace view test_rankings as
select
  a.test_id,
  a.id       as attempt_id,
  a.user_id,
  a.score,
  a.correct,
  a.wrong,
  a.skipped,
  rank() over (partition by a.test_id order by a.score desc) as rank,
  count(*)  over (partition by a.test_id)                    as cohort_size,
  round(
    (percent_rank() over (partition by a.test_id order by a.score asc))::numeric * 100,
    2
  ) as percentile
from attempts a
where a.mode = 'ranked'
  and a.submitted_at is not null
  and a.score is not null;

-- ------------------------------------------------------------- item statistics
-- p_value        fraction who got it right. Outside 0.2–0.9 it barely discriminates.
-- point_biserial correlation between getting this item right and total score.
--                <= 0.1 means the item is not measuring the same thing as the
--                rest of the paper — usually ambiguous, miskeyed, or leaked.

create or replace function compute_item_stats(p_test_id uuid) returns int
language plpgsql as $$
declare
  v_rows int;
begin
  delete from item_stats where test_id = p_test_id;

  insert into item_stats (
    test_id, question_id, n, n_correct, p_value, point_biserial,
    pct_a, pct_b, pct_c, pct_d, pct_blank, median_time_ms
  )
  with graded as (
    select
      tq.question_id,
      a.score,
      r.selected_option,
      r.time_ms,
      coalesce(r.selected_option = q.correct_option, false) as is_correct
    from attempts a
    join test_questions tq on tq.test_id = a.test_id
    join questions q       on q.id = tq.question_id
    left join responses r  on r.attempt_id = a.id
                          and r.question_id = tq.question_id
    where a.test_id = p_test_id
      and a.mode = 'ranked'
      and a.submitted_at is not null
      and a.score is not null
  ),
  spread as (
    select stddev_pop(score) as sd from attempts
    where test_id = p_test_id and mode = 'ranked'
      and submitted_at is not null and score is not null
  ),
  agg as (
    select
      g.question_id,
      count(*)                                  as n,
      count(*) filter (where g.is_correct)      as n_correct,
      avg(g.score) filter (where g.is_correct)     as mean_correct,
      avg(g.score) filter (where not g.is_correct) as mean_wrong,
      count(*) filter (where g.selected_option = 'A') as n_a,
      count(*) filter (where g.selected_option = 'B') as n_b,
      count(*) filter (where g.selected_option = 'C') as n_c,
      count(*) filter (where g.selected_option = 'D') as n_d,
      count(*) filter (where g.selected_option is null) as n_blank,
      percentile_cont(0.5) within group (order by g.time_ms) as median_time
    from graded g
    group by g.question_id
  )
  select
    p_test_id,
    agg.question_id,
    agg.n,
    agg.n_correct,
    round(agg.n_correct::numeric / nullif(agg.n, 0), 4),
    -- r_pb = ((M1 - M0) / SD) * sqrt(p * q)
    round(
      ((agg.mean_correct - agg.mean_wrong) / nullif(spread.sd, 0))
      * sqrt(
          (agg.n_correct::numeric / nullif(agg.n, 0))
          * (1 - agg.n_correct::numeric / nullif(agg.n, 0))
        ),
      4
    ),
    round(agg.n_a::numeric     * 100 / nullif(agg.n, 0), 2),
    round(agg.n_b::numeric     * 100 / nullif(agg.n, 0), 2),
    round(agg.n_c::numeric     * 100 / nullif(agg.n, 0), 2),
    round(agg.n_d::numeric     * 100 / nullif(agg.n, 0), 2),
    round(agg.n_blank::numeric * 100 / nullif(agg.n, 0), 2),
    agg.median_time::int
  from agg cross join spread;

  get diagnostics v_rows = row_count;
  return v_rows;
end;
$$;

-- --------------------------------------------------------- suspect items view
-- Items worth a human look after a test closes. High p_value with fast answers
-- suggests prior exposure; low or negative discrimination suggests a broken item.

create or replace view suspect_items as
select
  s.test_id,
  s.question_id,
  q.subject,
  s.n,
  s.p_value,
  s.point_biserial,
  s.median_time_ms,
  case
    when s.point_biserial < 0            then 'negative discrimination — likely miskeyed'
    when s.point_biserial < 0.10         then 'no discrimination — ambiguous or off-syllabus'
    when s.p_value > 0.90
     and s.median_time_ms < 20000        then 'very easy and answered fast — likely seen before'
    when s.p_value < 0.15                then 'almost nobody correct — check the key'
    -- Everyone answered the same way, so discrimination is undefined rather
    -- than low. Carries no information about ability either way.
    when s.point_biserial is null
     and s.p_value > 0.95                then 'everyone correct — carries no information'
    when s.point_biserial is null        then 'discrimination undefined — no variance in responses'
    when s.p_value > 0.95                then 'too easy to discriminate'
  end as flag
from item_stats s
join questions q on q.id = s.question_id
where s.point_biserial < 0.10
   or s.point_biserial is null
   or s.p_value < 0.15
   or s.p_value > 0.95
   or (s.p_value > 0.90 and s.median_time_ms < 20000);

commit;
