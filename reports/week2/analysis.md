## Learning points

The team gained valuable insights from the week's activities across multiple areas:

### User Stories
- Writing stories from incorrect user roles leads to rejection during customer validation
- Stories with "Won't Have" priority should not appear in the backlog due to customer needs
- Customer validation revealed that driver interests (reducing responsibility, finishing shift on time) differ from manager interests (resource optimization)

### Prioritization
- The team learned to distinguish between technical feasibility and customer value when assigning priorities
- Must Have stories now focus exclusively on hard constraints (capacity, time windows) and core user needs (pre-planned route)

### Prototyping
- Swagger UI prototype was effective for communicating API design expectations and was approved by the customer

### Interface Design
- A single interface for different users is sufficient because it meets all the requirements of different types of users (optimal routes for drivers and loaders)

### MVP v0 Deployment
The team learned how to:
- Configure a VPS server
- Deploy the product to the server
- Connect two servers using WireGuard

### Customer Validation
- Customer recommended combining trucks and loaders into a single optimization problem instead of greedy assignment
- Customer suggested exploring Assignment Problem + CPSolver/PIP
- Customer approved MIT license for the product
- Customer recommended to fix some user stories

---

## Validated assumptions

### Confirmed assumptions

- We assumed users need API documentation — confirmed during Swagger UI presentation, customer approved the design.
- We assumed MIT license is acceptable — confirmed during customer meeting.
- We assumed MVP can produce non-optimal solutions — confirmed during customer meeting.

### Rejected assumptions
- We assumed greedy assignment of loaders after VRP for trucks is sufficient — rejected after customer recommendation to combine trucks and loaders into one problem.
- We assumed PyVRP is the only algorithm approach to consider — rejected after customer suggested Assignment Problem + CPSolver/PIP as an alternative to explore in parallel.
- We assumed public transcripts are acceptable — rejected after customer requested transcripts not be published in public domain.
- We assumed real-time delivery refusal prioritization is valuable — rejected after technical constraint review: system recalculates once per morning with no dynamic changes.

---

## Needs clarification

Note: some questions remained from last week, because this week we focused on creating mp0, where this knowledge was not required

### Unresolved questions
- How should trucks and loaders be combined into a single optimization problem? (Assignment Problem + route generator + CPSolver needs research)
- Do we need to support multiple routes per vehicle (multiple departures from the warehouse), or can we simplify to one?
- Can time windows overlap in a way that makes it physically impossible for one vehicle to complete all orders (overlapping hard constraints) — what should be done in that case?

### Assumptions needing validation
- That the Assignment Problem + CPSolver approach will produce better integrated solutions than PyVRP
- Is it acceptable to ignore S9 (loader shift density) in the first version? (Assumes this constraint can be safely omitted for MVP)

### Requirements requiring clarification
- Whether the combined trucks + loaders problem has additional constraints beyond standard VRP
- Constraint H12 (route sequence) — is waiting for the next order allowed (if you arrive before the time window), or is it prohibited?

### Constraints to verify
- Will there be limits on memory usage (RAM) or CPU time?

### Technical risks
- PyVRP may not handle the combined trucks+loaders problem well
- MVP may produce a non-optimal solution, but customer might expect better results
- Alternative research (Assignment Problem, CPSolver, PIP) may distract from MVP delivery
- Real data may reveal edge cases not covered by synthetic tests

---

## Planned response

How learning points will affect MVP v1:

### User Story Changes

| Learning Point | Response | Affected Stories |
|----------------|----------|-------------------|
| Stories with wrong role rejected | Rewrite stories from correct user perspective | US-09 → US-13, US-05 → US-12 |
| "Won't Have" stories shouldn't be in backlog | Remove all Won't Have stories | US-01, US-04, US-07 |
| Drivers want pre-planned routes, not maps | Replace map story with route receipt story | US-01 (removed) → US-11 (added) |
| Time windows serve driver interests | Rewrite from driver perspective | US-09 (removed) → US-13 (added) |

### MVP v1 Scope

Keep only Must Have stories for MVP v1:
- US-10: Account for vehicle capacity
- US-11: Receiving a pre-planned route
- US-13: Respecting time windows to finish shift on time

Based on what the team learned this weak, we will make the following changes to MVP v1:

**Algorithm.** The customer recommended combining trucks and loaders into a single optimization problem instead of using greedy assignment. In parallel to PyVRP, we will optionally explore the Assignment Problem + CPSolver approach as the customer suggested.

**Testing.** We learned that synthetic tests are not enough. The customer asked us to use real data, so we will start testing VRP on real scenarios this week.

**Deployment.** The team learned how to configure a VPS server, deploy the product, and connect two servers using WireGuard. We will continue using this setup for MVP v1.

---
