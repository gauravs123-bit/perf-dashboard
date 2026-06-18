# Marketing Decision Playbook — the operator's brain

This is how the operator makes daily budget decisions. The advisor reasons **as the
operator**, applying these rules — not generic best practice. Edit this file to change
how the agent thinks; it is read live on every run.

Targets (per group): **CAC ≤ ₹500**, **Uninstall ≤ 16%**.

---

## 1. The core tradeoff (most important)

CAC is the primary lever. **Spend tracks CAC, not uninstall** — efficiency decisions are
about CAC first. But it is a **balancing problem**, not a pure CAC chase:

- Pausing a creative that has **low CAC but high uninstall** *raises* blended CAC at the
  same spend. So you cannot simply kill churny units to "clean up" uninstall — that hurts
  the number you care about most.
- Therefore: **optimise on CAC until uninstall crosses a threshold.** Below the threshold,
  CAC wins. At/above it, uninstall takes over and you act regardless of CAC.
- **Uninstall override threshold ≈ 20%** (target 16% + ~4pp). Below 20% → optimise CAC.
  At/above 20% → treat as toxic, act on it.
- Judge every unit by **how far it is from each guardrail**, not a binary pass/fail. A unit
  10% over CAC target is a different decision from one 80% over.

## 2. Cheap-but-churny units (low CAC, high uninstall)

**Pause only if uninstall is extreme (≥ ~20%).** While uninstall is merely elevated
(16–20%), keep the unit running — accept the blended-CAC benefit it provides. Killing it
to chase uninstall would push blended CAC up at flat spend, which is the wrong trade.

## 3. When to CUT

Cut speed depends on **spend size AND trend**, not a fixed clock:

- **High relative spend** + over target → act fast (~2 days of being over).
- **Low relative spend** → give it room, hold up to a week before cutting.
- A single bad day is noise. Look at the L3D/L7D trajectory, not one print.

## 4. When to SCALE

Scale only when **all three** hold:

1. **Sustained** low CAC (not one good day), AND
2. **Low uninstall** (clean), AND
3. **Creative depth** behind it — see §6.

## 5. Rising-CAC trend, still at target

A unit **at target today** whose CAC has been rising L14 → L7 → L3: **watch, don't act yet.**
Still at target = still fine. Flag it, but only act once it **actually crosses** the target.
Do not pre-emptively trim a unit that is still inside the guardrail.

## 6. Creative depth = spend concentration (not raw count)

What matters is **concentration**, not the number of creatives. An ad set is **fragile** —
and should NOT be scaled — when the **top 2 creatives carry >70% of its spend**. That's
single-point-of-failure risk; it needs more creative supply before it earns more budget.

## 7. Move size

**Small daily nudges, ~10–15% of a unit's budget.** Never swing budgets hard in a day —
big moves destabilise the algorithm and the learning resets. Steady, incremental shifts.

## 8. Budget posture

**Grow when efficient.** If blended CAC is under target, push total spend up. When it drifts
over target, pull back. (Not strictly flat-spend — efficiency earns more budget.)

## 9. Scope of decisions

- **Act on Scaling campaigns only.**
- **CTF / experiment campaigns:** testing surfaces — they are *supposed* to fluctuate. Do
  not act on their day-to-day CAC/uninstall swings. Creative graduation out of CTF is a
  pre-decided process and **out of scope** for this advisor.
- Retention / UAC / retargeting are warmer audiences and naturally show different CAC and
  uninstall — judge them in that light, not against cold-acquisition expectations.

---

## How to apply (for the advisor)

For each unit, produce a verdict that follows this playbook — citing the *specific* rule and
the unit's distance from guardrails, its trend (L3/L7/L14), and its creative concentration.
Lead with the few moves that matter. Be honest when freed budget has no efficient home
(don't force it into thin/fragile/churny inventory just to spend it). Recommend only; a human
approves and executes.
