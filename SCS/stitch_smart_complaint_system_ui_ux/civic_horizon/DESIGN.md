---
name: Civic Horizon
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#43474f'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#73777f'
  outline-variant: '#c3c6d0'
  surface-tint: '#3f608c'
  primary: '#002549'
  on-primary: '#ffffff'
  primary-container: '#163b65'
  on-primary-container: '#86a6d6'
  inverse-primary: '#a8c8fa'
  secondary: '#00629d'
  on-secondary: '#ffffff'
  secondary-container: '#7abeff'
  on-secondary-container: '#004c7b'
  tertiary: '#002a29'
  on-tertiary: '#ffffff'
  tertiary-container: '#004240'
  on-tertiary-container: '#34b6b1'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d4e3ff'
  primary-fixed-dim: '#a8c8fa'
  on-primary-fixed: '#001c3a'
  on-primary-fixed-variant: '#254872'
  secondary-fixed: '#cfe5ff'
  secondary-fixed-dim: '#98cbff'
  on-secondary-fixed: '#001d33'
  on-secondary-fixed-variant: '#004a77'
  tertiary-fixed: '#7ef5ef'
  tertiary-fixed-dim: '#60d9d3'
  on-tertiary-fixed: '#00201f'
  on-tertiary-fixed-variant: '#00504d'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: 0em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.03em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system establishes an authoritative, accessible, and highly transparent digital interface tailored for municipal complaint resolution and civic engagement. The audience spans a diverse constituency—from digital-native citizens reporting municipal issues via mobile to city administrators auditing resolution workflows on desktop workstations.

The visual narrative blends **Corporate / Modern** civic dependability with functional **Minimalism**. Every layout and component prioritizes immediate legibility, high visual clarity, and reassuring stability. Interface elements avoid ornamental distractions in favor of structural clarity, high semantic contrast, and crisp informational grouping. The resulting aesthetic instills confidence in public administration while maintaining approachable, civic-minded usability.

## Colors

The palette balances institutional gravitas with dynamic status monitoring:
- **Primary Navy Blue (`#163B65`)**: Anchors administrative authority, navigation bars, prominent action headers, and primary confirmation buttons.
- **Secondary Medium Blue (`#2878B5`)**: Handles active states, secondary interactive elements, links, and informational callouts.
- **Tertiary Civic Teal (`#16A6A1`)**: Reserved for system accents, progress tracks, active status indicators, and positive resolution highlights.
- **Neutral Slate (`#64748B`)**: Drives secondary text, subtle dividers, and structural borders without harsh visual noise.
- **Canvas & Containers**: Canvas defaults to an ultra-light cool slate (`#F5F7FA`), paired with crisp white (`#FFFFFF`) surface cards to ensure layered readability.
- **Functional Semantics**: Standardized against civic triage metrics—Success Green (`#10B981`) for resolved reports, Warning Amber (`#F59E0B`) for pending/escalated tickets, and Critical Red (`#EF4444`) for emergency municipal hazards.

## Typography

Inter serves as the unified typeface across all typographic roles. Its mechanical neutrality, tall x-height, and optimized open counters ensure clear legibility across diverse literacy levels, variable device screens, and translation contexts.

- **Headlines**: Semi-bold to bold weights with tight letter spacing, delivering authoritative structure to public notices, incident titles, and dashboard KPI summaries.
- **Body Text**: Tuned for maximum legibility with comfortable line heights (1.5x ratio) to facilitate rapid scanning of citizen testimonies, legal clauses, and formal municipal responses.
- **Labels & Metas**: Structured tracking and medium-to-semibold weights maintain instant recognition for ticket IDs, category badges, SLA timers, and tabular data.

## Layout & Spacing

The layout structure employs a standard 12-column responsive fluid grid designed to adapt across high-density operational screens and citizen mobile environments:

- **Desktop (>= 1200px)**: 12-column layout with 24px (`1.5rem`) gutters and 32px (`2rem`) margins. Max container width capped at 1360px for administrative dashboards, keeping content within a comfortable horizontal scanning span.
- **Tablet (768px – 1199px)**: 8-column layout with 20px gutters and 24px outer margins. Complaint cards transition to 2-column or full-width layouts.
- **Mobile (< 768px)**: 4-column layout with 16px (`1rem`) gutters and margins. Sidebars collapse into sticky bottom bars or accessible slide-out drawers. Complex multi-column data views reflow into vertical, self-contained incident cards.

