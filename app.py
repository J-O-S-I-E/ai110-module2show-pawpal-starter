"""
app.py
PawPal+ Streamlit UI.

Run with:
    streamlit run app.py
"""

import streamlit as st

# ── PawPal+ backend ────────────────────────────────────────────────────────────
from pawpal_system import (
    Owner,
    Pet,
    Task,
    Scheduler,
    ScheduleResult,
    Priority,
    Species,
)

# ── Page config (must be the FIRST Streamlit call — only call this once) ───────
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling.")

# ── Quick import check (delete these 4 lines once you've confirmed it works) ───
st.success(
    "✅ Backend connected! Classes available: "
    "Owner, Pet, Task, Scheduler, Priority, Species"
)