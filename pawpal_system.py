"""
pawpal_system.py
Core logic layer for PawPal+.
All backend classes live here. This file is UI-agnostic —
never import Streamlit in this file.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import uuid


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class Priority(Enum):
    """Task urgency level used to determine scheduling order."""
    LOW    = 1
    MEDIUM = 2
    HIGH   = 3

    @classmethod
    def from_str(cls, s: str) -> "Priority":
        """Convert a plain string like 'high' to Priority.HIGH."""
        return cls[s.upper()]


class Species(Enum):
    """Supported pet species."""
    DOG   = "dog"
    CAT   = "cat"
    OTHER = "other"


# ─────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────

@dataclass
class Task:
    """
    A single care activity for a pet.

    Attributes
    ----------
    title             : Human-readable name, e.g. "Morning walk".
    duration_minutes  : How long the task takes.
    priority          : LOW / MEDIUM / HIGH — drives scheduling order.
    preferred_time    : Optional hint: "morning", "afternoon", or "evening".
    recurring         : If True, completing the task auto-creates the next one.
    notes             : Free-text details, e.g. "Give with food".
    task_id           : Auto-generated unique ID (used for removal).
    completed         : Whether the task has been done today.
    scheduled_start   : Set by the Scheduler once a time slot is assigned.
    """
    title: str
    duration_minutes: int
    priority: Priority
    preferred_time: Optional[str] = None
    recurring: bool = False
    notes: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    completed: bool = False
    scheduled_start: Optional[datetime] = field(default=None, repr=False)

    # ── Computed property ──────────────────────

    @property
    def scheduled_end(self) -> Optional[datetime]:
        """Return the end time once scheduled_start has been set."""
        if self.scheduled_start:
            return self.scheduled_start + timedelta(minutes=self.duration_minutes)
        return None

    # ── Methods ───────────────────────────────

    def mark_done(self) -> Optional["Task"]:
        """
        Mark this task complete.

        If the task is recurring, returns a new Task cloned for the
        next day (scheduled_start + 1 day via timedelta). Otherwise
        returns None.
        """
        self.completed = True
        if self.recurring and self.scheduled_start:
            next_start = self.scheduled_start + timedelta(days=1)
            clone = Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                preferred_time=self.preferred_time,
                recurring=True,
                notes=self.notes,
            )
            clone.scheduled_start = next_start
            return clone
        return None

    def summary(self) -> str:
        """Return a formatted one-line string for terminal or UI display."""
        time_str = (
            self.scheduled_start.strftime("%I:%M %p")
            if self.scheduled_start else "unscheduled"
        )
        return (
            f"[{self.priority.name:<6}] {self.title:<25} "
            f"({self.duration_minutes} min) @ {time_str}"
        )


# ─────────────────────────────────────────────
# Pet
# ─────────────────────────────────────────────

@dataclass
class Pet:
    """
    Represents one of the owner's pets.

    Owns a list of Task objects and provides filtered views of them.
    Does not know anything about scheduling — that belongs to Scheduler.

    Attributes
    ----------
    name      : The pet's name.
    species   : DOG / CAT / OTHER.
    age_years : The pet's age in years.
    notes     : Free-text details about the pet.
    tasks     : All tasks associated with this pet.
    """
    name: str
    species: Species
    age_years: float = 0.0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a new task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> bool:
        """
        Remove a task by its unique ID.
        Returns True if a task was found and removed, False otherwise.
        """
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        return len(self.tasks) < before

    def pending_tasks(self) -> list[Task]:
        """Return all tasks that have not yet been marked complete."""
        return [t for t in self.tasks if not t.completed]

    def high_priority_tasks(self) -> list[Task]:
        """Return only HIGH-priority tasks that are not yet complete."""
        return [t for t in self.pending_tasks() if t.priority == Priority.HIGH]


# ─────────────────────────────────────────────
# Owner
# ─────────────────────────────────────────────

@dataclass
class Owner:
    """
    Represents the person using PawPal+.

    Owns a list of Pet objects and knows the daily window during which
    care tasks can be scheduled.

    Attributes
    ----------
    name            : The owner's name.
    available_start : Start of availability window, 24-h "HH:MM".
    available_end   : End of availability window, 24-h "HH:MM".
    pets            : All pets registered to this owner.
    """
    name: str
    available_start: str = "08:00"
    available_end: str = "20:00"
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet with this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """
        Remove a pet by name (case-insensitive).
        Returns True if a pet was found and removed, False otherwise.
        """
        before = len(self.pets)
        self.pets = [p for p in self.pets if p.name.lower() != pet_name.lower()]
        return len(self.pets) < before

    def all_pending_tasks(self) -> list[Task]:
        """
        Aggregate pending tasks across ALL pets into one flat list.
        This is the main entry point the Scheduler uses to get its data.
        """
        return [task for pet in self.pets for task in pet.pending_tasks()]

    @property
    def available_minutes(self) -> int:
        """Total minutes between available_start and available_end."""
        fmt = "%H:%M"
        start = datetime.strptime(self.available_start, fmt)
        end   = datetime.strptime(self.available_end,   fmt)
        return int((end - start).total_seconds() // 60)


# ─────────────────────────────────────────────
# ScheduleResult
# ─────────────────────────────────────────────

@dataclass
class ScheduleResult:
    """
    The output produced by Scheduler.build_schedule().

    Keeping this as a separate typed object (rather than a plain dict)
    makes the Streamlit UI code cleaner and prevents key-error bugs.

    Attributes
    ----------
    scheduled         : Tasks that were successfully assigned a time slot.
    skipped           : Tasks that didn't fit in the available window.
    conflicts         : Human-readable warning strings for any overlaps.
    total_minutes     : Sum of duration across all scheduled tasks.
    available_minutes : Total minutes in the owner's availability window.
    """
    scheduled: list[Task]
    skipped: list[Task]
    conflicts: list[str]
    total_minutes: int
    available_minutes: int

    @property
    def utilization_pct(self) -> float:
        """Percentage of the available window filled by scheduled tasks."""
        if self.available_minutes == 0:
            return 0.0
        return round(self.total_minutes / self.available_minutes * 100, 1)


# ─────────────────────────────────────────────
# Scheduler
# ─────────────────────────────────────────────

# Maps preferred_time strings to (start_hour, end_hour) ranges
_TIME_SLOTS: dict[str, tuple[int, int]] = {
    "morning":   (6,  12),
    "afternoon": (12, 17),
    "evening":   (17, 21),
}


class Scheduler:
    """
    The scheduling brain of PawPal+.

    Algorithm
    ---------
    1. Collect all pending tasks from the Owner's pets.
    2. Sort them: HIGH → MEDIUM → LOW; ties broken by shortest duration first.
    3. Assign time slots greedily, respecting preferred_time hints.
    4. Skip any task that would overflow the owner's available window.
    5. Detect overlapping durations and surface them as warning strings.

    The Scheduler holds no task data itself — all state lives in the
    Owner → Pet → Task layer. This keeps the logic independently testable.
    """

    def __init__(self, owner: Owner) -> None:
        """Bind the scheduler to a specific owner."""
        self.owner = owner

    # ── Public API ─────────────────────────────

    def build_schedule(self, date: Optional[datetime] = None) -> ScheduleResult:
        """
        Build and return a ScheduleResult for the given date.
        Defaults to today if no date is provided.
        """
        date = date or datetime.today().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        tasks          = self.owner.all_pending_tasks()
        sorted_tasks   = self._sort_tasks(tasks)
        scheduled, skipped = self._assign_times(sorted_tasks, date)
        conflicts      = self._detect_conflicts(scheduled)
        total          = sum(t.duration_minutes for t in scheduled)

        return ScheduleResult(
            scheduled=scheduled,
            skipped=skipped,
            conflicts=conflicts,
            total_minutes=total,
            available_minutes=self.owner.available_minutes,
        )

    # ── Sorting ────────────────────────────────

    @staticmethod
    def sort_by_priority(tasks: list[Task]) -> list[Task]:
        """Sort tasks HIGH → LOW; ties broken by shortest duration first."""
        return sorted(tasks, key=lambda t: (-t.priority.value, t.duration_minutes))

    @staticmethod
    def sort_by_time(tasks: list[Task]) -> list[Task]:
        """
        Sort tasks chronologically by scheduled_start.
        Tasks without a start time are placed at the end.
        Uses datetime comparison via a lambda key — not string comparison —
        so "09:00" correctly sorts before "10:30" in all cases.
        """
        return sorted(
            tasks,
            key=lambda t: t.scheduled_start or datetime.max
        )

    # ── Filtering ──────────────────────────────

    @staticmethod
    def filter_by_status(tasks: list[Task], completed: bool) -> list[Task]:
        """Return only tasks matching the given completion status."""
        return [t for t in tasks if t.completed == completed]

    @staticmethod
    def filter_by_pet(owner: Owner, pet_name: str) -> list[Task]:
        """Return all pending tasks belonging to the named pet."""
        for pet in owner.pets:
            if pet.name.lower() == pet_name.lower():
                return pet.pending_tasks()
        return []

    # ── Recurring helper ───────────────────────

    @staticmethod
    def complete_and_recur(task: Task, pet: Pet) -> Optional[Task]:
        """
        Mark a task done and, if it's recurring, add the next-day
        clone back to the pet's task list.
        Returns the new Task if one was created, else None.
        """
        next_task = task.mark_done()
        if next_task:
            pet.add_task(next_task)
        return next_task

    # ── Private helpers ────────────────────────

    @staticmethod
    def _sort_tasks(tasks: list[Task]) -> list[Task]:
        """Internal sort used by build_schedule (priority desc, duration asc)."""
        return sorted(tasks, key=lambda t: (-t.priority.value, t.duration_minutes))

    def _assign_times(
        self, tasks: list[Task], date: datetime
    ) -> tuple[list[Task], list[Task]]:
        """
        Walk through sorted tasks and assign each a start time.
        Respects preferred_time hints; falls back to the next free slot.
        Tasks that overflow the availability window are skipped.
        """
        fmt       = "%H:%M"
        day_start = datetime.combine(
            date.date(),
            datetime.strptime(self.owner.available_start, fmt).time()
        )
        day_end = datetime.combine(
            date.date(),
            datetime.strptime(self.owner.available_end, fmt).time()
        )

        scheduled: list[Task] = []
        skipped:   list[Task] = []
        cursor = day_start

        for task in tasks:
            ideal_start = self._preferred_start(task, date)
            start = max(cursor, ideal_start) if ideal_start else cursor
            end   = start + timedelta(minutes=task.duration_minutes)

            if end > day_end:
                skipped.append(task)
                continue

            task.scheduled_start = start
            scheduled.append(task)
            cursor = end

        return scheduled, skipped

    def _preferred_start(
        self, task: Task, date: datetime
    ) -> Optional[datetime]:
        """
        Convert a preferred_time string ('morning', 'afternoon', 'evening')
        into a concrete datetime on the given date.
        Returns None if no preferred_time is set.
        """
        if not task.preferred_time:
            return None
        slot = _TIME_SLOTS.get(task.preferred_time.lower())
        if not slot:
            return None
        return datetime.combine(
            date.date(),
            datetime.min.time().replace(hour=slot[0])
        )

    @staticmethod
    def _detect_conflicts(tasks: list[Task]) -> list[str]:
        """
        Check every pair of scheduled tasks for overlapping durations.
        Returns a list of human-readable warning strings.
        Raises no exceptions — warnings are surfaced to the UI instead.
        """
        conflicts = []
        for i, a in enumerate(tasks):
            for b in tasks[i + 1:]:
                if (
                    a.scheduled_start and a.scheduled_end
                    and b.scheduled_start and b.scheduled_end
                ):
                    if (
                        a.scheduled_start < b.scheduled_end
                        and b.scheduled_start < a.scheduled_end
                    ):
                        conflicts.append(
                            f"⚠️  Overlap: '{a.title}' and '{b.title}'"
                        )
        return conflicts

    # ── Output ────────────────────────────────

    @staticmethod
    def explain(result: ScheduleResult) -> str:
        """
        Produce a plain-text schedule summary.
        Suitable for the terminal, a README, or the Streamlit expander.
        """
        lines = ["📅 Daily Schedule", "=" * 40]
        for t in result.scheduled:
            lines.append(t.summary())
        if result.skipped:
            lines.append("\n⏭️  Skipped (didn't fit):")
            for t in result.skipped:
                lines.append(
                    f"  • {t.title} ({t.duration_minutes} min, {t.priority.name})"
                )
        if result.conflicts:
            lines.append("")
            lines.extend(result.conflicts)
        lines.append(
            f"\n⏱  {result.total_minutes} / {result.available_minutes} min used "
            f"({result.utilization_pct}%)"
        )
        return "\n".join(lines)

"""
app.py
PawPal+ Streamlit UI — Phase 3 Step 3.
All three forms are now wired to real backend class methods.

