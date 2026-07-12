# Sprint Review Summary

**Date:** 03.07.2026

**Participants:**
- **Maxim Potushinskii** - Team Lead/Interviewer, Speaker 2: Presented weekly progress, quality criteria overview, and architecture updates.
- **Dania Galieva** - Moderator/discussion participant, Speaker 5: Presented updated user stories and sprint backlog.
- **Timur Iusupov** - Moderator/discussion participant, Speaker 4: Presented CP-solver improvements - optional order cost recalculation with loader costs, and architecture restructuring with logging and metrics output.
- **Marsel Tukhvatullin** - Moderator/discussion participant, Speaker 3: Presented the new iterative route optimization algorithm (no PyVRP, parallel vehicle and loader planning with iterative point removal and reinsertion).
- **Anastasia Glinskaia** - Note taker: Took detailed notes during interview.

---

## Sprint Goal Reviewed

Empower managers with full visibility into route economics by delivering cost breakdown metrics (US-016) and fleet utilization optimization (US-006), all within a production-ready v0.3.0 (MVP v2) release on the refined architecture.

---

## Delivered Increment Discussed

- **Progress indicator:** Added stage-based display during calculation so the user can see the algorithm is running and not frozen.
- **Metrics endpoint:** A separate endpoint now returns route metrics and objective function results, allowing the customer to view and compare results with the baseline from the service.
- **Input validation endpoint (`/valid`):** New endpoint accepts an input JSON file, runs validation, and returns which rules are violated.
- **Architecture review:** The team reviewed and cleaned up the project architecture and component connections.
- **Algorithm updates:** Two parallel algorithm versions continue development. The new algorithm version (no PyVRP, parallel vehicle and loader planning with iterative point removal and reinsertion) now outperforms the baseline on 8 out of 10 test cases within 15 minutes. The CP-solver version is being extended to account for loader costs when evaluating optional order removal.
- **User stories updated:** Two user stories taken into the sprint - manager metrics display and vehicle minimization. Two technical tasks added - progress display and validation endpoint.

---

## UAT Results
 
The customer recorded a screen-capture video after the Sprint Review meeting and shared it with the team.
 
**UAT scenarios that passed:**
 
UAT-001 (Server Health Check) - PASS
 
UAT-002 (Start Background Solution) - PASS
 
UAT-003 (Retrieve Solution) - PASS (with comments)
 
UAT-004 (Retrieving Computational Metrics) - PASS
 
UAT-005 (Input Data Validation Check) - PASS
 
**UAT scenarios that failed or need product changes:**
 
No scenarios failed outright. However, UAT-003 was marked as "PASS (with comments)". The feedback from the previous UAT regarding lack of progress visibility has been partially addressed through the new metrics endpoint (UAT-004), but the core progress indication during long-running computations still needs attention. The system shows no stage-based progress - users cannot distinguish between "still computing" and "crashed/frozen" states.
 
**Most important feedback points received:**
 
The customer noted the system shows no progress during long calculations - "check status" returns only "processing" indefinitely without indicating which stage is currently in progress. A stage-based progress indicator is needed showing which algorithm stage is running and how many stages remain.
 
