---
name: Floodline
description: "A daylight map and evidence sheet for a synthetic flood pilot."
colors:
  ground: "#edf3f5"
  surface: "#ffffff"
  raised: "#f6f8f8"
  active: "#e3ebed"
  border: "#e2e9eb"
  rule: "#eaf0f1"
  control: "#b9c8cd"
  text: "#21343d"
  muted: "#586a73"
  faint: "#5c6d75"
  primary: "#21343d"
  primary-hover: "#38515c"
  accent: "#087f82"
  selected-map: "#185a64"
  positive: "#246755"
  negative: "#a73537"
  warning: "#805d11"
  status-positive-bg: "#e7f1ec"
  status-negative-bg: "#f8e8e7"
  status-warning-bg: "#f9efd6"
  status-neutral-bg: "#edf1f2"
  status-neutral-text: "#52666e"
  map-ground: "#e5edef"
  map-low: "#d4e7e7"
  map-elevated: "#f0dca6"
  map-high: "#dfb1ad"
  map-unknown: "#e4e8e8"
  unknown-hatch: "#a3b3b7"
  map-river: "#9fc5c5"
  map-park: "#c9d9d9"
  map-road: "#7e969c"
  gauge-track: "#dde8e9"
  gauge-stale: "#81969e"
  error-bg: "#fcf5f4"
  error-border: "#ead8d7"
  error-text: "#8d3235"
typography:
  headline:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "28px"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.028em"
  headline-compact:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "25px"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.028em"
  headline-phone:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "24px"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.028em"
  title:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "16px"
    fontWeight: 650
    lineHeight: 1.35
  title-small:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "15px"
    fontWeight: 650
    lineHeight: 1.4
  body:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.55
  body-small:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.55
  form-phone:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "13px"
    fontWeight: 650
    lineHeight: 1.55
  action-label:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.55
  caption:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.55
  value:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "26px"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "-0.015em"
  area-value:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "25px"
    fontWeight: 600
    lineHeight: 1.2
  gauge-value:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.4
  button:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.4
  status:
    fontFamily: "'Manrope Variable', 'Manrope', sans-serif"
    fontSize: "12px"
    fontWeight: 650
    lineHeight: 1.3
rounded:
  card: "12px"
  control: "6px"
  chip: "4px"
  sheet: "16px"
  gauge: "2px"
spacing:
  gap: "16px"
  card-pad: "20px"
  pad: "24px"
  small-gap: "4px"
  control-gap: "8px"
  inline-gap: "10px"
  field-gap: "7px"
  compact-pad: "12px"
  evidence-pad: "18px"
  sheet-inset: "8px"
  pad-compact: "20px"
  pad-phone: "18px"
  pad-wide: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    padding: "9px 13px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-primary-phone:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    padding: "10px 13px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    padding: "9px 13px"
  button-secondary-hover:
    backgroundColor: "{colors.raised}"
  button-text:
    textColor: "{colors.text}"
    typography: "{typography.action-label}"
    padding: "0px"
  button-text-hover:
    textColor: "{colors.accent}"
  button-icon:
    textColor: "{colors.muted}"
    rounded: "{rounded.control}"
    height: "32px"
    width: "32px"
  button-icon-hover:
    backgroundColor: "{colors.active}"
    textColor: "{colors.text}"
  button-icon-phone:
    textColor: "{colors.muted}"
    rounded: "{rounded.control}"
    height: "44px"
    width: "44px"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.body-small}"
    rounded: "{rounded.control}"
    padding: "10px"
  field-phone:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.form-phone}"
    rounded: "{rounded.control}"
    padding: "10px"
  area-select:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.body-small}"
    rounded: "{rounded.control}"
    padding: "0px 8px"
    height: "34px"
  area-select-phone:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0px 8px"
    height: "44px"
  nav-link:
    textColor: "{colors.muted}"
    typography: "{typography.body-small}"
    rounded: "{rounded.control}"
    padding: "11px 12px"
  nav-link-active:
    backgroundColor: "{colors.active}"
    textColor: "{colors.text}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "11px 12px"
  tab-active:
    textColor: "{colors.text}"
    typography: "{typography.label}"
    padding: "10px 0px 12px"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.card}"
    padding: "{spacing.card-pad}"
  evidence-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.card}"
    padding: "{spacing.evidence-pad}"
  sheet:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.sheet}"
    padding: "{spacing.pad}"
  status-monitor:
    backgroundColor: "{colors.status-positive-bg}"
    textColor: "{colors.positive}"
    typography: "{typography.status}"
    rounded: "{rounded.chip}"
    padding: "2px 7px"
    height: "22px"
  status-elevated:
    backgroundColor: "{colors.status-warning-bg}"
    textColor: "{colors.warning}"
    typography: "{typography.status}"
    rounded: "{rounded.chip}"
    padding: "2px 7px"
    height: "22px"
  status-high:
    backgroundColor: "{colors.status-negative-bg}"
    textColor: "{colors.negative}"
    typography: "{typography.status}"
    rounded: "{rounded.chip}"
    padding: "2px 7px"
    height: "22px"
  status-unknown:
    backgroundColor: "{colors.status-neutral-bg}"
    textColor: "{colors.status-neutral-text}"
    typography: "{typography.status}"
    rounded: "{rounded.chip}"
    padding: "2px 7px"
    height: "22px"
  gauge-row:
    backgroundColor: "{colors.raised}"
    rounded: "{rounded.control}"
    padding: "{spacing.compact-pad}"
  metrics-strip:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.card}"
    padding: "14px 0px"
