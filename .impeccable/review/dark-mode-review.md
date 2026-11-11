# Appearance review · v0.1.1

11 November 2026 · Operate surface · refinement of the existing map/evidence
layout and river-embankment direction. The original v0.1.0 design extraction and
two-fix verdict remain historical records; current appearance evidence is the
checksummed v0.1.1 browser run and the inspections described here.

| Measurement | Before: Light | After: Light | After: Dark |
| --- | --- | --- | --- |
| Taste inspector failures / warnings | 0 / 1 | 0 / 1 | 0 / 1 |
| Main heading lines at 1440 / 768 / 390 px | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 |
| Main heading size at those widths | 28 / 25 / 24 px | 28 / 25 / 24 px | 28 / 25 / 24 px |
| Loaded face | Manrope Variable | Manrope Variable | Manrope Variable |
| Frame / work surface | Water grey / white | Water grey / white | #111111 / #181818 |
| Horizontal overflow | 0 | 0 | 0 |

The warning concerns five geographic/data hues. They encode environmental
evidence, categorical risk and verified road restrictions; collapsing their
meanings to satisfy a four-series chart rule would remove information.
The inspections use the unmodified skill inspector with the browser's actual
system-dark setting. Full reports are exported as ui-inspection-light.json and
ui-inspection-dark.json under outputs/evidence/.

The browser acceptance has 14 passing workflow checks and 62 screenshots:
31 matched Light/Dark states at 1440, 1024, 390 and 320 px. It records no
uncaught JavaScript errors, horizontal overflow or loading captures. Each theme
passes 23 recorded contrast pairs. The smallest ordinary-text pair is 4.522:1
in Light and 4.604:1 in Dark; the smallest field-stroke pair is 3.198:1 and
3.260:1 respectively. These measured pairs and keyboard checks do not substitute
for a full human accessibility evaluation.

All twelve final inspector screenshots were opened, including every desktop,
tablet and phone fold and contact sheet in both themes. The latest dark browser
captures for the 320 px layout, mobile navigation, report form, alerts, feed
outage, moderator login error and withdrawal confirmation were also opened.
They preserve legible text, field boundaries, visible unknown hatching, route
and hazard keys, clear actions and the original responsive composition.
The source lint has no failures and four warnings for legitimate temporary
overlay shadows or explicit box-shadow removal. The recorded detector is [];
documentation-only changes did not require another detector run.

ROUND 1

Seen in one second: the bounded flood map beside its selected area's evidence.

Idea (one sentence): environmental warnings stay attached to their place,
freshness and supporting observations in either appearance.

Live thing: select an area, inspect its readings, report an observation or
request a route; the map and evidence use the same record.

Layout words by section: title=action row / summary=divided figures /
map=map-and-evidence split / history=chart-and-observation split /
phone=stacked map, evidence and history.

Scores: design 8 · usability 8 · creativity 7 · content 8 → overall 7.8

Caps applied: creativity capped at 7 for a familiar map/evidence composition.
The app-screen rules apply; marketing photography and decorative motion are
not requirements of this Operate surface.

Top three problems (most visible first), each with the screenshot it shows in and the fix:

No material appearance defects were found in this final round. Stop after one
round; preserve the established layout and data wording. Human phone testing,
five consenting usability testers and local-language review remain open in
docs/REMAINING_TASKS.md rather than being inferred from screenshots.

disposition: ship appearance update for the synthetic demo
