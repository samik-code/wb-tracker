# Update Rules — BJP Sarkar Promise Tracker (West Bengal)

> These rules govern how AI agents should update `index.html` when given new source links or information. Follow them strictly to maintain accuracy, neutrality, and source integrity.

---

## 1. Source Hierarchy (Strict)

Only these source tiers qualify as evidence for updating a promise status:

| Tier | Source Type | Example |
|------|------------|---------|
| **1 (Gold)** | Official government gazette / government order (GO) | Gazette notification PDF, official order |
| **2** | State government press release / official cabinet statement | CM's post-cabinet press briefing |
| **3** | PTI / ANI wire reports carried by national publications | Business Standard, The Hindu, Indian Express, Hindustan Times, Economic Times, Live Mint |
| **3** | Credible regional publications (English or Bengali) | The Telegraph India, Anandabazar Patrika |

**Disqualified sources (never use):**
- Social media posts (Twitter/X, Facebook, WhatsApp forwards)
- Party politician quotes without corresponding official action
- YouTube videos or TV news transcripts alone
- Websites without a clear editorial standard or byline

---

## 2. Status Definitions

This tracker uses a 4-stage pipeline:

```
Pending → In Progress → Fulfilled → (optionally: On Paper / On Ground)
```

| Status | CSS class | When to apply |
|--------|-----------|---------------|
| **Pending** | `pending` | No credible action reported yet |
| **In Progress** | `inprogress` | Any credible news report, cabinet statement, or official announcement showing the government has initiated or is actively pursuing the promise — a source link is required |
| **Fulfilled** | `done` | A formal document exists (gazette, bill enacted, official order) OR the scheme is demonstrably operational and verified by Tier 1/2 source |
| **Evaded** | `evaded` | Government action structurally makes fulfilment impossible (e.g. scheme repealed, policy reversed against promise) |

**Optional sub-labels for Fulfilled** (add in update note only when the distinction is meaningful):
- *"✓ Fulfilled — On Paper"* — formal document exists but real-world impact not yet verified
- *"✓ Fulfilled — On Ground"* — beneficiaries confirmed to be receiving the benefit

If neither label is needed, simply marking `done` with a summary note is sufficient.

> ⚠️ **CRITICAL:** In Progress is intentionally loose — a cabinet announcement, press briefing, or credible news report is sufficient. Fulfilled requires a formal document or verified operational evidence from a Tier 1/2 source.

---

## 3. Updating the 15 Key Promises Cards (kp-cards)

The `#key-15` section at the top uses `kp-card` divs with three possible states:
- `class="kp-card pending"` — badge text: `Pending`
- `class="kp-card inprogress"` — badge text: `◑ In Progress`
- `class="kp-card done"` — badge text: `✓ Done`

Update a kp-card to `inprogress` when the **corresponding promise item** in the detailed sections below has been moved to `inprogress` or `done`.

Update a kp-card to `done` only when **all sub-promises** under that key commitment are fulfilled.

---

## 4. Adding an Update Note to a Promise

When a source confirms partial or full action on a promise:

```html
<span class="update-note">
  [Plain-language summary of what happened, when, and what is still pending.]
  <span class="update-note-sources">
    <a class="source-link" href="[URL]" target="_blank" rel="noopener">
      ↗ [Publication Name] · [Wire if applicable, e.g. PTI] · [Date, e.g. May 11, 2026]
    </a>
  </span>
</span>
```

**Writing the summary:**
- State facts only. No opinion or political framing.
- Always mention: what was decided, when, and what is still pending (e.g. "No gazette notification yet").
- If only a cabinet statement exists, write: *"No official gazette notification published yet — tracking cabinet statement only."*
- Keep it under 3 sentences.

---

## 5. Adding Counter-Evidence or Controversy

Sometimes a promise is marked "In Progress" or "Fulfilled" by the government, but there are credible reports of actions directly contradicting it (e.g., violence occurring despite a "Rule of Law" promise). To maintain neutrality, add a **Counter-Note** below the update note, **inside the `<span class="promise-text">` block**:

```html
<span class="counter-note">
  <span class="counter-label">🛑 Counter-Evidence / Debatable</span>
  [Plain-language summary of the counter-evidence or ground reality that contradicts the promise progress.]
  <span class="update-note-sources">
    <a class="source-link" href="[URL]" target="_blank" rel="noopener">
      ↗ [Publication Name] · [Date]
    </a>
  </span>
</span>
```

**Rules for Counter-Notes:**
- Do not change the promise status to `evaded` unless the government *structurally abandoned* the policy. If the policy exists but enforcement is failing or contested, keep the status `inprogress` or `done` and add a `.counter-note`.
- Always provide a Tier-3 or higher source for counter-evidence. No social media or political opinions.
- Keep the summary factual (e.g., "Despite X, multiple incidents of Y were reported...").

---

## 6. Adding Sources

- Always use **direct article URLs** — never redirect or shortened links.
- Verify the URL loads before adding it.
- Format: `↗ Publication · Wire (if any) · Date`
- Prefer multiple sources (2–4) for high-profile decisions.
- Include at least one English national publication and one regional source where possible.
- Do not add a source if you cannot verify the URL is correct and live.

---

## 7. Updating the Stats & Progress Bar

Stats are **auto-calculated by JavaScript** from the DOM. You do not need to manually update numbers.

**What you must update manually:**
- `id="last-updated-footer"` in the footer — change the date whenever you make any update.
  - Format: `Last updated: 11 May 2026`

---

## 8. Category Badge Counts

Category header badges (e.g. `10 Promises`) are also **auto-calculated by JS** — do not edit them manually.

---

## 9. What NOT to Do

- ❌ Do not mark a promise `done` based on a press conference or tweet alone.
- ❌ Do not add update notes without a source link.
- ❌ Do not remove or alter the original promise text — only append `update-note` spans.
- ❌ Do not add political commentary, party opinions, or editorial framing.
- ❌ Do not guess or construct article URLs — only use verified, working links.
- ❌ Do not edit CSS class names or JS logic without reviewing impact on auto-stats.

---

## 10. Workflow When Given New Links

1. **Use Cloudflare Worker to Fetch Content** — To bypass JavaScript rendering or paywalls, prepend `https://fetch.itachiuchiha.workers.dev/?quest=` to the target URL and fetch the result.
2. **Read the article** — extract all facts, decisions, dates, and names.
3. **Match to promises** — identify which promise items in `index.html` the article addresses.
4. **Check current status** — if already tracked, only update if new information changes the status.
5. **Apply the lowest justified status** — when in doubt, use `inprogress` over `done`.
6. **Add source link** to the `update-note-sources` block.
7. **Update kp-cards** if the corresponding Key Promise card needs a status change.
8. **Update footer date** (`last-updated-footer`).
9. **Do not add the Census or non-manifesto decisions as new promise items** — only track promises from the official BJP *Bhoroshar Shopoth* manifesto.

---

## 11. Neutrality Rules

- This tracker is **non-partisan**. It tracks facts, not opinions.
- Never describe government action as "good" or "bad".
- Never use words like "finally", "disappointingly", "surprisingly".
- If a source is politically aligned (e.g. party press release), cross-verify with at least one independent national publication before using.
- Include sources from different editorial backgrounds when possible (e.g. The Hindu + Anandabazar + Business Standard = good mix).

---

*Last updated: 13 May 2026*
