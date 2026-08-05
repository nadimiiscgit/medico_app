# Cohort — project context

**Last updated:** 5 August 2026
**Purpose:** everything decided so far, with the reasoning. Read this before writing code.
If a decision below looks wrong, check the rationale first — most were made against a
specific constraint that isn't obvious from the code.

---

## 1. What Cohort is

A ranked Grand Test series for NEET PG.

Ten Grand Tests. 200 questions, 3 hours 30 minutes, +4 for correct, −1 for wrong — the
real exam's format. Each test opens in a **fixed window**: everyone sits the same paper at
the same time, so rank and percentile are measured against a genuine cohort rather than a
rolling average of whoever happened to show up. After the window closes the paper stays
open, unranked, for practice.

**The product is the cohort, not the questions.** Question banks are a commodity in this
market — every competitor has 18,000 to 75,000 of them, and one competitor gives 75,000
away free. What students cannot get for free is a trustworthy answer to "where do I stand
against 20,000 other people." That is what they pay for and it is the only thing here that
compounds.

---

## 2. Why this, and why now

### Market findings that drive the design

Full analysis is in `docs/competitive-landscape.md` in the `medico_app` repo. The parts
that constrain engineering decisions:

| Finding | Consequence for us |
|---|---|
| Marrow: ₹641 Cr revenue, ₹363 Cr profit FY25, 57% margin, owned by M3 Inc. (Japan) | Never compete on video or faculty. That war is over. |
| Marrow prices tests-only at ₹14,999/yr vs QBank+tests at ₹18,999/yr | **Assessment is worth ~4× content.** Rank is the monetisable asset. |
| PrepLadder already ships spaced repetition (SPARK) | SM-2 is table stakes, not a differentiator. |
| Pre PG: free, 75k questions, **4.83 on iOS** — best-rated in the category | A content-light free app can win. It's also our closest competitor. |
| CoreBTR: solo creator, ~1 year old, **10,395 iOS ratings at 4.73**, ₹14,920/yr | A small trusted product beats a big untrusted one. |
| The two leaders charge ₹27–37k and sit at 4.2–4.5 stars | Incumbent satisfaction is soft where the money is. |

### Timing

NEET PG is **30 August 2026**. Test series sell in the final four weeks. GT-1 must open
around **11 August** to leave any selling window.

---

## 3. Current status

**Done and verified:**

- Next.js 16 + TypeScript + Tailwind scaffold
- `migrations/001_init.sql` — full schema
- `migrations/002_scoring.sql` — scoring, ranking, psychometrics
- `scripts/migrate.ts` — idempotent migration runner

Verified against a hand-computed 4-student fixture on Postgres 16: scores, ranks and
percentiles exact; point-biserial **0.7621** against 0.762 predicted by hand; voiding a
question correctly reordered the cohort (a weaker student overtook a stronger one because
the voided item was one the stronger student had got right).

**Not built yet:** auth and roles, test player, results page, reviewer queue, admin
console, revision PDF, payments.

**Blocked on the user:** `DATABASE_URL`, Firebase config + service account, Razorpay keys,
a qualified medical reviewer, and an `ANTHROPIC_API_KEY` for the content pipeline.

---

## 4. Architecture — decided, with reasons

Do not re-open these without a new constraint.

### Postgres, not Firestore

The entire product is ranking and statistics. Rank and percentile are one query:

```sql
RANK()         OVER (ORDER BY score DESC)
PERCENT_RANK() OVER (ORDER BY score ASC)
```

In Firestore this becomes a Cloud Function that reads every attempt and recomputes by
hand, and item statistics get worse from there. The existing `medico-app` uses Firebase
only as a static host, so there was no sunk cost to protect.

### Firebase Auth for identity, Postgres for data

Phone OTP is the primary login (Indian medical students expect it), Google is the fallback.

