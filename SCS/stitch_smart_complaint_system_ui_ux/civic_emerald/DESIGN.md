---
name: Civic Emerald
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#3e4947'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#6e7977'
  outline-variant: '#bdc9c6'
  surface-tint: '#006a63'
  primary: '#005c55'
  on-primary: '#ffffff'
  primary-container: '#0f766e'
  on-primary-container: '#a3faef'
  inverse-primary: '#80d5cb'
  secondary: '#006a61'
  on-secondary: '#ffffff'
  secondary-container: '#86f2e4'
  on-secondary-container: '#006f66'
  tertiary: '#004eaa'
  on-tertiary: '#ffffff'
  tertiary-container: '#0165d8'
  on-tertiary-container: '#e4eaff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#9cf2e8'
  primary-fixed-dim: '#80d5cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#00504a'
  secondary-fixed: '#89f5e7'
  secondary-fixed-dim: '#6bd8cb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#005049'
  tertiary-fixed: '#d8e2ff'
  tertiary-fixed-dim: '#adc6ff'
  on-tertiary-fixed: '#001a42'
  on-tertiary-fixed-variant: '#004395'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
  title-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  title-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-sm: 0.75rem
  margin: 1rem
  margin-md: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system delivers a civic-tech experience engineered specifically for urban public governance in Bandar Lampung. The brand personality balances institutional authority, transparency, and welcoming public service. It targets diverse municipal residents—spanning varied ages, socioeconomic backgrounds, and digital literacy levels—alongside municipal civil servants managing operational workflows.

The visual style combines modern, accessible minimalism with tactile, functional clarity:
- **Atmosphere:** Clean, calm, credible, and action-oriented. The interface prioritizes civic accountability over bureaucratic friction.
- **Visual Principles:** High legibility, strict contrast compliance, robust tap targets, and unencumbered layouts that establish direct citizen trust.
- **Cultural Grounding:** Official Indonesian public governance terminology (*Lapor Warga*, *Tindak Lanjut*, *Status Pengaduan*) integrated natively alongside localized, empathetic microcopy.

## Colors

The palette establishes an authoritative civic presence using institutional teal and emerald, anchored by crisp neutral slates and purpose-built semantic status tokens.

- **Primary (`#0F766E` - Civic Emerald):** Used for key app bar elements, primary action triggers, and primary visual anchors. Represents trust, stability, and municipal responsibility.
- **Secondary (`#0D9488` - Vibrant Teal):** Used for interactive highlights, progressive disclosure elements, active selection indicators, and subtle tonal backgrounds.
- **Tertiary (`#3B82F6` - Verified Blue):** Reserved for administrative verification, official municipal badges, and institutional authenticity marks (*Diverifikasi / Petugas Resmi*).
- **Neutral (`#0F172A` - Slate Dark):** Primary typography and icon color, delivering maximum contrast against the clean canvas.
- **Surface Canvas (`#F8FAFC` - Light Slate Canvas):** A crisp, light backdrop engineered to reduce visual fatigue while maintaining distinct separation from pure white elevated surfaces.

### Semantic Status Tokens
- **Diproses / In Progress (`#F59E0B` - Amber):** Indicates ongoing field inspection or departmental triage. Paired with amber-tinted low-opacity fills (`#FEF3C7`).
- **Selesai / Resolved (`#10B981` - Emerald):** Indicates verified case closure and public resolution. Paired with emerald-tinted low-opacity fills (`#D1FAE5`).
- **Perlu Tindakan / Urgent (`#EF4444` - Rose):** Identifies critical public infrastructure hazards, emergency triage, or citizen escalations. Paired with rose-tinted low-opacity fills (`#FEE2E2`).
- **Diverifikasi / Verified (`#3B82F6` - Blue):** Indicates preliminary validation by admin or RT/RW/Lurah. Paired with blue-tinted low-opacity fills (`#DBEAFE`).

### Neutral Supporting Gradients & Borders
- **Border Default (`#CBD5E1` - Slate 300):** Structural card borders and divider lines.
- **Border Muted (`#E2E8F0` - Slate 200):** Subtle item separators and unselected state outlines.
- **Surface Container (`#FFFFFF` - Pure White):** Primary card, sheet, and modal container surface.

## Typography

Plus Jakarta Sans serves across all typographic roles. Designed with contemporary geometric underpinnings and friendly rounded terminals, it delivers exceptional legibility on small-format mobile devices without losing administrative seriousness.

- **Headlines:** Set with confident weights (`600` and `700`) to anchor civic category hubs (*Buat Laporan*, *Pantau Laporan*, *Pengaduan Sekitar*). Responsive tokens (`headline-xl-mobile`, `headline-lg-mobile`) prevent unwieldy line breaks on compact Android and iOS screens.
- **Body:** Engineered with relaxed line heights (`lineHeight: 22px` for `body-md`) to ensure effortless reading of lengthy citizen complaints, official resolution notes (*Catatan Tindak Lanjut*), and multi-step terms of service.
- **Labels:** Reserved for status pills, form field titles, input counters, and system metadata. Tightened letterform tracking maintains structural discipline within high-density lists.

## Layout & Spacing

