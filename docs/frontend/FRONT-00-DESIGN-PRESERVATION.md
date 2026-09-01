# FRONT-00 Design Preservation

Source: `EPD_Front.zip`, with `EPD/core.css` and the five exact HTML pages named
in `FRONT-00-VISUAL-REGRESSION.md`.

The migrations preserve the 1280 px canvas, public/internal headers, internal
sidebar, five-section home composition, login two-column layout, dashboard
profile plus eight-card density, communication list/chat split, abstimmungen
information callout, system typography, accent `#5c3d3d`, surfaces, borders,
8/14 px radii, spacing rhythm, and principal content positions.

Deliberate visible differences:

1. A yellow candidate banner precedes each fixture.
2. Source claims such as live identity, encryption, counts, results, and login
   are marked as static fixtures or disabled where leaving them active-looking
   would misrepresent backend state.
3. A blue 3 px focus ring and minimum 44 px interactive targets are required.
4. Status includes text and a marker rather than color alone.
5. Mobile navigation is horizontally scrollable or stacked without clipping.
6. Tables use a labelled, focusable horizontal-scroll region.
7. The login form is disabled because authentication is out of scope.
8. The communication composer is disabled because messaging is out of scope.
9. Legal/authority notices explicitly state non-activation.

No brand, palette, page hierarchy, major section, or business function was
redesigned.

## Baseline review

All five originals and migrated fixtures were rendered and compared at mobile,
1440×900, and 1920×1080 before approving the 15 PNG baselines. Public header and
navigation, internal header/sidebar, section order, typography hierarchy,
spacing rhythm, card grids, buttons, login fields, communication list/chat, and
the abstimmungen information composition remain recognizably aligned.

The reviewed differences are exactly the nine items above. In particular, the
additional candidate/non-activation notices increase vertical height on some
fixtures; mobile layouts deliberately reflow rather than reproduce the source's
clipped desktop canvas; disabled controls accurately expose missing backend
behavior. No difference was accepted merely because it was current output.