Run with:
    streamlit run app.py
"""

import streamlit as st
from pawpal_system import (
    Owner,
    Pet,
    Task,
    Scheduler,
    Priority,
    Species,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling.")

# ─────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None

# ─────────────────────────────────────────────
# Sidebar — Owner setup
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Owner Setup")

    owner_name  = st.text_input("Your name",               value="Jordan")
    avail_start = st.text_input("Available from (HH:MM)",  value="08:00")
    avail_end   = st.text_input("Available until (HH:MM)", value="20:00")

    if st.button("💾 Save Owner", use_container_width=True):
        if st.session_state.owner is None:
            # First save — create a brand new Owner object
            # and store it in session state
            st.session_state.owner = Owner(
                name=owner_name,
                available_start=avail_start,
                available_end=avail_end,
            )
        else:
            # Subsequent saves — update fields in place
            # so any pets already added are preserved
            st.session_state.owner.name            = owner_name
            st.session_state.owner.available_start = avail_start
            st.session_state.owner.available_end   = avail_end
        st.success(f"Saved! Hello, {owner_name} 👋")

    # Show registered pets in the sidebar for quick reference
    if st.session_state.owner and st.session_state.owner.pets:
        st.divider()
        st.caption("Registered pets")
        for p in st.session_state.owner.pets:
            st.write(f"• {p.name} ({p.species.value}, {p.age_years}y)")

# ─────────────────────────────────────────────
# Guard
# ─────────────────────────────────────────────
if st.session_state.owner is None:
    st.info("👈 Fill in your name and availability in the sidebar, then click Save Owner.")
    st.stop()

owner: Owner = st.session_state.owner

# ─────────────────────────────────────────────
# Section 1 — Add a Pet
# ─────────────────────────────────────────────
st.subheader("🐾 Add a Pet")

# st.form batches all inputs so the script only re-runs
# once when the submit button is clicked — not on every keystroke
with st.form("add_pet_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name    = st.text_input("Pet name", placeholder="Mochi")
    with col2:
        species_str = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        pet_age     = st.number_input("Age (years)", min_value=0.0,
                                       max_value=30.0, value=1.0, step=0.5)

    submitted = st.form_submit_button("➕ Add Pet", use_container_width=True)

    if submitted:
        if not pet_name.strip():
            st.warning("Please enter a pet name.")
        else:
            # Check the pet doesn't already exist
            existing_names = [p.name.lower() for p in owner.pets]
            if pet_name.strip().lower() in existing_names:
                st.warning(f"'{pet_name}' is already registered.")
            else:
                # ── Calls Owner.add_pet() and Pet() constructor ────────────
                new_pet = Pet(
                    name=pet_name.strip(),
                    species=Species(species_str),
                    age_years=pet_age,
                )
                owner.add_pet(new_pet)
                # ──────────────────────────────────────────────────────────
                st.success(f"Added {new_pet.name} ({species_str}) to your household!")

# Show all registered pets
if owner.pets:
    st.markdown("**Registered pets**")
    rows = [
        {
            "Name":    p.name,
            "Species": p.species.value,
            "Age":     f"{p.age_years}y",
            "Tasks":   len(p.tasks),
            "Pending": len(p.pending_tasks()),
        }
        for p in owner.pets
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ─────────────────────────────────────────────
# Section 2 — Add a Task
# ─────────────────────────────────────────────
st.subheader("📋 Add a Task")

if not owner.pets:
    st.warning("Add a pet first before adding tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        # Which pet does this task belong to?
        pet_names   = [p.name for p in owner.pets]
        target_name = st.selectbox("Assign to pet", pet_names)

        col1, col2, col3 = st.columns(3)
        with col1:
            task_title   = st.text_input("Task title", placeholder="Morning walk")
        with col2:
            duration     = st.number_input("Duration (min)", min_value=1,
                                            max_value=480, value=30)
        with col3:
            priority_str = st.selectbox("Priority", ["high", "medium", "low"])

        col4, col5 = st.columns(2)
        with col4:
            pref_time = st.selectbox(
                "Preferred time", ["(none)", "morning", "afternoon", "evening"]
            )
        with col5:
            recurring = st.checkbox("Recurring (repeats daily)")

        notes     = st.text_input("Notes (optional)", placeholder="e.g. Give with food")
        submitted = st.form_submit_button("➕ Add Task", use_container_width=True)

        if submitted:
            if not task_title.strip():
                st.warning("Please enter a task title.")
            else:
                # Find the target Pet object from owner.pets
                target_pet = next(p for p in owner.pets if p.name == target_name)

                # ── Calls Task() constructor and Pet.add_task() ────────────
                new_task = Task(
                    title=task_title.strip(),
                    duration_minutes=int(duration),
                    priority=Priority.from_str(priority_str),
                    preferred_time=None if pref_time == "(none)" else pref_time,
                    recurring=recurring,
                    notes=notes.strip(),
                )
                target_pet.add_task(new_task)
                # ──────────────────────────────────────────────────────────
                st.success(f"Added '{new_task.title}' to {target_name}!")

    # Show pending tasks for each pet
    for pet in owner.pets:
        pending = pet.pending_tasks()
        if not pending:
            continue
        st.markdown(f"**{pet.name}** — {len(pending)} pending task(s)")
        rows = [
            {
                "Task":     t.title,
                "Min":      t.duration_minutes,
                "Priority": t.priority.name,
                "Time":     t.preferred_time or "—",
                "Recurring": "Yes" if t.recurring else "No",
                "Notes":    t.notes or "—",
            }
            for t in pending
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)

st.divider()

# ─────────────────────────────────────────────
# Section 3 — Generate Schedule
# ─────────────────────────────────────────────
st.subheader("🗓️ Generate Schedule")

all_pending = owner.all_pending_tasks()

if not all_pending:
    st.info("Add at least one task before generating a schedule.")
else:
    if st.button("⚡ Build Today's Schedule", use_container_width=True):
        # ── Calls Scheduler.build_schedule() ──────────────────────────────
        scheduler = Scheduler(owner)
        result    = scheduler.build_schedule()
        # ──────────────────────────────────────────────────────────────────

        # Metrics row
        col1, col2, col3 = st.columns(3)
        col1.metric("Scheduled",   len(result.scheduled))
        col2.metric("Skipped",     len(result.skipped))
        col3.metric("Time used",   f"{result.total_minutes} min")

        # Scheduled tasks table
        if result.scheduled:
            st.markdown("**✅ Scheduled**")
            rows = [
                {
                    "Start":    t.scheduled_start.strftime("%I:%M %p"),
                    "End":      t.scheduled_end.strftime("%I:%M %p"),
                    "Task":     t.title,
                    "Priority": t.priority.name,
                    "Min":      t.duration_minutes,
                }
                for t in result.scheduled
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

        # Skipped tasks
        if result.skipped:
            st.warning(f"{len(result.skipped)} task(s) didn't fit in your window:")
            for t in result.skipped:
                st.write(f"  • {t.title} ({t.duration_minutes} min, {t.priority.name})")

        # Plain text summary
        with st.expander("📄 Plain-text summary"):
            st.code(Scheduler.explain(result), language="text")