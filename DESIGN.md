---
name: Memo Sticker
description: White memo sheets placed directly over a transparent desktop field, with quiet timestamped task states.
colors:
  desktop-field: "rgba(0, 0, 0, 0)"
  chrome-translucent: "rgba(255, 255, 255, 0.87)"
  paper-active: "#FFFFFF"
  paper-completed: "#D8D6CF"
  paper-completed-rail: "#CCCAC3"
  graphite: "#302D25"
  graphite-muted: "#74716A"
  graphite-soft: "#746D5E"
  resize-grip: "#625A45"
  menu-surface: "#FFFDF7"
  menu-hover: "#F0E8D8"
  focus-ink: "#514C3E"
  action: "#2F4A42"
  action-hover: "#3B5D52"
  action-pressed: "#243A34"
  action-wash: "#E7EEE9"
  warm-hairline: "rgba(70, 63, 47, 0.16)"
typography:
  title:
    fontFamily: "Segoe UI Variable Text, Segoe UI, Malgun Gothic, sans-serif"
    fontSize: "17px"
    fontWeight: 700
  body:
    fontFamily: "Segoe UI Variable Text, Segoe UI, Malgun Gothic, sans-serif"
    fontSize: "14px"
    fontWeight: 400
  label:
    fontFamily: "Segoe UI Variable Text, Segoe UI, Malgun Gothic, sans-serif"
    fontSize: "11px"
    fontWeight: 600
  meta:
    fontFamily: "Segoe UI Variable Text, Segoe UI, Malgun Gothic, sans-serif"
    fontSize: "10px"
    fontWeight: 400
  control:
    fontFamily: "Segoe UI Variable Text, Segoe UI, Malgun Gothic, sans-serif"
    fontSize: "12px"
    fontWeight: 600
  appTitle:
    fontFamily: "Segoe UI Variable Text, Segoe UI, Malgun Gothic, sans-serif"
    fontSize: "15px"
    fontWeight: 750
  compactTitle:
    fontFamily: "Segoe UI Variable Text, Segoe UI, Malgun Gothic, sans-serif"
    fontSize: "16px"
    fontWeight: 700
rounded:
  swatch: "4px"
  menu-item: "5px"
  control: "7px"
  action: "8px"
  footer: "11px"
  card: "12px"
  chrome: "13px"
spacing:
  compact: "6px"
  control: "9px"
  rail: "14px"
  body: "13px"
---

# Design System: Memo Sticker

## Overview

**Creative North Star: "The Desktop Paper Field"**

Memo Sticker should feel embedded in the desktop rather than framed inside another application window. The outer field, top drag rail, and gaps are fully transparent; only the four global controls, memo sheets, and a small corner resize grip remain visible.

The interface is deliberately restrained because users repeatedly enter, scan, and close small tasks. Memo cards stack in one scrollable window; each card gives most of its area to user content while completion and formatting controls occupy narrow rails.

**Key Characteristics:**

- One transparent desktop field containing a vertical stack of white paper cards.
- One uninterrupted writing field inside every card.
- White unfinished notes and a neutral graphite completed state.
- Quiet created and modified timestamps on every card.
- Authored checklist and color-swatch icons for familiar formatting, with Korean tooltips and accessible names.
- Visible focus borders and reversible state changes.

## Colors

The palette uses opaque white paper over a transparent field with warm graphite text, reserving gray for completion rather than for inactive decoration.

### Primary

- **Clean White Paper:** Default working surface for unfinished notes.
- **Graphite Ink:** Primary text and control color.

### Secondary

- **Highlighter Set:** Lemon, mint, coral, and blue appear only behind selected rich text.

### Neutral

- **Transparent Desktop Field:** Reveals the wallpaper between the header, cards, and footer.
- **Completed Paper:** Replaces the whole white card surface when work is checked off.
- **Menu Surface:** Near-white context menus keep commands readable over every note color.
- **Muted Graphite:** Read-only completed content and disabled controls.

### Named Rules

**The Whole-Card State Rule.** Completion changes the entire selected card from white working paper to gray; the transparent field and other notes remain unchanged.

**The Ink Stays Warm Rule.** Active text uses warm graphite rather than absolute black so it belongs to the paper surface.

## Typography

**Display Font:** Not used.
**Body Font:** Segoe UI Variable Text with Segoe UI, Malgun Gothic, and system sans fallbacks.

**Character:** A familiar Windows UI sans keeps a small desktop utility fast to scan. Hierarchy comes from weight and size, not a separate display face.

