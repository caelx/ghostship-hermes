## 1. Backend Payload Expansion

- [ ] 1.1 Inventory the current dashboard home payload and map the existing runtime facts into grouped feature sections
- [ ] 1.2 Extend the dashboard backend to emit generic grouped sections for runtime, paths, profiles, model path, auxiliary overrides, and env-backed capability presence
- [ ] 1.3 Add grouped payload support for memory, security, browser, messaging, and conditional router enrichment without exposing secret values

## 2. Generic Home Rendering

- [ ] 2.1 Refactor the home view renderer to consume grouped sections instead of hardcoded large runtime/provider/profile panels
- [ ] 2.2 Add generic profile rendering that works for discovered profile lists without hardcoded profile names or counts
- [ ] 2.3 Add graceful fallback handling for missing optional sections and unknown future fields within existing groups
- [ ] 2.4 Make terminal tab creation and removal optimistic in the UI so tabs appear immediately on open and disappear immediately on close while backend `ttyd` lifecycle work continues asynchronously

## 3. Responsive Card Layout

- [ ] 3.1 Replace the current fixed home-grid panel layout with a smaller modular card system that auto-flows across viewport sizes
- [ ] 3.2 Break the home view into feature-oriented cards for runtime, profiles, models, auxiliary tasks, memory, security, browser, messaging, env presence, and router details when present
- [ ] 3.3 Verify the new layout remains readable when sections appear, disappear, or grow with additional runtime data
- [ ] 3.4 Apply a more distinctive futuristic Hermes visual system with purposeful animations for section reveals, status changes, and terminal-tab transitions

## 4. Validation And Documentation

- [ ] 4.1 Update dashboard tests or smoke coverage for grouped payload rendering, generic profile handling, and conditional router enrichment
- [ ] 4.2 Update dashboard documentation and screenshots or examples to describe the new operator-facing observability surface
- [ ] 4.3 Validate the dashboard against the current Hermes image scaffold so the home view accurately reflects the live runtime configuration categories