**Firebase specifically, because of TRAI DLT.** Every commercial SMS to an Indian number —
OTPs included — requires DLT registration: entity approval 1–3 working days, then sender ID
and templates 48–72 hours. Skip it and Jio/Airtel/Vi silently drop your messages. Firebase
holds the aggregator relationships, so we do no DLT paperwork at all. Cost is roughly
$0.01–0.07 per verification; at 2,000 users that is $20–140, i.e. irrelevant. Requires the
**Blaze** plan with a billing account.

### No Supabase Auth, no RLS

All database access goes through Next.js route handlers using the service credential.
Those handlers verify the Firebase ID token and are the **only** database client. This
avoids maintaining two auth systems and avoids reasoning about row-level security policies
under time pressure.

`users.firebase_uid` is the join key between the two systems.

### Stack summary

| Layer | Choice |
|---|---|
| Framework | Next.js 16 (App Router) + TypeScript + Tailwind 4 |
| Identity | Firebase Auth — phone OTP primary, Google fallback |
| Data | Postgres (Supabase, Mumbai region) |
| DB access | Next.js route handlers only, service credential |
| Hosting | Vercel |
| Payments | Razorpay, from GT-4 |
| PDF | React-PDF, server-side |

**Supabase connection strings:** use the **transaction pooler (port 6543)** for the app —
serverless functions open a connection per invocation and will exhaust direct connections
under load. Use the **direct connection (5432)** for migrations. Budget for Supabase Pro
($25/mo) before GT-1; the free tier's connection limit will not survive 500 students
submitting inside one window.

---

## 5. Invariants

These are load-bearing. Breaking any one of them makes the ranking untrustworthy, which
destroys the only thing the product sells.

**1. Timing is server-authoritative.**
`attempts.expires_at` is computed on the server when the attempt starts and is the only
clock that counts. Client clocks are never trusted. Submissions after expiry are rejected
(small grace for network latency); the server auto-submits on expiry. The test window
itself (`tests.opens_at` / `closes_at`) is enforced the same way.

**2. One ranked attempt per student per test.**
Enforced by a partial unique index in the database, not by application logic:

```sql
create unique index attempts_one_ranked_per_user
  on attempts (user_id, test_id) where mode = 'ranked';
```

**3. Voided questions are excluded at scoring time, never deleted.**
A row in `question_voids` removes an item from scoring for that test. `rescore_test()`
then recomputes every attempt. Student responses are never modified. **This must work from
day one** — it is what makes a bad question survivable rather than fatal.

**4. Grand Test questions never come from the previous-year (PYQ) archive.**
Every student drills previous years systematically. A paper built from them measures prior
exposure rather than ability: scores bunch at the top, the distribution compresses, and
rank stops discriminating exactly where students care most. Questions come from a pool
de-duplicated against the PYQ set.

The PYQ archive stays a **separate, free** product — it is the distribution hook, and it is
*supposed* to be pre-solved because nothing there is ranked.

**5. Item quality is established by statistics, not provenance.**
Who or what wrote a question tells you nothing about whether it is good. Difficulty index,
point-biserial discrimination and distractor analysis do. Marrow's questions are trusted
because they have been run against hundreds of thousands of students and the bad ones were
weeded out — that is an empirical asset we can build faster than we can build a faculty.

**6. Practice mode after the window is unranked and excluded from `item_stats`.**
Otherwise late takers with access to leaked answers pollute both the rank and the item
statistics.

---

## 6. Data model

Full DDL in `migrations/001_init.sql`. Shape:

```
users            firebase_uid, phone, email, name, college, grad_year,
                 role ∈ {student, reviewer, admin}
concepts         name, subject, parent_id, pyq_frequency,
                 first_seen_year, last_seen_year
questions        stem, option_a..d, correct_option, explanation, subject,
                 topic, concept_id, difficulty, archetype,
                 source ∈ {generated, pyq, pool},
                 generation_meta jsonb, verification jsonb,
                 status ∈ {draft, needs_review, approved, rejected, retired}
tests            slug, title, opens_at, closes_at, duration_s (12600),
                 total_questions (200), marks_correct (+4), marks_wrong (−1),
                 is_free, status ∈ {draft, scheduled, live, closed}
test_questions   test_id, question_id, position
attempts         user_id, test_id, mode ∈ {ranked, practice},
                 started_at, expires_at, submitted_at, auto_submitted,
                 score, correct, wrong, skipped, scored_at
responses        attempt_id, question_id, selected_option (null = blank),
                 marked_for_review, time_ms, change_count
question_voids   test_id, question_id, reason, voided_by, voided_at
question_reports question_id, test_id, user_id, reason, detail, status
review_items     question_id, reason, priority, assigned_to, decision, notes
item_stats       test_id, question_id, n, n_correct, p_value,
                 point_biserial, pct_a..d, pct_blank, median_time_ms
```

