# Implementation Guide: Adding the Help Portal FAB Button

This document outlines the exact steps and code required to replicate the addition of the "Help Portal" Floating Action Button (FAB) on the main dashboard of the West Bengal Promise Tracker.

## Overview
The goal was to add a circular help button (🤝) next to the existing Home button (🏠) in the bottom-right corner of the screen, linking to `help.html`.

---

## Step 1: Update the CSS (`v2/css/style.css`)

We need to add the shared styles for circular buttons, define the layout for the side-by-side row, and specify the individual button aesthetics.

### 1.1 Update Shared Button Styles
Search for `.fab-submit, .fab-home` and include `.fab-help`. We also force `text-decoration: none !important` to ensure no underlines appear on the emoji link.

```css
.fab-submit, .fab-home, .fab-help {
  font-family: 'Space Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  text-decoration: none !important; /* Prevents link underlines */
  box-shadow: 0 4px 20px rgba(26, 18, 8, 0.2);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
}
```

### 1.2 Define the Layout Row
Add the `.fab-row` class to ensure the circular buttons sit horizontally.

```css
.fab-row {
  display: flex !important;
  flex-direction: row !important;
  gap: 12px;
  justify-content: flex-end;
  width: auto;
}
```

### 1.3 Add Help Button Specifics
Define the background, border, and size to match the Home button.

```css
.fab-help {
  background: var(--surface); /* White background */
  color: var(--ink-blue);
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 1px solid var(--rule); /* Light grey border */
  font-size: 20px;
  cursor: pointer;
}

.fab-help:hover {
  background: var(--paper-warm);
  border-color: var(--saffron);
  color: var(--saffron);
}
```

### 1.4 Update Mobile Responsiveness
Ensure the buttons scale down on smaller screens (around line 1327).

```css
@media (max-width: 600px) {
  .fab-row {
    gap: 8px;
  }
  .fab-home, .fab-help {
    width: 42px;
    height: 42px;
    font-size: 16px;
  }
}
```

---

## Step 2: Update the HTML (`v2/index.html`)

Modify the `fab-container` (usually near the bottom of the file) to wrap the circular buttons in the new row div.

```html
<!-- ===== FLOATING BUTTONS ===== -->
<div class="fab-container">
  <div class="fab-row">
    <!-- New Help Button -->
    <a class="fab-help" href="help.html" title="Help Portal — Support Bridge">
      🤝
    </a>
    <!-- Existing Home Button -->
    <button class="fab-home" id="fab-home" title="Back to Top">
      🏠
    </button>
  </div>
  <!-- Submit Button remains below -->
  <a class="fab-submit" href="https://tally.so/r/ja5B74" target="_blank" rel="noopener">
    ✏ Submit An Update
  </a>
</div>
```

---

## Summary of Changes
1.  **Structure**: Created a `fab-row` inside `fab-container`.
2.  **Style**: Matched the background (`var(--surface)`) and hover state of the Help button to the Home button.
3.  **Behavior**: Linked the 🤝 icon to `help.html` and added accessibility titles.
