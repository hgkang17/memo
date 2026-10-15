# Product

<!-- impeccable:product-schema 1 -->

## Platform

windows-native

## Stack

Confirmed by the user: Python with Qt. Implementation uses Python 3.11+, PySide6, and SQLite.

## Users

Primary user: an individual working on a Windows desktop who wants tasks and short notes to remain visible without opening a full note-taking application.

## Product Purpose

Place one visually embedded memo widget on the Windows desktop and collect multiple editable white note cards inside it. Each card records created and modified timestamps, supports rich-text emphasis, and can be marked complete so its white working state becomes gray.

## Positioning

The note itself is the task surface: writing, visual emphasis, and completion happen directly on a lightweight desktop card rather than inside a document library or dashboard.

## Operating Context

Frequent, short desktop sessions in one compact widget window. New notes are added to a scrollable list inside that window, survive app restarts, and remain available after the window is hidden to the system tray.

## Capabilities and Constraints

- Confirmed: memo editing, highlighter colors, text colors, completion checkbox, and white-to-gray completion state.
- Confirmed: Python and Qt implementation on Windows.
- Confirmed: the application has one window; multiple notes are added inside that window rather than opening separate windows.
- Confirmed: active memo cards use a white background and show both created and last-modified date and time.
- Confirmed: the outer board should be visually transparent so the desktop shows through between cards.
- Confirmed: each note card has an independently adjustable, persisted height.
- Confirmed: each note card has independently persisted opacity presets.
- Confirmed: memo body paragraphs can become interactive checklist rows; checked rows alone turn gray and struck through.
- Confirmed: the transparent top rail shows only add, menu, minimize, and hide controls; formatting icons live inside each card's title rail.
- Confirmed: the menu exposes a live title index for jumping to a note.
- Confirmed: the widget uses a normal frameless Windows window so restoring after `Win+D` is stable without forcing topmost; topmost remains optional.
- Confirmed: releases ship as one portable Windows EXE and check the public GitHub repository for verified in-place updates.
- Inferred for the first version: local-only SQLite persistence, system-tray recovery, autosave, and remembered shared window geometry.
- The first version is a stable frameless desktop-style window. Direct attachment to the Windows Explorer `WorkerW` desktop layer remains deliberately undecided because that technique is brittle across Explorer restarts and Windows updates.

## Evidence on Hand

No logo, brand assets, reference screenshots, or existing application code were supplied. Do not fabricate commercial claims or external integrations.

## Product Principles

- Writing must be immediate: no save dialog or setup step.
- Completion must be visible at a glance and reversible.
- Formatting controls stay secondary to the note itself.
- Hiding the widget window must never imply deleting its notes.
- Local data should remain usable without an account or network connection.

## Accessibility & Inclusion

The inferred baseline is keyboard-operable controls, visible focus states, Korean labels, tooltips, and text/background contrast suitable for daily desktop use.