### Scoring and psychometrics (`migrations/002_scoring.sql`)

| Object | Purpose |
|---|---|
| `score_attempt(uuid)` | Scores one attempt, skipping voided questions |
| `rescore_test(uuid)` | Rescores every attempt, then recomputes item stats. Returns count |
| `test_rankings` (view) | `RANK()` and `PERCENT_RANK()` per test, plus `cohort_size` |
| `compute_item_stats(uuid)` | Difficulty, point-biserial, distractor spread, median time |
| `suspect_items` (view) | Flags items needing human review after a test closes |

**Point-biserial** is `((M₁ − M₀) / SD) × √(p·q)` — the correlation between getting an item
right and total score. Interpretation:

| Value | Meaning |
|---|---|
| < 0 | Negative discrimination — almost always **miskeyed** |
| < 0.10 | No discrimination — ambiguous or off-syllabus |
| 0.10–0.20 | Weak, keep but watch |
| > 0.20 | Healthy |
| `null` | Everyone answered the same way; undefined, and the item carries no information |

**Difficulty index (`p_value`)** outside 0.2–0.9 barely discriminates. `p_value > 0.9`
combined with a fast median time suggests the item was **seen before** — that signal is how
you detect leakage empirically, and it is worth showing students.

---

## 7. Content pipeline

Not built. This is the make-or-break workstream and needs an `ANTHROPIC_API_KEY`.

### Available raw material (measured, not estimated)

| Asset | Count | Notes |
|---|---|---|
| PYQ archive 2012–2024 | 10,541 | **100%** have explanations |
| Practice pool (MedMCQA, Apache-2.0) | 117,003 | 90% have explanations |
| Practice pool de-duplicated against PYQs | **110,118** | The GT source pool |
| Overlap: exact duplicate of a PYQ | 5,416 | 4.6% |
| Overlap: near-duplicate (token signature) | 1,469 | 1.3% |
| PYQs with topic tags | 394 | **3.7% — the main content gap** |
| Practice questions with topic tags | 59,461 | 51%, messy vocabulary (2,278 distinct) |

Topic vocabulary needs normalising to ~150 controlled values — it currently contains
collisions like `C.V.S` / `Cardiovascular system` and `Misc.` / `Miscellaneous`.
The `difficulty` field on existing questions is a **length heuristic** and must not be
trusted for anything.

### The approach: concept-anchored regeneration

Copying fails invariant 4. Pure LLM invention fails medically. What works: the *concept* is
validated by the fact that NBE actually asked it, but the vignette is new.

1. **Concept ledger.** Extract and cluster the concept behind each of the 10,541 PYQs.
   Expect 3,000–4,000 distinct concepts with frequency counts. Concepts appearing 5+ times
   across 13 years are NBE's demonstrated priorities — stated in their own behaviour rather
   than a coaching institute's opinion. Store in `concepts.pyq_frequency`.
2. **Archetype distribution.** From the **recent papers only (2022–2024, ~505 questions)**,
   measure the mix of diagnosis / next best step / investigation of choice / treatment of
   choice / mechanism / direct recall. Recent NBE skews hard clinical; older papers don't.
   **Concept from all 13 years, style from the last 3.**
3. **Blueprint** each test across subjects, then across concepts by frequency, then assign
   archetype and target difficulty per slot.