### Hierarchy

- **Title** (700, 17px): Editable memo title and strongest user-authored line.
- **Body** (400, 14px): Rich-text memo content.
- **Completion Label** (700, 12px): The primary state control.
- **Control Label** (600, 11px): Header, timestamp, and formatting actions.

### Named Rules

**The User Content Leads Rule.** No application heading may outrank the note title or body inside a memo window.

## Layout

The default board is approximately 430×650px with a 350×420px minimum. A 42px transparent drag rail sits above a scrollable vertical list with matching 13px side insets and 10px transparent gaps. Only add, menu, minimize, and hide appear on that rail. Each card contains a completion/title rail with compact formatting icons, a created/modified timestamp row, a flexible checklist-capable writing field, and a quiet bottom resize grip. Cards start at 238px high and can be adjusted independently from 210–720px. New cards enter at the top of the same window.

## Elevation & Depth

The system uses no outer board plate, header plate, footer plate, or outer shadow. Separation comes from memo-sheet surfaces and precise low-contrast hairlines against the visible desktop. Cards may be reduced to 85%, 70%, or 55% opacity without changing the transparent field.

### Named Rules

**The No Outer Plate Rule.** Desktop wallpaper must remain visible between every major surface; never add a full-window fill or shadow behind the list.

## Shapes

Memo cards use 12px corners. Compact controls use 7–8px corners, checklist boxes use 3–4px corners, and color swatches use 4px corners. Rounded shapes remain functional and modest; full pills are not part of this system.

## Components

### Buttons

- **Shape:** Compact rounded rectangle (7px) with Korean action text.
- **Header:** The rail itself is fully transparent; only its four controls render a surface.
- **Primary action:** Deep evergreen identifies `메모 추가` without coloring passive chrome.
- **Formatting:** Icon-only split buttons sit left of Settings. Their main area reapplies the remembered color; their arrow opens color choices.
- **Focus:** A solid 2px graphite border remains visible across every paper color.

### Board / Container

- **Corner Style:** No enclosing outer silhouette or rail container.
- **Background:** Fully transparent field and header rail.
- **Shadow Strategy:** No outer shadow.
- **Internal Padding:** 13px around the card list.

### Memo Cards

- **Corner Style:** Compact 12px paper leaves separated by 10px gaps.
- **Background:** Opaque white active paper or completed neutral.
- **Shadow Strategy:** No card shadow; one low-contrast hairline contains each leaf.
- **Internal Structure:** Completion/title/formatting rail, timestamp row, flexible checklist-capable writing area, and a centered resize grip.

### Checklist Rows

The checkbox-format action converts the current paragraph into a checklist row. A 14px authored checkbox appears in a reserved gutter. Clicking it changes only that row to muted graphite with a strike-through; unchecking restores active ink. Checklist state persists with the note.

### Card Opacity

Settings exposes four explicit presets: 100%, 85%, 70%, and 55%. Opacity applies to one paper surface, not its text or the entire board, and is layout state rather than a content modification.

### Card Resize Grip

The 18px bottom strip uses a short graphite line as its drag affordance. Mouse drag changes only that card; double-click returns to the default height. Keyboard focus exposes the same control through the arrow keys, with `Shift` for a larger step. Height is saved with the note.

### Inputs / Fields

- **Title:** Borderless and transparent at rest; a 2px bottom rule appears on focus.
- **Body:** Borderless transparent rich-text canvas.
- **Disabled:** Completion makes title and body read-only and reduces text contrast without hiding content.

### Completion Rail

The native checkbox carries a clear `완료` label on every card. Checking it changes only that card to the completed palette and disables its formatting; unchecking restores white paper and editability.

## Do's and Don'ts

### Do:

- **Do** keep all notes inside one scrollable board window.
- **Do** keep the outer board and inter-card gaps fully transparent.
- **Do** show created and modified date and time on every card.
- **Do** keep writing as the largest uninterrupted region of every card.
- **Do** express completion across one whole card and keep it reversible.
- **Do** label destructive actions explicitly and place permanent deletion behind a confirmation.
- **Do** preserve a visible keyboard focus border on every compact control.

### Don't:

- **Don't** add a permanent full-size formatting ribbon.
- **Don't** introduce selectable card background colors; active cards remain white.
- **Don't** make hiding a memo visually or behaviorally equivalent to deleting it.
- **Don't** open a separate top-level window when a note is added.
- **Don't** introduce shadows on individual memo cards inside the board.
- **Don't** add a full-window backdrop or outer-board shadow.
