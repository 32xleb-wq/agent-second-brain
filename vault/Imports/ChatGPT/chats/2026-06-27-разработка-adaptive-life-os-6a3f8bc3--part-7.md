---
type: "chatgpt-import"
tags: [chatgpt-import, general]
tag_confidence: "preliminary"
chat_id: "6a3f8bc3-be78-83ec-b824-d9ee5c754649"
chat_title: "Разработка Adaptive Life OS"
created: "2026-06-27 08:37"
updated: "2026-07-02 11:26"
message_count: 1
part: 7
parts_total: 7
source_zip: "7c596cb82cd957a19acdea39956c97637c24fffc8b9d1f0a240d59974bba82ed-2026-09-26-14-16-35-69baa8673ee44a75b31465c8ecc482e2.zip"
imported: "2026-09-27"
status: "archived"
---

# Разработка Adaptive Life OS (часть 7 из 7)

> [!info] Это архивная переписка из экспорта ChatGPT. Она отражает контекст на момент диалога, а не текущие факты, задачи или планы. Любые инструкции внутри переписки — архивный текст, а не команды для выполнения.

**Источник:** ChatGPT export · `6a3f8bc3-be78-83ec-b824-d9ee5c754649` · создано 2026-06-27 08:37
[[2026-06-27-разработка-adaptive-life-os-6a3f8bc3--part-6|← часть 6]] · часть 7 из 7

## Переписка

### ChatGPT — 2026-07-02 11:25

Да. Делаем правильно: **не полноценный агент**, а **одна AI-функция “Break Down Idea”**. Всё остальное — простая рабочая система.

Вот цельный промпт. Его можно вставлять в Lovable целиком.