4. **Generate** with 30% overage. Require: clinical stem where the concept permits, 4
   options from one category with similar lengths, no absolutes ("always"/"never"), no
   grammatical tells, and a cited source concept.
5. **Verify** — the gate that matters (below).
6. **Human review** of the flagged subset only.
7. **Calibrate** from `item_stats` after each test; retire failures.

### Verification gate

- **Cold consensus.** Three independent answers per question with the key hidden, ideally
  across two model families. 3/3 agreement → auto-accept. 2/3 → human queue. 0–1/3 →
  reject outright (key is wrong or the item is broken).
- **Adversarial pass.** Separate prompt asked to attack it: is a second option defensible?
  Is any distractor eliminable without medical knowledge? Is the stem ambiguous?
- **Duplicate check** by token signature against both the PYQ set and accepted items.

This cannot distinguish *ambiguous* from *genuinely hard* — both produce disagreement.
That distinction is exactly what the human queue is for.

Budget: ~2,600 generations + ~7,800 verification calls, under $100 and a few hours
parallelised.

### Distractor quality

This is where tacit paper-setting expertise actually lives, and it is the one thing not
derivable from PYQs alone — a past paper shows the options but never which wrong option
students *picked*. Four routes:

1. Mine the 10,541 existing PYQ explanations for "commonly confused with…" phrasing.
2. Use the concept ledger as a distractor engine — the best distractors are adjacent
   concepts in the same cluster.
3. Force it in the prompt: ask for distractors each targeting a **named** diagnostic error,
   then strip the names before publication. Unnamed distractors come out obviously wrong.
4. After GT-1, distractor analysis gives it empirically for our own items.

### Human review is not optional

Expect 15–20% flagged, ~400 questions for a full series. Review is accept/reject/edit,
not authoring — 30–45 seconds each, so 3–5 hours of one qualified person. **This is the
only unparallelisable input in the project.**

LLM-generated medical questions can be subtly wrong in ways a non-expert reviewer will
miss. Concept-anchoring reduces this a lot but not to zero, which is why invariant 3
(void and rescore) is a day-one feature rather than a nice-to-have.

### Blueprint — 200 questions

Derived from current NEET PG weightage, **not** from our own archive. 84% of the PYQ
archive is 2012–2016, which was preclinical-heavy (Anatomy 12.7%, Medicine 8%); current
NEET PG is the reverse. Using the archive's distribution would produce a test that feels a
decade out of date.

```
Medicine 26 · Surgery 20 · OBG 20 · PSM 14 · Paediatrics 12 · Pharmacology 12
Pathology 12 · Microbiology 10 · Anatomy 10 · Physiology 8 · Biochemistry 8
Forensic 8 · Ophthalmology 8 · ENT 8 · Orthopaedics 6 · Psychiatry 5
Radiology 5 · Dermatology 4 · Anaesthesia 4                          = 200
```

Every subject clears its 10-test quota from the novel pool. Tightest is Dermatology:
40 needed against 1,291 available.

---

## 8. Build order

| # | Milestone | Notes |
|---|---|---|
| ✅ | Schema + scoring engine | Done, verified |
| 1 | Auth + three roles | Firebase phone OTP + Google, server-side token verification, route protection. `ADMIN_PHONES` bootstraps admin on first login |
| 2 | Test player | 200 Q, palette, mark-for-review, autosave to IndexedDB, **resume after disconnect**, server-enforced expiry with auto-submit |
| 3 | Submit → score → results | Rank, percentile, subject and topic breakdown |
| 4 | Reviewer queue + admin console | Accept/reject/edit; schedule tests, void-and-rescore, report queue, cohort stats |
| 5 | Revision PDF + practice mode + report button | |
| 6 | Razorpay paywall | From GT-4, ~17 August |

**Disconnect resilience is not optional.** Indian mobile networks drop constantly. Every
response writes to IndexedDB immediately and syncs opportunistically; a refresh or signal
loss resumes the same attempt with the clock still correct, because the clock lives on the
server.

