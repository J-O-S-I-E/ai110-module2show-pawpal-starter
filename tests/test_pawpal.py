"""
tests/test_pawpal.py
Phase 2 test suite for PawPal+.

Covers the two required behaviors for this phase:
  1. Task completion  — mark_done() changes the task's status
  2. Task addition    — adding a task increases the pet's task count

Run with:
    python -m pytest tests/ -v
"""

import pytest
from pawpal_system import Pet, Task, Priority, Species


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
def basic_pet() -> Pet:
    """A pet with no tasks."""
    return Pet(name="Mochi", species=Species.DOG, age_years=3)


# ─────────────────────────────────────────────
# Test 1: Task Completion
# ─────────────────────────────────────────────

class TestTaskCompletion:
    """
    Verify that calling mark_done() correctly changes
    the task's completed status from False to True.
    """

    def test_task_starts_incomplete(self, basic_task):
        """A newly created task should not be marked complete."""
        assert basic_task.completed is False

    def test_mark_done_sets_completed_true(self, basic_task):
        """Calling mark_done() must flip completed to True."""
        basic_task.mark_done()
        assert basic_task.completed is True

    def test_mark_done_returns_none_for_non_recurring(self, basic_task):
        """
        A non-recurring task should return None from mark_done()
        because there is no next occurrence to create.
        """
        result = basic_task.mark_done()
        assert result is None

    def test_completed_task_excluded_from_pending(self, basic_pet, basic_task):
        """
        Once a task is marked done, it should no longer appear
        in the pet's pending_tasks() list.
        """
        basic_pet.add_task(basic_task)
        basic_task.mark_done()
        assert basic_task not in basic_pet.pending_tasks()


# ─────────────────────────────────────────────
# Test 2: Task Addition
# ─────────────────────────────────────────────

class TestTaskAddition:
    """
    Verify that adding a task to a Pet correctly increases
    that pet's task count.
    """

    def test_pet_starts_with_no_tasks(self, basic_pet):
        """A newly created pet should have an empty task list."""
        assert len(basic_pet.tasks) == 0

    def test_add_one_task_increases_count_to_one(self, basic_pet, basic_task):
        """Adding a single task should result in a task count of 1."""
        basic_pet.add_task(basic_task)
        assert len(basic_pet.tasks) == 1

    def test_add_three_tasks_increases_count_to_three(self, basic_pet):
        """Adding three tasks one at a time should result in a count of 3."""
        basic_pet.add_task(Task("Walk",     30, Priority.HIGH))
        basic_pet.add_task(Task("Feed",     10, Priority.HIGH))
        basic_pet.add_task(Task("Grooming", 15, Priority.LOW))
        assert len(basic_pet.tasks) == 3

    def test_added_task_appears_in_task_list(self, basic_pet, basic_task):
        """The specific task object added should be retrievable from the list."""
        basic_pet.add_task(basic_task)
        assert basic_task in basic_pet.tasks

    def test_added_task_appears_in_pending(self, basic_pet, basic_task):
        """A freshly added task should show up in pending_tasks()."""
        basic_pet.add_task(basic_task)
        assert basic_task in basic_pet.pending_tasks()