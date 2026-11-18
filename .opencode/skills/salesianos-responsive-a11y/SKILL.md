---
name: salesianos-responsive-a11y
description: "Trigger: responsive review, accessibility audit, mobile QA, UI acceptance. Verify Salesianos routes across viewports and interaction states."
license: MIT
metadata:
  author: "Salesianos"
  version: "1.0.0"
---

# Salesianos Responsive Accessibility

## Activation Contract

Use for UI acceptance, implementation review, and pre-completion audits.

## Hard Rules

- Validate mobile-first at widths 360, 390, 768, 1024, and 1440.
- Require usable touch targets, keyboard operation, visible focus, programmatic labels, associated errors, and appropriate live regions.
- Reject horizontal page overflow, clipped controls, inaccessible hidden content, and motion that ignores reduced-motion preferences.
- Preserve the documented route flow and business behavior while remediating presentation defects.

## Decision Gates

| Surface    | Required behavior                                                            |
| ---------- | ---------------------------------------------------------------------------- |
| Tables     | Preserve meaning; scroll, stack, or prioritize columns without page overflow |
| Forms      | Keep labels, help, errors, focus order, and mobile input ergonomics          |
| Dialogs    | Trap and restore focus; fit small viewports; provide clear dismissal         |
| Navigation | Expose current location, keyboard access, and usable compact behavior        |

## Execution Steps

1. Trace the route's primary and recovery flows against `contract/` and the route documentation.
2. Check loading, empty, error, validation, success, and permission states.
3. Audit layout and interaction at every required width; test content expansion and zoom-sensitive wrapping.
4. Test keyboard order, focus visibility, names/labels, errors, announcements, touch targets, and reduced motion.
5. Audit responsive tables, forms, dialogs, and navigation for overflow and lost actions.
6. Re-run the audit after fixes and report any unverified browser or assistive-technology behavior.

## Output Contract

Report findings with severity, `file:line`, route, viewport, evidence, remediation, and functional-flow impact. State explicitly when no findings remain and list residual test gaps.

## References

- `contract/`
- `Aplicacion/documentacion/03a-paginas-publicas-y-compra.md`
- `Aplicacion/documentacion/03b-paginas-administrativas-y-operativas.md`
- `Aplicacion/documentacion/05a-matriz-pagina-flujo-endpoint-datos.md`
- `Aplicacion/documentacion/07-guia-para-ui-ux.md`