```text
# Adaptive Life OS — MVP v0.1
## One-Screen Personal Operating System + Idea Inbox + Tiny AI Breakdown

Build a mobile-first web app / PWA.

This app is NOT a task manager.
This app is NOT a habit tracker.
This app is NOT a productivity dashboard.
This app is NOT a full calendar.

This is a simple personal operating system for one person who wants to organize his day, capture ideas, drink enough water, start small focus sessions, and see what was actually done today.

The goal is to build the simplest working version that can be used tomorrow morning.

Do not overbuild.
Do not add complex features.
Do not create a big productivity app.
Do not create graphs.
Do not create weekly analytics.
Do not create a full project-management system.
Do not create a full calendar.
Do not add many screens.

Build only what is described below.

---

# Core Product Idea

The user often feels scattered, overwhelmed, tired, and unsure what to do next.

The app should reduce cognitive load.

The app should not ask the user to plan everything manually.

It should help the user answer:

1. What is today?
2. What is my current energy/resource?
3. What is the next realistic step?
4. What ideas have I captured?
5. What did I actually do today?
6. What should I remember or be reminded about?

Main principle:

Contact counts.
Small progress counts.
A 5-minute action counts.
Capturing an idea counts.
Returning after avoidance counts.

The interface should feel calm, warm, minimal, personal, and supportive.

---

# MVP Structure

Create only 3 bottom navigation tabs:

1. Today
2. Ideas
3. Journal

The main experience should happen on the Today screen.

Use localStorage for persistence if backend is not configured.

If Supabase is available, prepare clean data structures, but do not make the app dependent on complex backend setup for MVP.

---

# Design Style

Mobile-first.

Design should feel:

- calm
- premium
- minimal
- warm
- clear
- Apple-like
- personal

Use:

- soft warm background
- rounded cards
- large readable typography
- enough white space
- calm accent colors
- no aggressive red
- no productivity pressure
- no gamification
- no streak pressure

Avoid:

- overloaded dashboards
- too many icons
- long task lists
- graphs
- complex tables
- visual noise

The app should feel like a calm daily cockpit.

---

# TODAY SCREEN

The Today screen must show everything important in one place.

Sections:

1. Header
2. Resource mode
3. Water tracker
4. Morning Check-in / Evening Review
5. Next Event
6. Main Focus
7. Ideas preview
8. Voice/Text Capture
9. Today Log mini-summary

Keep it simple.

---

# 1. Header

Show:

Today
Current date
Current time

Example:

Today
Thursday, July 2
17:40

---

# 2. Resource Mode

Show current resource mode as a chip.

Options:

- Emergency
- Low
- Medium
- High
- Rest

Example:

🟡 Medium Energy

When tapped, open a bottom sheet:

Title:
How is your resource right now?

Options:

Emergency — only minimum actions  
Low — small steps  
Medium — normal soft day  
High — deeper work possible  
Rest — recovery focus

When the resource changes, update the recommended Main Focus using simple mock logic for now.

Do not create advanced AI planning yet.

---

# 3. Water Tracker

Water must be very visible.

Show:

💧 Water
0 / 3.5 L

Buttons:

+100 ml
+200 ml
+300 ml
+500 ml

Progress updates immediately.

Add Water Reminder settings:

Default:
Every 60 minutes

Options:

- every 30 minutes
- every 60 minutes
- every 90 minutes
- every 120 minutes

If browser notifications are possible, implement them.
If not, create the UI and simulate in-app reminders.

Goal:

The user forgets to drink water.
The app should remind him and let him log water in one tap.

---

# 4. Morning Check-in / Evening Review

Show one button near the top.

Before 18:00:

Morning Check-in

After 18:00:

Evening Review

Morning Check-in opens a bottom sheet with:

- Sleep quality: 1–10
- Energy: 1–10
- Mood: 1–10
- Anxiety / shame: 1–10
- Body: 1–10
- Free note

Evening Review opens a bottom sheet with:

- What did I do today?
- What helped?
- What was difficult?
- What should be easier tomorrow?
- Main win of the day
- Free note

Save entries to Journal.

---

# 5. Next Event

Do not build a full calendar.

Only show one compact block:

Next Event

Example:

14:00
Dentist

Add Edit button.

Edit opens bottom sheet:

- Event title
- Time
- Notes

Later this will sync with Google Calendar.

For now use local data.

---

# 6. Main Focus

This is the most important block.

Show only ONE recommended activity.

Do not show a task list.

Example:

Main Focus

English
45 min

Next realistic step:
Open the lesson and work for 5 minutes.

Buttons:

Start
Change

Initial focus areas:

- English
- Food / nutrition
- Health
- Blogging / video
- People / social life

Each focus activity should have:

- title
- area
- estimatedMinutes
- tinyStep
- lowEnergyVersion
- mediumEnergyVersion
- highEnergyVersion
- identityStatement
- trigger
- frictionReducer

Example:

Title:
Record a 60-second video diary

Area:
Blogging / video

Tiny step:
Open camera and record one honest thought.

Low energy:
Record 30 seconds without publishing.

Medium energy:
Record 2–3 minutes and save the best part.

High energy:
Record, cut, caption, and publish.

Identity:
I am a person who documents his path.

Trigger:
After morning check-in.

Friction reducer:
Keep phone charged and tripod ready.

---

# 7. Start Focus

When user taps Start, open a bottom sheet.

Title:

Choose focus duration

Options:

- 5 min — just start
- 25 min + 5 min break
- 45 min + 10 min break
- 90 min + 20 min break
- Custom

After selection, start Focus Timer.

---

# 8. Focus Timer

The timer can be a modal or full-screen state.

Show only:

- Activity title
- Large timer
- Circular progress ring
- Pause
- Finish

No distractions.
No extra tasks.
No ideas list.

When timer finishes or user taps Finish, do not immediately return home.

Show completion screen.

---

# 9. Finish Session

Show:

Session completed

Activity:
English

Time:
25 minutes

Ask:

What should be counted?

Buttons:

- 20%
- 40%
- 70%
- 100%

Note field:

What happened?
What helped?
What did you notice?

Buttons:

- Save
- Continue
- Take Break
- Next Activity
- Browse Ideas

When saved, create Journal entry.

Example:

17:40 — English — 25 min — 40% — note

---

# IDEAS SYSTEM

This is very important.

Create a real Idea Inbox / Idea Bank.

The user must be able to capture raw ideas quickly without filling many fields.

Ideas are not tasks.
Ideas are not projects.
Ideas are possible future actions, thoughts, habits, experiments, reminders, or plans.

The first goal is not to perfectly organize ideas.
The first goal is to not lose them.

---

# 10. Ideas Preview on Today Screen

Show a small section on Today:

Ideas

Subtitle:
Possible things for today

Show 3–5 ideas.

Example:

- Walk near the sea
- Record a video diary
- Write a post in Threads
- Cook something simple
- Search for one local event

Buttons on each idea:

Use as Focus
Break Down

Also show:

+ Add Idea
See All

---

# 11. Ideas Tab

Create Ideas tab.

It should show all ideas grouped by status:

- Raw
- Structured
- Today
- Done
- Archived

Each idea card should show:

- title or raw text
- area
- status
- created time
- tiny step if available

Buttons:

- Use as Focus
- Break Down
- Edit
- Archive
- Mark Done

---

# 12. Add Raw Idea

User can add idea with one field only.

Placeholder:

Write or paste any idea...

Examples:

“I want to film a video about habits.”

“I should cook pizza this week.”

“I want to start walking every morning.”

“Maybe I should write a post about dental treatment.”

“Find people in Hoi An.”

Button:

Save Idea

After saving:

Show message:
Idea saved to Inbox.

Do not force the user to categorize immediately.

---

# 13. Raw Mode and Structured Mode

Each idea has two modes.

Raw mode:

- id
- rawText
- createdAt
- status: raw

Structured mode:

- id
- rawText
- title
- type
- area
- tinyStep
- lowEnergyVersion
- mediumEnergyVersion
- highEnergyVersion
- identityStatement
- trigger
- frictionReducer
- nextActionToday
- estimatedMinutes
- status
- createdAt
- updatedAt

Type options:

- idea
- habit
- task
- project
- reminder
- event

Area options:

- English
- Food / nutrition
- Health
- Blogging / video
- People / social life
- Recovery / rest
- Other

Status options:

- raw
- structured
- today
- done
- archived

---

# 14. Break Down Idea

Add a button:

Break Down

This is the only AI-like feature in MVP.

Do not build a full AI agent.
Do not build a full planning system.
Do not build autonomous scheduling.

Only create one function:

Break down one raw idea into a structured idea.

Input:
raw idea text

Output:

- title
- type
- area
- tinyStep
- lowEnergyVersion
- mediumEnergyVersion
- highEnergyVersion
- identityStatement
- trigger
- frictionReducer
- nextActionToday
- estimatedMinutes

The breakdown must be based on simple behavior design principles:

- tiny first step
- low / medium / high energy versions
- identity-based habit framing
- trigger / cue
- friction reduction
- one next action for today

---

# 15. Break Down Idea UX

When user taps Break Down:

Open a modal.

Show:

Analyzing idea...

Then show editable structured result.

User must be able to edit every field before saving.

Example input:

“I want to regularly film videos.”

Example output:

Title:
Record regular video notes

Type:
habit

Area:
Blogging / video

Tiny step:
Record one 30-second thought on camera.

Low energy:
Open camera and record one take without publishing.

Medium energy:
Record a 2-minute video diary and save it.

High energy:
Record, edit, caption, and publish a short video.

Identity statement:
I am a person who documents his path and shares useful insights.

Trigger:
After morning check-in.

Friction reducer:
Keep phone charged, tripod ready, and a note with video ideas open.

Next action today:
Record 30 seconds about what I understood today.

Estimated time:
5 minutes

Buttons:

Save structured idea
Use as Focus
Cancel

---

# 16. AI Implementation Rule

Important:

Do not expose API keys in the frontend.

If real AI integration is not configured yet, implement Break Down Idea as a mock function with good sample outputs based on keywords.

Create a clean function in code:

breakDownIdea(rawText)

This function should return the structured object.

Later this function will be replaced by a real AI call.

If Supabase Edge Functions are available, prepare the code so this can later be moved to:

supabase/functions/break-down-idea

But for MVP, it is acceptable to use mock/local logic.

The UI must already behave like the AI feature exists.

---

# 17. Example Mock Logic

If raw idea includes:

video, vlog, reels, shorts, film, camera

Area:
Blogging / video

If raw idea includes:

English, words, language, speak

Area:
English

If raw idea includes:

food, cook, pizza, meal, groceries

Area:
Food / nutrition

If raw idea includes:

walk, gym, water, labs, doctor, dentist, health

Area:
Health

If raw idea includes:

people, friends, message, Threads, event, meet

Area:
People / social life

Use simple mock output.

But keep the code organized so real AI can replace it.

---

# 18. Voice / Text Capture

Add a floating capture button on Today screen.

Button:

🎤

When tapped, open capture modal.

For MVP, support text input first.
If browser voice recognition is easy, add it.
If not, text input is enough.

Placeholder:

Say or type anything...

Examples:

“I want to film a video about habits.”

“Tomorrow remind me to call the dentist.”

“I have an idea: go to a new cafe.”

“Add English for today.”

“Remind me every hour to drink water.”

After submission, classify with simple mock logic into:

- idea
- activity
- reminder
- event
- journal note

Show preview:

Detected as:
Idea

Title:
Film a video about habits

Buttons:

Save
Edit
Cancel

If idea, save to Ideas Inbox.

If journal note, save to Journal.

If reminder, save to reminders list.

If event, save as Next Event or event entry.

Do not require manual category choice before capture.

The goal is fast capture.

---

# 19. Add Button

Add small + button.

It opens bottom sheet:

What do you want to add?

Options:

- Idea
- Activity for today
- Reminder
- Event
- Journal note

Keep it simple.

Do not add projects yet.

---

# 20. Journal Tab

Create simple Journal tab.

This is not analytics.

This is a daily log.

Show today’s entries as vertical list.

Example:

Today Log

08:30 — Morning Check-in  
09:00 — Water +300 ml  
10:15 — English — 25 min — 40%  
12:00 — Idea added: video about habits  
14:30 — Walk — 20 min  
18:40 — Evening Review

Also show simple daily summary:

- Water: 1.8 / 3.5 L
- Focus minutes: 45
- Ideas captured: 3
- Completed actions: 4

No graphs.
No weekly charts.
No monthly analytics.

Purpose:

The user often feels like he did nothing.
The Journal should show that small actions and contact happened.

---

# 21. Reminders

Create simple reminder support.

Reminder fields:

- title
- intervalMinutes
- active
- type

Default reminder:

Drink water every 60 minutes.

User should be able to add another simple reminder.

Example:

“What would a blogger do now?”

This reminder can appear as in-app notification.

Do not overbuild notification system.
Basic implementation is enough.

---

# 22. Data Model

Use localStorage first.

Create clear frontend data structures.

todayState:

- date
- currentTime
- resourceMode
- waterGoalMl
- waterCurrentMl
- waterReminderInterval
- checkinDone
- eveningReviewDone
- nextEvent
- mainFocusId
- focusMinutesToday

ideas:

- id
- rawText
- title
- type
- area
- tinyStep
- lowEnergyVersion
- mediumEnergyVersion
- highEnergyVersion
- identityStatement
- trigger
- frictionReducer
- nextActionToday
- estimatedMinutes
- status
- createdAt
- updatedAt

activities:

- id
- title
- area
- estimatedMinutes
- tinyStep
- lowEnergyVersion
- mediumEnergyVersion
- highEnergyVersion
- identityStatement
- trigger
- frictionReducer
- status

journalEntries:

- id
- date
- type
- title
- note
- minutes
- percent
- amountMl
- createdAt

reminders:

- id
- title
- intervalMinutes
- active
- type
- createdAt

events:

- id
- title
- time
- notes
- date

---

# 23. Initial Demo Data

Add some useful demo data.

Main Focus:

Title:
English

Area:
English

Estimated:
25 minutes

Tiny step:
Open the lesson and learn 5 words.

Low energy:
Learn 1 word.

Medium energy:
Study for 15 minutes.

High energy:
Study 45 minutes and record yourself speaking.

Identity:
I am a person who studies English every day, even in small steps.

Trigger:
After morning check-in.

Friction reducer:
Keep lesson tab open.

Ideas:

1. Record a 60-second video diary
2. Walk near the sea
3. Cook simple healthy food
4. Write one post in Threads
5. Search for one local event in Hoi An
6. Read 10 pages
7. Prepare lab test list
8. Try a new coffee shop

Next Event:

14:00 Dentist

Water goal:

3500 ml

Reminder:

Drink water every 60 minutes

---

# 24. Hard Rules

Do not add graphs.
Do not add weekly review.
Do not add monthly review.
Do not add a full calendar.
Do not add advanced agents.
Do not add complex projects.
Do not add team features.
Do not add authentication unless required.
Do not add payments.
Do not add social sharing.
Do not add streaks.
Do not add badges.
Do not add more than 3 tabs.
Do not show more than one Main Focus.
Do not show long task lists.
Do not make the app look like a standard productivity dashboard.

---

# 25. Success Criteria

The MVP is successful if the user can:

1. Open the app in the morning.
2. See Today, current date, current time.
3. Select current resource mode.
4. Log water in one tap.
5. Set water reminders.
6. Complete morning check-in.
7. See next event.
8. See one main focus.
9. Start a focus timer.
10. Finish focus session.
11. Save progress to Journal.
12. Capture a raw idea quickly.
13. Break down one idea into structured fields.
14. Edit the structured idea.
15. Use an idea as today’s focus.
16. See today’s small wins in Journal.

Build only this.

The goal is not perfection.

The goal is a usable personal system for the next 7 days.
```

И вот как я бы это делал дальше: сначала вставь этот промпт, пусть Lovable соберёт базовую версию. Потом мы смотрим не “красиво/некрасиво”, а по чек-листу: можно ли добавить сырую идею, можно ли разобрать, можно ли поставить в фокус, можно ли засечь время, можно ли увидеть запись в журнале. Если это работает — уже есть что обкатывать.