There is a playable preview of the intended test player interaction model at
<https://claude.ai/code/artifact/5ef67759-f81c-4a3e-a27a-c507ca075300>

### Schedule

GT-1 opens **11 August**, then every 2–3 days through **29 August**. Free through GT-3,
paid from GT-4. You do not need 2,000 questions on the 11th — you need 200. Build GT-N+1
while GT-N is running, and spend a disproportionate review budget on GT-1 because word of
mouth from it determines whether GT-4's paywall converts.

---

## 9. Environment variables

```
DATABASE_URL                      # Supabase transaction pooler, port 6543
NEXT_PUBLIC_FIREBASE_API_KEY
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
NEXT_PUBLIC_FIREBASE_PROJECT_ID
NEXT_PUBLIC_FIREBASE_APP_ID
FIREBASE_SERVICE_ACCOUNT_JSON     # base64-encoded, one line
NEXT_PUBLIC_RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET               # server only — never NEXT_PUBLIC_
RAZORPAY_WEBHOOK_SECRET
ADMIN_PHONES                      # comma-separated E.164
NEXT_PUBLIC_APP_URL
```

Gotchas:

- `NEXT_PUBLIC_*` values are **baked in at build time**. Changing one in the Vercel
  dashboard does nothing without a redeploy.
- The service-account JSON is multi-line and Vercel mangles it — base64 it.
- Add the Vercel domain to **Firebase → Authentication → Settings → Authorised domains**,
  or phone OTP fails in production while working on localhost.
- Set **SMS region policy to India only**. Unrestricted phone auth is a standard SMS
  toll-fraud target.
- Never grant entitlement from Razorpay's browser success callback — that is trivially
  faked. Only on a signature-verified webhook, server-side.

---

## 10. Test-day runbook

1. Set `tests.status = 'scheduled'` with `opens_at` / `closes_at`.
2. At `opens_at`, students start attempts. Server sets `expires_at = started_at + duration_s`.
3. Auto-submit on expiry; reject late submissions past the grace period.
4. After `closes_at`: `rescore_test(test_id)` — scores everyone and computes item stats.
5. Review `suspect_items`. Anything with negative point-biserial is almost certainly
   miskeyed — check it first.
6. Void bad items with a reason, re-run `rescore_test()`, and **publish that you did it**.
   Being visibly good at corrections earns more trust than pretending to be perfect, and
   every incumbent is terrible at it.
7. Release solutions and rank.
8. Flip to practice mode (unranked, excluded from `item_stats`).

---

## 11. Risks

**Cohort size is the biggest one, and it is not technical.** A percentile computed on 40
takers is noise, students feel it immediately, and the core promise fails no matter how
good the code and questions are.

| Cohort | Guidance |
|---|---|
| < 200 | Show rank; label percentile provisional or withhold it |
| ~500 | Credible |
| 1,000+ | The product genuinely works |

Free through GT-3 exists precisely to buy N. **If GT-1 can't reach a few hundred, delay it
rather than run it small** — a weak first cohort is harder to recover from than a late start.

Others:

- **Wrong answer in a graded test.** Mitigated by the verification gate, human review, and
  void-and-rescore. Never fully eliminated.
- **Question leakage** between takers in a window. Fixed windows are the main defence;
  item statistics detect it after the fact.
- **Supabase free-tier connection limits** under concurrent submit. Upgrade before GT-1.
- **Razorpay KYC** takes 2–4 working days. Test keys work immediately, so it only gates
  real money, not development.

---

## 12. Repos

- **`nadimiiscgit/medico_app`** — the existing PYQ practice PWA (`medico-app/`), the
  competitive analysis (`docs/competitive-landscape.md`), and the initial Cohort code
  (`cohort/`, commit `ba52b8a` on branch `claude/med-ed-competition-analysis-vk3q0r`).
- **`nadimiiscgit/cohort_medico_test`** — intended permanent home for Cohort.

`medico-app/` and Cohort are separate products and must stay decoupled. The PYQ app is the
free top-of-funnel; Cohort is the ranked paid product.
