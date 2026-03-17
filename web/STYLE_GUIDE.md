# mowen (墨紋) Visual Identity Style Guide

## Concept

The visual language is rooted in the product's name — 墨紋 (ink-print/fingerprint). The aesthetic draws from sumi ink (墨), washi paper (和紙), and cinnabar seals (朱印) to evoke a calligraphy studio rather than a generic dark-mode application.

## Color Palette — Sumi Ink + Cinnabar

### Backgrounds (warm charcoal, not cool blue-black)

| Variable | Hex | Role |
|---|---|---|
| `--bg` | `#141210` | Deepest ink — page background |
| `--bg-surface` | `#1e1b18` | Cards, panels |
| `--bg-elevated` | `#282420` | Inputs, nested panels |
| `--bg-hover` | `#322d28` | Hover states |
| `--bg-inset` | `#0f0e0c` | Recessed areas (progress troughs) |

### Text (aged paper tones)

| Variable | Hex | Role |
|---|---|---|
| `--text` | `#e8e0d4` | Primary — warm off-white |
| `--text-muted` | `#9c9488` | Secondary — faded ink |
| `--text-faint` | `#6b6359` | Disabled, placeholders |

### Accent — Cinnabar/Vermillion (朱)

Replaces the original periwinkle `#7c8cf8`.

| Variable | Value | Role |
|---|---|---|
| `--accent` | `#c8523c` | Buttons, active states, links |
| `--accent-hover` | `#b5442f` | Hover |
| `--accent-subtle` | `rgba(200,82,60,0.12)` | Tinted backgrounds |
| `--accent-glow` | `rgba(200,82,60,0.25)` | Focus ring glow |

### Secondary — Gold (金)

| Variable | Value |
|---|---|
| `--gold` | `#c9a84c` |
| `--gold-subtle` | `rgba(201,168,76,0.12)` |

### Status (harmonized warm tones, not neon)

| Status | Color | Variable |
|---|---|---|
| Success | `#6b9e5e` (sage) | `--success` |
| Warning | `#c9a84c` (= gold) | `--warning` |
| Danger | `#c75050` (cool red, distinct from accent) | `--danger` |
| Info | `#5e8a9e` (slate) | `--info` |

Each status color has `-bg` (12% opacity) and `-border` (40% opacity) variants.

### Borders & Shadows

- `--border: #2e2a25`
- `--border-strong: #3d3732`
- `--shadow-sm: 0 1px 3px rgba(10,8,6,0.3)`
- `--shadow-md: 0 4px 12px rgba(10,8,6,0.4)`
- `--shadow-lg: 0 8px 24px rgba(10,8,6,0.5)`

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

## Texture & Depth

### Paper grain
SVG `feTurbulence` noise filter overlaid on the viewport at ~3.5% opacity with `mix-blend-mode: overlay`. Gives all surfaces a subtle washi paper grain.

### Ink-wash cards
Cards use a top-edge highlight gradient (`rgba(255,255,255,0.02)` → transparent) and inner glow to simulate how ink pools lighter at edges. Cards lift on hover with deeper warm shadow.

### Brush-stroke dividers
Dividers use an SVG `feTurbulence` mask to create irregular, ragged edges like brush strokes, not clean CSS lines.

### Hanko seal buttons
Primary buttons have a diagonal light-to-dark gradient overlay simulating uneven ink transfer of a stamp, plus a warm cinnabar glow shadow.

### Seal-cut badges
Status badges use near-square border-radius (3px) like carved seals, not rounded pills. Smaller text with wider letter-spacing.

### Ink ripple watermark
Dashboard stats row has a concentric-ring radial gradient in faint cinnabar behind it, echoing the favicon's ink-drop motif.

### Negative space (間)
Generous padding throughout — cards 1.5rem, tables 0.75rem, main content area 2.5rem, max-width 1100px.

## Logo & Favicon

### Favicon — Ink Ripple
Hand-crafted SVG: dark charcoal background with 3 slightly irregular concentric elliptical rings in warm off-white (varying opacity) and a solid cinnabar center dot. The rings are offset and rotated slightly to feel brush-drawn, not mechanical.

### AI generation prompts (for future logo work)

**Primary mark:**
> Minimalist logo mark, concentric ripple pattern like a single drop of black ink falling into still water, viewed from above. Three to four elliptical rings radiating outward with organic irregularity — not perfect circles but slightly calligraphic, as if drawn with a brush. Monochrome with subtle warm charcoal tones. Clean vector style. Dark background (#141210). No text.

**App icon (512x512):**
> App icon for 'mowen', an authorship attribution tool. Square with rounded corners. Dark warm charcoal background (#1e1b18). Center: ink ripple pattern in warm off-white (#e8e0d4) with a small solid cinnabar (#c8523c) circle at center. 3-4 ripple rings. Japanese/Chinese ink art aesthetic.

## Architecture

All styles are implemented as:
- **`web/src/styles/variables.css`** — Design tokens (CSS custom properties)
- **`web/src/styles/global.css`** — Reset, base typography, body texture
- **`web/src/styles/components.css`** — Shared classes (`.card`, `.badge--*`, `.divider`, `.tag`, etc.)
- **`*.module.css`** — Per-component CSS Modules for scoped styles

No inline React `style={{}}` objects for layout or color — all visual styling lives in CSS.