Spacing is governed strictly by an 8-point baseline rhythm (using `0.25rem` / 4px sub-increments) to maintain consistent vertical cadences between form fields, incident steps, and metric blocks.

## Elevation & Depth

Visual hierarchy uses a refined hybrid of **tonal containment** and **low-contrast ambient shadows** to prioritize functional clarity over decorative depth:

- **Surface Base (Level 0)**: `#F5F7FA` canvas serves as the foundational backdrop.
- **Surface Elevation (Level 1)**: White (`#FFFFFF`) cards and content panels sit on the canvas, bounded by a crisp 1px neutral border (`rgba(100, 116, 139, 0.16)`) and an ultra-subtle ambient drop shadow (`0 1px 3px rgba(22, 59, 101, 0.04), 0 1px 2px rgba(22, 59, 101, 0.02)`).
- **Interactive Hover & Overlay (Level 2)**: Actionable cards, dropdown menus, and date pickers elevate slightly using `0 4px 12px rgba(22, 59, 101, 0.08)` while the border remains crisp.
- **Modal & System Notices (Level 3)**: Critical confirmation sheets, citizen report confirmation modals, and mobile sheets cast a wide, diffused shadow (`0 12px 32px rgba(22, 59, 101, 0.12)`) alongside a soft semi-transparent backdrop scrim (`rgba(22, 59, 101, 0.4)`).

## Shapes

The design system utilizes a structured, balanced **Rounded** (`0.5rem` / 8px) geometry. This radius softens institutional rigidity without feeling playful or unanchored.

- **Standard Elements (8px / `0.5rem`)**: Applied to buttons, form inputs, complaint status cards, and metric containers.
- **Large Surfaces (16px / `1rem`)**: Applied to primary modal containers, notification banners, and featured municipal announcements.
- **Pills (Full Radius)**: Reserved exclusively for status badges (e.g., "In Progress", "Verified", "Resolved") and citizen identity tag avatars to establish immediate contrast against squared layout blocks.

## Components

### Buttons
- **Primary**: Solid Navy Blue (`#163B65`) background with pure white text, 8px border-radius, `label-lg` typography, and 12px vertical by 20px horizontal padding. Hover darkens to `#0F2947`.
- **Secondary**: Outlined 1.5px with Medium Blue (`#2878B5`), transparent background, and Medium Blue text.
- **Tertiary / Sub-action**: Ghost variant with no border, using Medium Blue text and a light tint background on hover.

### Form Inputs & Textareas
- Built with a minimum target height of 48px to satisfy accessibility standards.
- Surface background is `#FFFFFF` with a 1px border (`#CBD5E1`).
- Focus state triggers a 2px outer ring in Teal (`#16A6A1`) with zero offset, paired with an input border shift to `#2878B5`.
- Error states enforce a 1.5px `#EF4444` border accompanied by persistent assistive text below the field.

### Status Badges & Chips
- Fully rounded pill containers with a 6px vertical by 12px horizontal padding.
- Employs a low-saturation tinted background with high-contrast text:
  - *Resolved*: `#10B981` (10% tint bg) + `#065F46` (text).
  - *In Review*: `#2878B5` (10% tint bg) + `#1E40AF` (text).
  - *Pending Action*: `#F59E0B` (12% tint bg) + `#92400E` (text).
  - *Critical*: `#EF4444` (12% tint bg) + `#991B1B` (text).

### Complaint Cards & Structured Metrics
- **Cards**: Crisp white surfaces bordered by 1px `#E2E8F0` with 8px radius. Includes dedicated slots for Ticket ID, relative timestamp, category badge, excerpt description, and a civic department handler tag.
- **Metric Tiles**: Single-stat metric containers with Navy Blue numeric values (`headline-lg`), coupled with muted slate labels (`label-md`) and accent indicators powered by Civic Teal for percentage changes or SLA milestones.

### Lists & Activity Feeds
- Timeline-based resolution progress lists. Connected vertical nodes utilize 2px lines in Teal or Neutral depending on progress completion.
- List items feature alternating soft background hover states (`#F8FAFC`) and 16px internal padding.

### Checkboxes & Radios
- 20px x 20px controls with a 4px radius (checkbox) or circular format (radio).
- Inactive state uses a 1.5px border (`#94A3B8`). Active states fill with `#163B65` displaying an inset pure white check or dot indicator.