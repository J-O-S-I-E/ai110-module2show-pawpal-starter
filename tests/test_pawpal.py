"""
tests/test_pawpal.py
Full automated test suite for PawPal+.

Covers all five behaviors identified in Phase 5 Step 1:
  1. Task completion
  2. Task addition
  3. Sorting correctness
  4. Recurrence logic
  5. Conflict detection

Run with:
    python -m pytest tests/ -v
"""

import pytest
from datetime import datetime
from pawpal_system import (
    Owner, Pet, Task, Scheduler, ScheduleResult, Priority, Species
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def basic_task() -> Task:
    """A plain non-recurring task with no scheduled time."""
    return Task(
        title="Morning walk",
        duration_minutes=30,
        priority=Priority.HIGH,
    )


@pytest.fixture
def recurring_task() -> Task:
    """A recurring task with a scheduled_start already set."""
    t = Task(
        title="Daily medication",
        duration_minutes=5,
        priority=Priority.HIGH,
        recurring=True,
    )
    t.scheduled_start = datetime(2025, 6, 1, 8, 0)
    return t


@pytest.fixture
def basic_pet() -> Pet:
    """A pet with no tasks."""
    return Pet(name="Mochi", species=Species.DOG, age_years=3)


@pytest.fixture
def basic_owner(basic_pet) -> Owner:
    """An owner with one pet and a 12-hour availability window."""
    owner = Owner(
        name="Jordan",
        available_start="08:00",
        available_end="20:00",
    )
    owner.add_pet(basic_pet)
    return owner


@pytest.fixture
def sample_tasks() -> list[Task]:
    """Four tasks with mixed priorities for sorting tests."""
    return [
        Task("Grooming",  duration_minutes=15, priority=Priority.LOW),
        Task("Playtime",  duration_minutes=20, priority=Priority.MEDIUM),
        Task("Feed",      duration_minutes=10, priority=Priority.HIGH),
        Task("Walk",      duration_minutes=30, priority=Priority.HIGH),
    ]


@pytest.fixture
def scheduled_date() -> datetime:
    """A fixed date used across scheduling tests."""
    return datetime(2025, 6, 1)


def build(owner: Owner, date: datetime) -> ScheduleResult:
    """Helper — runs the scheduler and returns the result."""
    return Scheduler(owner).build_schedule(date=date)


# ─────────────────────────────────────────────
# 1. Task Completion
# ─────────────────────────────────────────────

class TestTaskCompletion:
    """mark_done() must flip completed and handle recurring vs non-recurring."""

    def test_task_starts_incomplete(self, basic_task):
        """A newly created task should not be marked complete."""
        assert basic_task.completed is False

    def test_mark_done_sets_completed_true(self, basic_task):
        """Calling mark_done() must flip completed to True."""
        basic_task.mark_done()
        assert basic_task.completed is True

    def test_non_recurring_returns_none(self, basic_task):
        """A non-recurring task must return None — no next occurrence."""
        result = basic_task.mark_done()
        assert result is None

    def test_completed_task_leaves_pending_list(self, basic_pet, basic_task):
        """Once done, the task must not appear in pending_tasks()."""
        basic_pet.add_task(basic_task)
        basic_task.mark_done()
        assert basic_task not in basic_pet.pending_tasks()

    def test_completed_task_stays_in_full_list(self, basic_pet, basic_task):
        """Completed tasks remain in pet.tasks — only filtered from pending."""
        basic_pet.add_task(basic_task)
        basic_task.mark_done()
        assert basic_task in basic_pet.tasks


# ─────────────────────────────────────────────
# 2. Task Addition
# ─────────────────────────────────────────────

class TestTaskAddition:
    """add_task() must grow the task list and make tasks visible in pending."""

    def test_pet_starts_with_no_tasks(self, basic_pet):
        """A newly created pet should have an empty task list."""
        assert len(basic_pet.tasks) == 0

    def test_add_one_task_count_becomes_one(self, basic_pet, basic_task):
        """Adding one task should result in a task count of 1."""
        basic_pet.add_task(basic_task)
        assert len(basic_pet.tasks) == 1

    def test_add_three_tasks_count_becomes_three(self, basic_pet):
        """Adding three tasks must result in a count of exactly 3."""
        basic_pet.add_task(Task("Walk",     30, Priority.HIGH))
        basic_pet.add_task(Task("Feed",     10, Priority.HIGH))
        basic_pet.add_task(Task("Grooming", 15, Priority.LOW))
        assert len(basic_pet.tasks) == 3

    def test_added_task_in_task_list(self, basic_pet, basic_task):
        """The exact task object added must be retrievable from pet.tasks."""
        basic_pet.add_task(basic_task)
        assert basic_task in basic_pet.tasks

    def test_added_task_in_pending(self, basic_pet, basic_task):
        """A freshly added task must appear in pending_tasks()."""
        basic_pet.add_task(basic_task)
        assert basic_task in basic_pet.pending_tasks()


# ─────────────────────────────────────────────
# 3. Sorting Correctness
# ─────────────────────────────────────────────

class TestSorting:
    """sort_by_priority() and sort_by_time() must return correct order."""

    def test_sort_by_priority_high_first(self, sample_tasks):
        """Highest priority tasks must appear first in the sorted list."""
        sorted_tasks = Scheduler.sort_by_priority(sample_tasks)
        assert sorted_tasks[0].priority == Priority.HIGH
        assert sorted_tasks[-1].priority == Priority.LOW

    def test_sort_by_priority_descending_order(self, sample_tasks):
        """Priority values must be in non-increasing order throughout."""
        sorted_tasks = Scheduler.sort_by_priority(sample_tasks)
        values = [t.priority.value for t in sorted_tasks]
        assert values == sorted(values, reverse=True)

    def test_sort_by_priority_tie_broken_by_duration(self):
        """Two HIGH tasks must be ordered shortest duration first."""
        short = Task("Short", duration_minutes=10, priority=Priority.HIGH)
        long  = Task("Long",  duration_minutes=40, priority=Priority.HIGH)
        result = Scheduler.sort_by_priority([long, short])
        assert result[0].title == "Short"

    def test_sort_by_time_chronological(self, basic_owner, sample_tasks, scheduled_date):
        """Scheduled tasks must come back in ascending start-time order."""
        for t in sample_tasks:
            basic_owner.pets[0].add_task(t)
        result = build(basic_owner, scheduled_date)
        by_time = Scheduler.sort_by_time(result.scheduled)
        starts  = [t.scheduled_start for t in by_time]
        assert starts == sorted(starts)

    def test_sort_by_time_unscheduled_go_last(self):
        """Tasks with no scheduled_start must appear after all timed tasks."""
        timed     = Task("Timed",     10, Priority.HIGH)
        untimed   = Task("Untimed",   10, Priority.HIGH)
        timed.scheduled_start = datetime(2025, 6, 1, 9, 0)
        result = Scheduler.sort_by_time([untimed, timed])
        assert result[0].title == "Timed"
        assert result[1].title == "Untimed"


# ─────────────────────────────────────────────
# 4. Recurrence Logic
# ─────────────────────────────────────────────

class TestRecurrence:
    """Recurring tasks must auto-generate a next-day clone on completion."""

    def test_recurring_returns_new_task(self, recurring_task):
        """mark_done() on a recurring task must return a Task object."""
        clone = recurring_task.mark_done()
        assert clone is not None
        assert isinstance(clone, Task)

    def test_recurring_clone_is_next_day(self, recurring_task):
        """The clone's scheduled_start must be exactly 1 day after the original."""
        original_date = recurring_task.scheduled_start
        clone = recurring_task.mark_done()
        assert clone.scheduled_start.day == original_date.day + 1

    def test_recurring_clone_preserves_title(self, recurring_task):
        """The clone must keep the same title as the original."""
        clone = recurring_task.mark_done()
        assert clone.title == recurring_task.title

    def test_recurring_clone_preserves_priority(self, recurring_task):
        """The clone must keep the same priority as the original."""
        clone = recurring_task.mark_done()
        assert clone.priority == recurring_task.priority

    def test_recurring_clone_is_still_recurring(self, recurring_task):
        """The clone must also be marked recurring so the chain continues."""
        clone = recurring_task.mark_done()
        assert clone.recurring is True

    def test_complete_and_recur_adds_to_pet(self, basic_pet, recurring_task):
        """complete_and_recur() must append the clone to the pet's task list."""
        basic_pet.add_task(recurring_task)
        before = len(basic_pet.tasks)
        Scheduler.complete_and_recur(recurring_task, basic_pet)
        assert len(basic_pet.tasks) == before + 1

    def test_recurring_without_scheduled_start_returns_none(self):
        """A recurring task with no scheduled_start must return None safely."""
        t = Task("Walk", 30, Priority.HIGH, recurring=True)
        # scheduled_start is None — no next date can be calculated
        result = t.mark_done()
        assert result is None


# ─────────────────────────────────────────────
# 5. Conflict Detection
# ─────────────────────────────────────────────

class TestConflictDetection:
    """_detect_conflicts() must flag overlaps and ignore back-to-back tasks."""

    def _make_task(self, title: str, start_hour: int,
                   start_min: int, duration: int) -> Task:
        """Helper — create a task with a fixed scheduled_start."""
        t = Task(title, duration_minutes=duration, priority=Priority.HIGH)
        t.scheduled_start = datetime(2025, 6, 1, start_hour, start_min)
        return t

    def test_overlapping_tasks_flagged(self):
        """Two tasks whose durations overlap must produce a conflict warning."""
        # A: 09:00 → 09:30   B: 09:15 → 09:45   (15-min overlap)
        a = self._make_task("Walk A", 9,  0,  30)
        b = self._make_task("Walk B", 9,  15, 30)
        conflicts = Scheduler._detect_conflicts([a, b])
        assert len(conflicts) == 1

    def test_conflict_warning_contains_task_names(self):
        """The warning string must mention both conflicting task titles."""
        a = self._make_task("Walk A", 9,  0,  30)
        b = self._make_task("Walk B", 9,  15, 30)
        conflicts = Scheduler._detect_conflicts([a, b])
        assert "Walk A" in conflicts[0]
        assert "Walk B" in conflicts[0]

    def test_back_to_back_no_conflict(self):
        """Tasks that end exactly when the next begins must not be flagged."""
        # A: 09:00 → 09:30   B: 09:30 → 10:00   (no overlap)
        a = self._make_task("Feed",  9, 0,  30)
        b = self._make_task("Walk",  9, 30, 30)
        conflicts = Scheduler._detect_conflicts([a, b])
        assert len(conflicts) == 0

    def test_no_tasks_no_conflicts(self):
        """An empty task list must return an empty conflict list."""
        assert Scheduler._detect_conflicts([]) == []

    def test_one_task_no_conflicts(self):
        """A single task can never conflict with itself."""
        a = self._make_task("Solo", 9, 0, 30)
        assert Scheduler._detect_conflicts([a]) == []

    def test_greedy_schedule_has_no_conflicts(
        self, basic_owner, sample_tasks, scheduled_date
    ):
        """The scheduler's own output must never produce conflicts."""
        for t in sample_tasks:
            basic_owner.pets[0].add_task(t)
        result = build(basic_owner, scheduled_date)
        assert result.conflicts == []


# ─────────────────────────────────────────────
# Edge Cases
# ─────────────────────────────────────────────

class TestEdgeCases:
    """Boundary conditions that could crash or silently misbehave."""

    def test_empty_pet_no_crash(self, scheduled_date):
        """build_schedule() must work cleanly when a pet has zero tasks."""
        owner = Owner("Test", available_start="08:00", available_end="20:00")
        owner.add_pet(Pet("Empty", Species.CAT))
        result = build(owner, scheduled_date)
        assert result.scheduled == []
        assert result.skipped   == []

    def test_window_too_short_task_skipped(self, scheduled_date):
        """A task longer than the window must land in skipped, not scheduled."""
        owner = Owner("Tight", available_start="09:00", available_end="09:10")
        pet   = Pet("Pip", Species.CAT)
        pet.add_task(Task("Long task", duration_minutes=60, priority=Priority.HIGH))
        owner.add_pet(pet)
        result = build(owner, scheduled_date)
        assert len(result.skipped)   == 1
        assert len(result.scheduled) == 0

    def test_utilization_calculated_correctly(
        self, basic_owner, sample_tasks, scheduled_date
    ):
        """Utilization percentage must equal total_minutes / available_minutes."""
        for t in sample_tasks:
            basic_owner.pets[0].add_task(t)
        result   = build(basic_owner, scheduled_date)
        expected = round(result.total_minutes / result.available_minutes * 100, 1)
        assert result.utilization_pct == expected

    def test_filter_by_pet_returns_correct_tasks(self, basic_owner, sample_tasks):
        """filter_by_pet() must return only tasks belonging to the named pet."""
        for t in sample_tasks:
            basic_owner.pets[0].add_task(t)
        tasks = Scheduler.filter_by_pet(basic_owner, "Mochi")
        assert len(tasks) == len(sample_tasks)

    def test_filter_by_pet_unknown_returns_empty(self, basic_owner):
        """filter_by_pet() must return an empty list for an unknown pet name."""
        assert Scheduler.filter_by_pet(basic_owner, "Ghost") == []