The layout architecture relies on a fluid grid bounded by strict mobile ergonomic zones:
- **Canvas Margins:** Mobile devices utilize a default outer margin of `1rem` (16px), scaling to `1.25rem` (20px) on wide-screen mobile devices and small tablets.
- **Grid Layout:** Standard mobile views use a single or 2-column fluid grid with `1rem` column gutters. Dashboard cards, report submission forms, and feed items consume the full content width.
- **Touch Target Assurance:** All interactive controls (buttons, chips, list rows, form controls) enforce a strict minimum touch area of 48×48px, preventing mis-taps during one-handed field reporting.
- **Spacing Rhythm:** Structured strictly around an 8px base grid, utilizing `space-xs` (4px) for micro badge gaps, `space-sm` (8px) between related label-input groups, `space-md` (16px) for intra-card content, `space-lg` (24px) for structural section breaks, and `space-xl` (32px) for canvas headers.

## Elevation & Depth

Visual hierarchy uses a refined hybrid of tonal container separation, crisp low-contrast borders, and diffused ambient shadows. High-gloss skeuomorphism and aggressive heavy drops are avoided to maintain government-grade utility.

- **Level 0 (Flat Canvas):** `#F8FAFC` background. Elements resting directly on canvas have no shadow.
- **Level 1 (Interactive Cards & List Tiles):** Surface `#FFFFFF` layered over `#F8FAFC`, bound by a hairline border (`1px solid #E2E8F0`) and reinforced with a soft ambient shadow: `box-shadow: 0 2px 8px -2px rgba(15, 23, 42, 0.05), 0 1px 4px -1px rgba(15, 23, 42, 0.03)`.
- **Level 2 (Active Sheets, Dropdowns & Popovers):** Elevated surface with `box-shadow: 0 8px 24px -4px rgba(15, 23, 42, 0.08), 0 4px 12px -2px rgba(15, 23, 42, 0.04)` and `1px solid #CBD5E1`.
- **Level 3 (Modals & Emergency Alerts):** Floating overlay container with `box-shadow: 0 16px 36px -6px rgba(15, 23, 42, 0.12), 0 8px 16px -4px rgba(15, 23, 42, 0.06)`, anchored over a 40% opacity slate scrim backdrop (`rgba(15, 23, 42, 0.4)`).

## Shapes

The design system incorporates a modern, approachable geometry with softened corners to reduce cognitive tension in grievance reporting:
- **Cards & Primary Modules:** Configured with `rounded-2xl` (16px / `1rem`) corner radii, projecting an approachable and modern civic identity.
- **Input Fields & Buttons:** Configured with `rounded-xl` (12px / `0.75rem`) corner radii, striking a balance between structure and tactile comfort.
- **Badges, Chips, and Avatars:** Employ continuous full-radius pill styling (`9999px`) to distinguish actionable metadata and tracking statuses from container surfaces.

## Components

### Buttons (Tombol Aksi)
- **Primary Civic Button:** Solid `#0F766E` background with `#FFFFFF` text. Minimum height 48px, horizontal padding `space-lg`, border-radius 12px. Active press scales slightly to `0.98` with background darkening to `#115E59`.
- **Secondary / Muted Action:** Pure `#FFFFFF` background with 1.5px border `#CBD5E1`, text `#0F172A`.
- **Floating Action Button (FAB - Buat Laporan):** High-priority circular or expanded pill container (`#0F766E` fill, `#FFFFFF` text and icon), elevated with Level 2 shadow, fixed 16px above the navigation bar.

### Status Chips & Badges (Lencana Status)
- Structured as continuous pills (`rounded-full`) with uppercase/semibold `label-md` typography.
- **Diproses:** `#FEF3C7` background, `#B45309` text, paired with an amber status dot icon.
- **Selesai:** `#D1FAE5` background, `#047857` text, paired with a checkmark badge icon.
- **Perlu Tindakan:** `#FEE2E2` background, `#B91C1C` text, paired with an exclamation alert icon.
- **Diverifikasi:** `#DBEAFE` background, `#1D4ED8` text, paired with an administrative shield icon.

### Form Inputs & Location Pickers (Formulir Pengaduan)
- **Text & Area Fields:** Surface white `#FFFFFF`, height 48px (min), border `1px solid #CBD5E1`, text `body-md` in `#0F172A`. Focused state transitions border to 2px solid `#0F766E` with a 3px outer glow ring of `rgba(15, 118, 110, 0.15)`.
- **Photo Upload Target (Unggah Bukti Foto):** Dotted border `2px dashed #94A3B8`, surface `#F8FAFC`, minimum height 120px with centered icon and instructional text in Indonesian (*"Ketuk untuk ambil foto bukti atau pilih dari galeri"*).

### Complaint Cards (Kartu Laporan Warga)
- Container: Surface white, radius `16px`, border `1px solid #E2E8F0`, padding `space-md`.
- Layout: Header row contains category chip (*Infrastruktur*, *Kebersihan*, *Lampu Jalan*) and status chip. Middle section displays complaint title (`title-md`), description excerpt (`body-md`), and photo thumbnail. Footer includes geocoded address (*Kec. Teluk Betung Selatan*), timestamp, and citizen interaction metrics (vote/dukungan counter).

### Lists & Timelines (Riwayat Tindak Lanjut)
- Vertical progress tracks utilizing status colors for node states. Active progress lines use `#0D9488`, pending segments use `#E2E8F0`.
- List rows maintain a minimum height of 56px with inset dividers (`#E2E8F0`) and explicit tap highlights for accessibility.