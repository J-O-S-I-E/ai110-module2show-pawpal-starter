# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

Before writing any code, I identified three core actions a user should be able to perform:

1. **Add a pet** — The user needs to register a pet (name, species, age) so that care
   tasks can be associated with it. Without this, the system has nothing to schedule.

2. **Add a care task** — The user needs to create a task (e.g. "Morning walk", 30 min,
   HIGH priority) and assign it to a pet. Tasks are the central unit of data in PawPal+.

3. **View today's scheduled tasks** — The user needs to see a prioritized, time-ordered
   list of what needs to happen today. This is the app's main output and the reason
   scheduling logic exists.

These three actions map to the four main classes I'll need to build:
- `Task` (represents a single action)
- `Pet` (owns a list of tasks)
- `Owner` (owns a list of pets and a daily availability window)
- `Scheduler` (takes the owner's data and produces an ordered daily plan)

**b. Design changes**

After asking Copilot to review my skeletons with #file:pawpal_system.py,
I made the following changes:


1. **Added `task_id` to Task** — Copilot pointed out that without a unique
   identifier, removing a specific task from a pet's list would require matching
   on title, which breaks if two tasks have the same name. I added a
   `task_id` field using `uuid.uuid4()` as the default factory.

2. **Added `ScheduleResult` as a separate dataclass** — Initially I planned to
   return a plain dictionary from `build_schedule()`. Copilot suggested a typed
   return object would make the UI code cleaner and prevent key-error bugs. I
   agreed and added `ScheduleResult` with typed fields.

3. **Kept `available_start` and `available_end` as strings on Owner** — Copilot
   suggested converting them to `datetime.time` objects immediately. I decided
   against this because string inputs are simpler to collect from the Streamlit
   UI and the conversion can happen inside the Scheduler when needed.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
