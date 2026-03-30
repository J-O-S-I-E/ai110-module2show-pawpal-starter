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

st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling.")

# ─────────────────────────────────────────────
# Session state initialisation
# ─────────────────────────────────────────────
# Think of st.session_state as a dictionary that survives re-runs.
# We check if the key exists BEFORE creating anything — this is the
# critical pattern. Without the `if` check, a new Owner would be
# created on every button click, wiping all existing data.

if "owner" not in st.session_state:
    st.session_state.owner = None   # No owner set up yet

# ─────────────────────────────────────────────
# Sidebar — Owner setup form
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Owner Setup")

    owner_name  = st.text_input("Your name",              value="Jordan")
    avail_start = st.text_input("Available from (HH:MM)", value="08:00")
    avail_end   = st.text_input("Available until (HH:MM)", value="20:00")

    if st.button("💾 Save Owner", use_container_width=True):
        # Only create a new Owner if one doesn't exist yet.
        # If one already exists, update its fields in place so
        # any pets already added are not lost.
        if st.session_state.owner is None:
            st.session_state.owner = Owner(
                name=owner_name,
                available_start=avail_start,
                available_end=avail_end,
            )
        else:
            st.session_state.owner.name            = owner_name
            st.session_state.owner.available_start = avail_start
            st.session_state.owner.available_end   = avail_end

        st.success(f"Saved! Hello, {owner_name} 👋")

# ─────────────────────────────────────────────
# Guard — stop here if no owner has been saved
# ─────────────────────────────────────────────
# st.stop() halts the script at this point so nothing below
# tries to access st.session_state.owner while it's still None.

if st.session_state.owner is None:
    st.info("👈 Fill in your name and availability in the sidebar, then click Save Owner.")
    st.stop()

# ─────────────────────────────────────────────
# Confirmation — show what's stored in state
# ─────────────────────────────────────────────
owner: Owner = st.session_state.owner

st.subheader("✅ Owner saved to session state")
st.write(f"**Name:** {owner.name}")
st.write(f"**Window:** {owner.available_start} – {owner.available_end}")
st.write(f"**Available minutes:** {owner.available_minutes}")
st.write(f"**Pets registered:** {len(owner.pets)}")

st.info(
    "Session state is working. This data will survive button clicks and "
    "form submissions without resetting. Add pets and tasks in Phase 3 Step 3."
)