---

# Design System: Floodline

## Overview

**Creative North Star: "River-embankment level marks"**

Floodline is a calm, precise information sheet for reading environmental evidence in daylight. A pale water-grey frame holds a white work surface. Manrope gives headings, ordinary web controls and measured figures one consistent voice. Compact labels, comparable rows and modest corners keep the map and its evidence easy to scan.

Depth comes from tone and hairline boundaries. Environmental data carries teal; amber and red describe warning and failure states. Missing evidence has its own words and patterned geometry. The gauge and observation, issue and validity times make the age and meaning of a reading visible alongside its value. These are durable visual commitments drawn from the implementation and the confirmed direction; the synthetic pilot is always labelled.

**Key Characteristics:**

- Water-grey frame, white sheet and flat bordered panels.
- Locally bundled Manrope with compact sentence-case labels and tabular figures.
- Teal environmental evidence with separate amber, red and neutral state signals.
- Patterned unknown areas, plain-language limitations and visible freshness.
- Familiar navigation, keyboard focus and responsive resident forms.

Source extraction: `frontend/src/styles.css`, shared UI and the screens reached by `frontend/src/App.tsx`. The sidecar records each source hash and the eight reviewed captures. Source manifest SHA-256: `5b963177d57ddf902c4c38ad3f05ffe44f948b41b628d29ffa0207606a21721f`.

## Colors

The palette is a cool water-grey ground with dark blue-grey ink and restrained environmental and state colors. Frontmatter values are normative; descriptive names below explain their roles.

### Primary

- **Action Ink** (`primary`): primary reporting, submission and sign-in buttons. It shares the text ink value; primary actions are dark and legible on the light surface.
- **Lifted Ink** (`primary-hover`): the primary button's hover background.
- **Environmental Teal** (`accent`): rainfall bars, current gauge water, a proposed route, the product mark, selected tab underline, caret and focus outline.
- **Selected-Area Teal** (`selected-map`): the selected cell edge and the report-location pin outline.

### Secondary

- **Verified Green** (`positive`, `status-positive-bg`): verified reports, sent deliveries, success notices and the Monitor tag.
- **Warning Amber** (`warning`, `status-warning-bg`): elevated risk, queued delivery and limited data support.
- **Hazard Red** (`negative`, `status-negative-bg`): high risk, rejected reports, failed deliveries and active verified road hazards. Map hazards use a dashed line as well as this color.
- **Map Risk Fills** (`map-low`, `map-elevated`, `map-high`): subdued cell fills for Monitor, Elevated and High. They are distinct from the darker text colors used by their tags.
- **Cartographic Water and Land** (`map-river`, `map-park`): the synthetic river and parks. Their color describes geographic material, not risk severity.
- **Error Sheet** (`error-bg`, `error-border`, `error-text`): an inline error with an alert icon, readable message and optional Retry action.

### Neutral

