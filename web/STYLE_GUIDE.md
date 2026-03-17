# mowen (墨紋) Visual Identity Style Guide

## Concept

Surreal Gentle Magic meets scholarly calligraphy. The aesthetic merges the enchanted mist palette from AmbonMUD with mowen's East Asian typographic identity — dreamlike deep-blue surfaces, lavender accents, and soft luminous depth, grounded by Cormorant Garamond serif headings and washi paper texture. Nothing feels industrial. Nothing feels sharp unless intentional.

**Key principles:**
- Enchanted, not explosive — magic feels ambient and inevitable
- Dreamlike, not chaotic — softness enables focus
- Softly luminous, never harsh — light is diffused, source-ambiguous
- Scholarly warmth — calligraphic typography anchors the ethereal palette

## Color Palette — Surreal Gentle Magic

### Backgrounds (deep mist blues)

| Variable | Hex | Role |
|---|---|---|
| `--bg` | `#1e2538` | Deepest mist — page background |
| `--bg-surface` | `#2a3149` | Cards, panels |
| `--bg-elevated` | `#313a56` | Inputs, nested panels |
| `--bg-hover` | `#3a4468` | Hover states |
| `--bg-inset` | `#181e30` | Recessed areas (bar troughs) |

### Text (moonlit cloud tones)

| Variable | Hex | Role |
|---|---|---|
| `--text` | `#dbe3f8` | Primary — moonlit cloud |
| `--text-muted` | `#aebada` | Secondary — soft fog |
| `--text-faint` | `#7f89a8` | Disabled, placeholders |

### Accent — Lavender (enchanted)

| Variable | Value | Role |
|---|---|---|
| `--accent` | `#a897d2` | Buttons, active states, links |
| `--accent-hover` | `#9585c4` | Hover |
| `--accent-subtle` | `rgba(168,151,210,0.12)` | Tinted backgrounds |
| `--accent-glow` | `rgba(168,151,210,0.30)` | Focus ring glow |

### Secondary — Soft Gold (luminous warmth)

| Variable | Value |
|---|---|
| `--gold` | `#bea873` |
| `--gold-subtle` | `rgba(190,168,115,0.12)` |

### Status (gentle magic tones, not neon)

| Status | Color | Variable |
|---|---|---|
| Success | `#8da97b` (moss green) | `--success` |
| Warning | `#bea873` (= soft gold) | `--warning` |
| Danger | `#c5a8a8` (desaturated rose) | `--danger` |
| Info | `#8caec9` (pale blue) | `--info` |

Each status color has `-bg` (12% opacity) and `-border` (40% opacity) variants.

### Rules

- No neon, no saturated primaries
- No pure black — use deep mist (`#1e2538`) or darker
- Cool undertones dominate, warm accents (gold, rose) balance
- Contrast: WCAG AA minimum (4.5:1 for primary text on surfaces)

### Borders & Shadows

Borders use translucent glass edges, not opaque lines:
- `--border: rgba(151,166,204,0.20)`
- `--border-strong: rgba(151,166,204,0.36)`

Shadows are cool-tinted mist:
- `--shadow-sm: 0 1px 3px rgba(20,24,40,0.3)`
- `--shadow-md: 0 4px 12px rgba(20,24,40,0.4)`
- `--shadow-lg: 0 8px 24px rgba(20,24,40,0.5)`

## Typography

| Role | Font | Weight | Source |
|---|---|---|---|
| Display/headings | Cormorant Garamond | 400, 600 | Google Fonts |
| Body | Inter | 400, 500, 600 | Google Fonts |
| CJK (墨紋) | Noto Serif JP | 400, 600 | Google Fonts (subset: `&text=墨紋`) |
| Monospace | JetBrains Mono | 400, 500 | Google Fonts |

Loaded via `<link>` tags in `index.html`.

### Sizes

- h1: 2.2rem, weight 400 (light calligraphic)
- h2: 1.5rem, weight 400
- h3: 1.15rem, weight 600
- Body: 15px
- Small labels: 0.7rem, uppercase, letter-spacing 0.08-0.12em

### Radii

Slightly softer than typical dark-mode apps:
- `--radius: 8px`, `--radius-md: 10px`, `--radius-lg: 12px`

## Texture & Depth

### Paper grain
SVG `feTurbulence` noise filter overlaid on the viewport at ~3.5% opacity with `mix-blend-mode: overlay`. Provides subtle tactile grain across all surfaces.

### Mist-glow cards
Cards use a top-edge highlight gradient (`rgba(255,255,255,0.02)` to transparent) and inner glow. Glass-edge top border (`rgba(255,255,255,0.04)`). Cards lift on hover with deeper shadow.

### Brush-stroke dividers
Dividers use an SVG `feTurbulence` mask to create irregular, ragged edges — organic, not mechanical.

### Enchanted buttons
Primary buttons have a diagonal light-to-dark gradient overlay with a lavender aura glow shadow. The effect is luminous rather than flat.

### Seal-cut badges
Status badges use near-square border-radius (3px). Running badges emit a faint lavender glow. Compact text with wide letter-spacing.

### Lavender ripple watermark
Dashboard stats row has a concentric-ring radial gradient in faint lavender behind it, echoing the magical aura motif.

### Body vignette
A cool mist glow radiates from the top of the viewport — a blend of lavender and pale blue at very low opacity, creating atmospheric depth.

### Negative space
Generous padding throughout — cards 1.5rem, tables 0.75rem, main content area 2.5rem, max-width 1100px.

## Logo & Favicon

### Logo — Scroll, Brush & Seal
AI-generated illustration: aged parchment scroll with ornate purple/gold finials, turquoise calligraphy brush, and a cinnabar wax seal embossed with 墨 in seal script (篆書). Black background, transparent PNG.

### Favicon — 墨 Seal Character
SVG with deep mist background (`#1e2538`). The vectorized 墨 character in seal script, rendered in lavender (`#a897d2`). Source: `web/src/assets/seal.svg`.

### Navbar brand
The full scroll logo at 2.6rem height alongside the "mowen (墨紋)" wordmark in Cormorant Garamond + Noto Serif JP.

### AI generation prompts

**Logo:**
> Ornate fantasy scroll with turquoise calligraphy brush, aged parchment texture, purple and gold finials. Red cinnabar wax seal at bottom-left with the Chinese character 墨 (ink) embossed in seal script (篆書). Black background. Square format, transparent PNG.

**App icon (512x512):**
> App icon for 'mowen', an authorship attribution tool. Square with rounded corners. Deep blue-purple background (#2a3149). Center: 墨 character in seal script, soft lavender (#a897d2). Gentle magical glow. Dreamlike, scholarly aesthetic.

## Architecture

All styles are implemented as:
- **`web/src/styles/variables.css`** — Design tokens (CSS custom properties)
- **`web/src/styles/global.css`** — Reset, base typography, body texture, vignette
- **`web/src/styles/components.css`** — Shared classes (`.card`, `.badge--*`, `.divider`, `.tag`, etc.)
- **`*.module.css`** — Per-component CSS Modules for scoped styles

No inline React `style={{}}` objects for layout or color — all visual styling lives in CSS.

---

Copyright 2026 John Noecker Jr.