**Resulting PBIs or issues:** [#71](https://github.com/iu-students/route-optimization-platform/issues/71), [#77](https://github.com/iu-students/route-optimization-platform/issues/77), [#78](https://github.com/iu-students/route-optimization-platform/issues/78), [#58](https://github.com/iu-students/route-optimization-platform/issues/58), [#81](https://github.com/iu-students/route-optimization-platform/issues/81)

---

## Quality Evidence Discussed

- The team confirmed that **API key-based access** is implemented.
- **Input validation endpoint** is implemented and will be testable during UAT.
- A new **quality criterion** was added: the algorithm must complete within 15 minutes. This was moved from a user story into a quality requirement.
- A new **documentation quality criterion** was added: the repository structure, project structure, and component interactions must be described in architecture documentation.

---

## Feedback

1. **Progress indicator:** The customer requested a stage-based progress indicator rather than a simple time estimate - showing which algorithm stage is currently in progress and how many stages remain. This helps distinguish between "computing" and "crashed/frozen". 
2. **Calculation history:** The customer suggested an optional feature - a table or dashboard showing all past runs with execution time and objective function value per run. Not mandatory; at the team's discretion.
3. **Multi-route per vehicle:** The customer noted that the problem statement allows a single vehicle to complete multiple routes per shift if time allows. The team had not yet implemented this. The customer suggested analyzing how many short routes are currently generated and whether combining them could reduce vehicle count.
4. **Heavy order separation:** The customer suggested identifying high-volume orders and handling them in a separate routing iteration to allow more small orders to fill remaining capacity.
5. **2-opt and 3-opt heuristics:** The customer suggested exploring these VRP improvement heuristics, either through built-in solver settings or as standalone steps.

---

## Approvals or Requested Changes

- **Approved:** Two new user stories (manager metrics, vehicle minimization) and two technical tasks (progress display, validation endpoint) taken into the sprint.
- **Approved:** API/endpoint-only approach - no visual UI needed.
- **Approved:** UAT format - customer will record independently after the meeting covering both old and new scenarios.
- **Requested:** Stage-based progress indicator showing algorithm stage percentage, not just binary computing/done status. To be implemented closer to the 21st.
- **Requested (optional):** Calculation history feature - table of past runs with execution time and objective function value.
- **Noted:** Multi-route per vehicle logic not yet implemented. Customer suggested investigating short-route frequency before deciding whether to implement it.

---

## Risks


| Risk | Mitigation |
|---|---|
| CP-solver version currently exceeds the 15-minute time limit on some test cases. | Team is restructuring the algorithm and reviewing time budget management. |
| New algorithm version (8/10) is not yet the stable production version. | Continue development; keep current version as fallback until the new version is stable. |
|The stage-based progress bar has not yet been implemented - the system currently shows how many seconds are left. The client requested a step-by-step progress bar instead. | Plan algorithm stages and implement stage-based status reporting. |
| Multi-route per vehicle logic not yet implemented. | Investigate short-route frequency in test data first; implement only if data shows it is beneficial. |

---

## Action Points

- Add calculation history feature to the backlog as an optional item. Consider starting implementation.
- Based on customer suggestions, investigate and evaluate the following algorithm directions before deciding whether to implement:
  - Analyze how many short routes are currently generated across test cases; if there are many, evaluate whether combining them into multi-route per vehicle plans would reduce vehicle count.
  - Analyze volume distribution of orders across test cases; evaluate whether separating high-volume orders into a dedicated routing iteration would improve overall route quality.
  - Look into 2-opt and 3-opt heuristics as potential improvement steps for the current algorithm.
- Replace the current seconds-based progress display with a stage-based progress indicator showing which algorithm stage is currently running and how many stages remain. This addresses the customer's concern that the current display does not help distinguish between a running and a frozen calculation.

---

## Resulting Product Backlog or Scope Changes

- **Added to backlog** Calculation history feature - a table showing all past runs with execution time and objective function value per run. 
- **Scope update:** TT-6 (progress display) to be extended: the current seconds-based display with a 2-minute limit should be replaced or supplemented with stage-based progress, showing which algorithm stage is currently running and how many stages remain.
- **To be evaluated (not yet added to sprint scope):** Multi-route per vehicle - a single vehicle completing more than one route per shift if time allows. This is permitted by the problem statement but not yet implemented. Requires data analysis first (frequency of short routes across test cases).
- **To be evaluated (not yet added to sprint scope):** Heavy order separation - handling high-volume orders in a dedicated routing iteration, separate from small orders, to allow denser packing of small orders and avoid mixing.
- **Added to quality requirements:** Algorithm must complete within 15 minutes (moved from user story). Architecture documentation must describe repository structure, project structure, and component interactions.
- **No scope removals** from the current sprint.