- **Water-Grey Frame** (`ground`), **White Sheet** (`surface`) and **Quiet Inset** (`raised`): the app frame, work panels and source/gauge/form trays.
- **Active Wash** (`active`): selected and hovered navigation and icon controls.
- **Hairline Edge** (`border`) and **Row Rule** (`rule`): sheet/panel edges and internal dividers. **Control Stroke** (`control`) is stronger so fields and outlined buttons stay identifiable.
- **Blue-Grey Ink** (`text`), **Evidence Grey** (`muted`) and **Caption Grey** (`faint`): primary text, supporting evidence and lower-emphasis annotations. Captions remain readable.
- **Neutral State** (`status-neutral-bg`, `status-neutral-text`): Unknown, pending, expired, resolved, duplicate and cancelled labels. A pending observation does not inherit verified styling.
- **Map Ground** (`map-ground`) and **Road Grey** (`map-road`): the bounded map background and ordinary road lines.
- **Unknown Ground and Hatch** (`map-unknown`, `unknown-hatch`): missing or stale cell evidence. A diagonal hatch and dashed edge preserve meaning without color.
- **Gauge Track and Stale Water** (`gauge-track`, `gauge-stale`): the level scale and a retained reading whose observation is absent or older than the implemented freshness window.

**The Evidence Color Rule.** Keep ordinary navigation and controls neutral. Use teal for environmental data and amber/red/green for their documented state meanings; the map's geographic and severity colors retain their distinct roles.

**The Unknown Rule.** Missing or stale evidence stays visibly unknown. Use the neutral tag and hatched cell; show "Unavailable" or "Not estimable" where a current value cannot be supported.

## Typography

**Display and Body Font:** locally bundled Manrope Variable, with Manrope and sans-serif fallbacks. There is no separate decorative display or mono family in the implemented system.

**Character:** open, compact and steady. Sentence case, moderate semibold weights and slightly tightened page titles give hierarchy without ceremonial labels. Units and supporting timestamps stay smaller than measured values.

### Hierarchy

- **Headline** (`headline`, `headline-compact`, `headline-phone`): page title; semibold (650), tight leading (1.2) and tracking. The desktop size steps down at the observed compact and phone breakpoints.
- **Title** (`title`, `title-small`): panel headings and subordinate explanations; semibold (650) with more relaxed leading.
- **Body** (`body`, `body-small`): the global reading size and compact evidence copy. Component explanations use leading (1.5); report and alert descriptions use (1.65) and wrap long strings anywhere. Title descriptions stop at (72ch); report descriptions at (74ch).
- **Labels and actions** (`label`, `action-label`, `button`): short sentence-case field labels, active navigation and actions. Control labels carry their weight, not an oversized type treatment.
- **Caption** (`caption`): source statements, dates, units and chart labels. Small text is regular and remains part of the reading hierarchy.
- **Measured values** (`value`, `area-value`, `gauge-value`): summary totals, relative area index and local gauge reading. Phone summary values reduce to (24px); the demo-time summary also uses (24px).
- **Phone form text** (`form-phone`): ordinary editable fields rise to (16px) at the phone breakpoint. The area selector uses the body size; coordinate fields retain the source's smaller (14px) exception.
- **Status** (`status`): compact, semibold words with a dot or check when appropriate; labels are never color-only.

**The Comparable Figures Rule.** Use tabular numerals for totals, timestamps, rainfall, the relative index and gauge marks. Keep the unit and observation context visible with the number.

## Layout

The wide shell uses a labelled sidebar (224px), an uninterrupted tinted scope bar (48px) and a white sheet inset from the right and bottom (8px). The sheet has a hairline edge, generous corners and a fluid content width. At the checked desktop viewport (1440 × 900), its inner width is (1158px): a map (802px), a gutter (16px) and an evidence column (340px). The rainfall/report row follows those same column lines. Main content padding is the `pad` token; panels use `card-pad`, with compact evidence padding and zero-padded map containers.

The rhythm is based on repeated component gaps (16px), content padding (24px) and panel padding (20px). It is not a strict eight-pixel-only scale: labels, compact controls and evidence facts use the extracted smaller gaps. Sections do not create additional nested card levels or different gutters for related rows. The status strip is one divided container with four equal cells on desktop.

