"""
demo.py
CLI verification script for PawPal+.

Run this from your terminal to confirm backend logic works
before connecting anything to the Streamlit UI.

Usage:
    python demo.py
"""

from datetime import datetime
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, Species


def print_section(title: str) -> None:
    """Print a clearly visible section header to the terminal."""
    print(f"\n{'=' * 45}")
    print(f"  {title}")
    print(f"{'=' * 45}")


# ─────────────────────────────────────────────
# 1. Create the Owner
# ─────────────────────────────────────────────
print_section("1. Setting up Owner")

owner = Owner(
    name="Jordan",
    available_start="08:00",
    available_end="20:00",
)
print(f"Owner   : {owner.name}")
print(f"Window  : {owner.available_start} – {owner.available_end}")
print(f"Minutes : {owner.available_minutes} available today")


# ─────────────────────────────────────────────
# 2. Create 2 Pets
# ─────────────────────────────────────────────
print_section("2. Adding Pets")

mochi = Pet(name="Mochi", species=Species.DOG, age_years=3)
luna  = Pet(name="Luna",  species=Species.CAT, age_years=1)

owner.add_pet(mochi)
owner.add_pet(luna)

for pet in owner.pets:
    print(f"  • {pet.name} ({pet.species.value}, {pet.age_years}y)")


# ─────────────────────────────────────────────
# 3. Add Tasks to each Pet
# ─────────────────────────────────────────────
print_section("3. Adding Tasks")

# Tasks for Mochi
mochi.add_task(Task(
    title="Morning walk",
    duration_minutes=30,
    priority=Priority.HIGH,
    preferred_time="morning",
    recurring=True,
))
mochi.add_task(Task(
    title="Breakfast feeding",
    duration_minutes=10,
    priority=Priority.HIGH,
    preferred_time="morning",
))
mochi.add_task(Task(
    title="Medication",
    duration_minutes=5,
    priority=Priority.HIGH,
    notes="Give with food",
))
mochi.add_task(Task(
    title="Training session",
    duration_minutes=20,
    priority=Priority.MEDIUM,
    preferred_time="afternoon",
))
mochi.add_task(Task(
    title="Evening walk",
    duration_minutes=45,
    priority=Priority.HIGH,
    preferred_time="evening",
    recurring=True,
))

# Tasks for Luna
luna.add_task(Task(
    title="Breakfast",
    duration_minutes=5,
    priority=Priority.HIGH,
    preferred_time="morning",
))
luna.add_task(Task(
    title="Litter box clean",
    duration_minutes=10,
    priority=Priority.MEDIUM,
))
luna.add_task(Task(
    title="Playtime",
    duration_minutes=15,
    priority=Priority.MEDIUM,
    preferred_time="afternoon",
))

# Confirm counts
for pet in owner.pets:
    print(f"  • {pet.name}: {len(pet.tasks)} tasks added")

total = len(owner.all_pending_tasks())
print(f"\n  Total pending across all pets: {total}")


# ─────────────────────────────────────────────
# 4. Generate Today's Schedule
# ─────────────────────────────────────────────
print_section("4. Today's Schedule")

scheduler = Scheduler(owner)
result    = scheduler.build_schedule(date=datetime(2025, 6, 1))

print(Scheduler.explain(result))


# ─────────────────────────────────────────────
# 5. Sorted by time
# ─────────────────────────────────────────────
print_section("5. Same Schedule — Sorted by Time")

by_time = Scheduler.sort_by_time(result.scheduled)
for task in by_time:
    start = task.scheduled_start.strftime("%I:%M %p")
    end   = task.scheduled_end.strftime("%I:%M %p")
    print(f"  {start} → {end}  {task.title}")


# ─────────────────────────────────────────────
# 6. Filter — Mochi's tasks only
# ─────────────────────────────────────────────
print_section("6. Filter — Mochi's Pending Tasks")

mochi_tasks = Scheduler.filter_by_pet(owner, "Mochi")
for task in mochi_tasks:
    print(f"  [{task.priority.name:<6}] {task.title}")


# ─────────────────────────────────────────────
# 7. Edge case — very short window
# ─────────────────────────────────────────────
print_section("7. Edge Case — 30-Minute Window")

busy_owner = Owner(
    name="Busy Alex",
    available_start="09:00",
    available_end="09:30",
)
tiny_pet = Pet(name="Pip", species=Species.CAT, age_years=1)
tiny_pet.add_task(Task("Quick feed",  5,  Priority.HIGH))
tiny_pet.add_task(Task("Playtime",   20, Priority.MEDIUM))
tiny_pet.add_task(Task("Grooming",   40, Priority.LOW))
busy_owner.add_pet(tiny_pet)

r2 = Scheduler(busy_owner).build_schedule(date=datetime(2025, 6, 1))
print(Scheduler.explain(r2))