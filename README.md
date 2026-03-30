## 🧠 Smarter Scheduling

PawPal+ goes beyond a simple task list. The `Scheduler` class implements
four algorithmic features that make the daily plan genuinely useful.

---

### Priority-first ordering

Tasks are sorted **HIGH → MEDIUM → LOW** before any time slots are assigned.
Within the same priority level, shorter tasks are placed first so quick care
actions (a 5-minute medication) are never blocked by a long task of equal
urgency. This guarantees that the most important care always happens, even
if the day runs short.

```python
sorted(tasks, key=lambda t: (-t.priority.value, t.duration_minutes))
```

---

### Preferred-time hints

Tasks can carry a soft time-of-day preference: `"morning"`, `"afternoon"`,
or `"evening"`. The scheduler respects these hints where possible but treats
them as suggestions, not hard constraints — a HIGH priority task will be
placed even if its preferred slot is already full.

| Hint | Target window |
|---|---|
| morning | 06:00 – 12:00 |
| afternoon | 12:00 – 17:00 |
| evening | 17:00 – 21:00 |

---

### Conflict detection

After building the schedule, every pair of tasks is checked for overlapping
durations using the interval overlap formula:

```
tasks overlap if: start_a < end_b AND start_b < end_a
```

Conflicts are returned as human-readable warning strings rather than
exceptions, so the app keeps running and the owner can decide how to
resolve them. Back-to-back tasks (one ends exactly when the next begins)
are correctly treated as non-overlapping.

---

### Recurring task automation

Tasks marked `recurring=True` automatically generate the next day's
occurrence when marked complete. The new task is cloned from the original
and its `scheduled_start` is advanced by exactly one day using
Python's `timedelta`:

```python
next_start = self.scheduled_start + timedelta(days=1)
```

This means daily care routines (morning walks, feedings, medications) only
need to be entered once — the system maintains the chain automatically.

---

### Sorting and filtering

The `Scheduler` class exposes four helper methods for the UI layer:

| Method | What it does |
|---|---|
| `sort_by_priority(tasks)` | HIGH → LOW, ties by shortest duration |
| `sort_by_time(tasks)` | Chronological by `scheduled_start` |
| `filter_by_status(tasks, completed)` | Done or pending tasks only |
| `filter_by_pet(owner, name)` | Tasks belonging to one specific pet |

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