| Source breakpoint | Observed behavior |
| --- | --- |
| At least 1600px | Canvas padding increases to (32px); the base map height becomes (380px), while the map/evidence flex arrangement can grow it to the evidence height. |
| At most 1190px | Sidebar narrows to (208px), canvas padding becomes (20px), the evidence/report columns narrow to (300px), and the page title becomes the compact headline. |
| At most 1050px | Sidebar yields to ordinary menu navigation, the right/bottom sheet inset disappears, and the work surface uses rounded top corners (12px). The scope bar remains (48px). |
| At most 760px | Map and evidence stack; rainfall precedes reviewed reports. Report, route, alert, data and review columns also stack. The evidence panel temporarily uses two internal columns, and report-location stickiness ends. Canvas padding becomes (18px). |
| At most 480px | The top bar becomes (52px); the scope breadcrumb and top-bar time are hidden. The page title and its action wrap, the summary becomes a two-by-two strip, and area evidence becomes a single reading column. Ordinary buttons and icon controls have a (44px) minimum target; form text becomes larger. The overview map is (300px) high, with a wrapping legend. |

At the checked tablet width (1024px), navigation is in the menu while the map and (300px) evidence column remain alongside each other. At (390px), the map precedes full-width evidence, the report form precedes its location map, and the footer stacks. At the minimum supported width (320px), labels, metadata, the title action and legends wrap without horizontal page overflow. The checked full-page captures establish those sizes; new flows still require their own responsive check.

## Elevation & Depth

The frame, sheet, panels, summary strip and map zoom controls are flat. Their tone step and hairline boundaries provide structure; none uses a panel shadow. Raised gauge, image-upload and confirmation trays use a light fill without another elevated card. The two overlay exceptions express temporary depth rather than decorating dashboard panels.

### Shadow Vocabulary

- **Map tooltip** (`0 4px 12px #21343d14`): a transient label over geographic detail. Permanent ward labels have no border, fill or shadow.
- **Moderator dialog** (`0 18px 64px #21343d33`): a modal white sign-in surface. Its backdrop is the corresponding translucent ink (`#21343d66`).

**The Flat Sheet Rule.** Keep the frame, work sheet and ordinary panels free of shadows. Preserve the small tooltip shadow and modal depth when those temporary layers are present.

## Shapes

Corners are gently shaped, not pill-shaped: the sheet, cards, controls, state tags and gauge use their respective frontmatter radius tokens. On smaller screens the sheet rounds only its top corners. Ordinary boundaries are thin (1px); tabs use a selected underline (2px). Map panels clip geographic rendering within their rounded container. The gauge is a narrow, vertically clipped level column, not a circular score ornament.

The selected map cell has a stronger teal edge (2.4px) against ordinary white edges (1.5px). Unknown cells combine a diagonal repeat (7 × 7px) with dashed edges (`4 4`). Active reviewed road hazards use a heavier dashed line (4.5px, `7 5`) and a matching legend. A proposed route is a solid teal line (5px). These geometries convey different information and must remain distinguishable.

## Components

### Buttons

Quiet, direct controls with compact corners and clear words. The primary variant uses Action Ink on White Sheet; the secondary variant is white with a Control Stroke; text actions are unboxed. Frontmatter captures their colors, type and padding. The button minimum height is (36px) on desktop and (44px) on phones; actual height can grow with padding and text. Icon controls are (32 × 32px) before the phone increase. Disabled buttons halve opacity and stop press movement.

Hover changes the background of primary, secondary and icon buttons; text actions turn teal and underline. Primary and icon press feedback moves down (1px), with background and transform transitions (120ms, ease-out). All interactive controls retain the shared focus outline (2px teal, offset 3px). The sidecar carries these behaviors because they are outside the frontmatter's component properties.

### Chips

State words are compact tags, not toggles. They use a small rounded rectangle, measured text, and a dot or verified check. Monitor/verified/sent, Elevated/queued, High/rejected/failed and neutral lifecycle states have the documented color assignments. The map legend removes tag fills and uses risk swatches; Unknown has a dashed swatch and a word. Labels such as pending or expired remain neutral even when a separate road hazard has its own validity.

### Cards / Containers

Panels are white, flat and bordered with Hairline Edge. Standard inner padding uses `card-pad`; evidence uses `evidence-pad`; history and recent-report panels use compact padding (16px 18px). Map panels use no inner padding around the map and apply spacing to their headings, source strip and legend. The divided status strip shares one boundary; internal separators do not create four independent cards. Lists separate observations with the lighter Row Rule and let long evidence text wrap.

### Inputs / Fields

Use visible sentence-case labels, white fields, a Control Stroke, gently curved corners and inner padding (10px). Field groups have a label-to-field gap (7px), a bottom gap (16px) and a minimum field height (38px). Textareas resize vertically and start at (90px). The dedicated area selector is compact on desktop (34px) and taller on phones (44px). Ordinary phone fields use the larger form typography; coordinate inputs retain their documented exception.

Focus is the shared visible outline; caret and native checkbox accent are teal. Errors use an inline alert with a message and optional Retry action. Location errors clear when a landmark, coordinate or map pin changes; unrelated form errors retain their own state. Submission guidance is future tense until the API confirms success. Image evidence remains optional and supports a text-only report. A successful save is shown through a dismissible status notice, not through a prematurely saved label.

### Navigation

Navigation uses familiar labelled anchors with small inline line icons. Active and hovered sidebar rows use Active Wash; the active row adds stronger ink, weight and a trailing chevron. The six destinations remain ordinary screen choices. The mobile menu is a native dialog with labelled close control, focus containment, Escape dismissal, scroll lock and focus restoration to its trigger. It closes on return to a desktop layout. Its phone padding respects safe-area insets.

Secondary screen tabs are text buttons above a hairline rule. The active tab adds a teal underline (2px) and semibold text; tabs can scroll horizontally. Keep the main navigation and tabs visually distinct. The visible-on-focus skip link reaches the main work surface.

### Map, Gauge and Freshness

The bounded map and selected-area evidence use the same risk record. Map clicks have an ordinary area-selector alternative; evidence lists provide the text path to values, reasons and source times. Synthetic geography and optional OpenStreetMap tiles are labelled. Scroll-wheel zoom is disabled, map resize fits without animation, and touch behavior permits vertical page movement. Project geometry, rainfall charts and gauges are rendered from code/data; they are not generated raster artwork.

The level column is (17px) wide and (68px) tall, with marks at 8, 6, 4, 2 and 0. It fills from the bottom according to a clamped (0–8m) local demo scale. Current water is translucent teal; absent or more-than-one-hour-old observations use Stale Water and an explicit "stale" suffix. The text value and observation date carry the meaning; the scale is hidden from assistive technology. The synthetic datum warning distinguishes a gauge reading from road-water depth.

Observation time, issue time and validity stay attached to evidence. Missing values use words or an understated dash rather than a large zero. The page's warning total uses evaluated cells as its denominator and separately names unknown cells. When every cell is unknown, the leading copy says that warnings cannot be estimated and the total says "Unavailable". Retained rainfall and gauge readings keep their original timestamps.

Rainfall history uses six hourly bins from observed records, with teal bars for present values. Incomplete intervals use lower opacity (0.45 rather than 0.9); an absent bin stays blank. The SVG has a text alternative naming each bin and its value or missing observation. Threshold risk and verified observations have separate wording and visual keys.

### Motion and Feedback

Motion is limited to short control feedback and the map library's native behavior. Loading rows and the initial map state are static; no decorative animation is required. With reduced motion requested, animations and transitions are disabled, scrolling is automatic, and Leaflet's animated zoom transition is removed. Shared interaction styles suppress tap flashes, use direct touch activation on buttons/selects/labels, and keep disabled actions legible.

## Do's and Don'ts

### Do:

- **Do** reuse the water-grey frame, white work sheet and flat panel hierarchy.
- **Do** keep Manrope, sentence-case labels and tabular figures consistent across screens.
- **Do** attach units, observation times, source meaning and validity to environmental values.
- **Do** show Unknown with both a word and patterned geography, and keep stale readings visibly retained.
- **Do** provide labelled controls, keyboard focus and a text route through map evidence.
- **Do** preserve the shared gutters and verify resident flows at 1024px, 390px and 320px.
- **Do** use the dedicated warning, failure and lifecycle states after the relevant action or evidence confirms them.

### Don't:

- **Don't** turn missing or stale observations into zero rainfall, an all-clear result or a current estimate.
- **Don't** give the frame, sheet or ordinary dashboard panels decorative shadows.
- **Don't** use teal to imply that an observation is verified, or a risk fill to imply a road is closed.
- **Don't** hide risk, freshness or submission state behind color alone.
- **Don't** display a saved-state confirmation before the submission succeeds.
- **Don't** expand the relative demo index into an asserted flood probability or unlabeled live forecast.
- **Don't** replace standard screen navigation with gestures or map-only interaction.
