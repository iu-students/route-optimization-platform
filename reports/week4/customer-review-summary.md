# Customer Review Summary

**Date:** 26.06.2026

**Participants:**
- **Maxim Potushinskii** - Team Lead/Interviewer, Speaker 3: Presented weekly progress, testing results, and quality criteria overview.
- **Dania Galieva** - Moderator/discussion participant, Speaker 4: Presented updated user stories, sprint backlog, and feedback traceability.
- **Anastasia Glinskaia** - Note taker/discussion participant, Speaker 5: Explained UAT process, testing scenarios, and server availability.
- **Marsel Tukhvatullin** - Moderator/discussion participant, Speaker 2: Presented greedy algorithm improvements and baseline comparison results.
- **Timur Iusupov** - Moderator/discussion participant, Speaker 6: Presented CP-solver-based algorithm (version B), route generation approach, and metric summary.


---

## Sprint Goal Reviewed

MVPv1 modification, developing a different version of the algorithm to solve the problem, and the implementation of US-08 and US-015, release v0.2.0

---

## Delivered Increment Discussed

- **Optional order handling** implemented: unprofitable optional orders are now excluded from the route when fulfillment cost exceeds the penalty.
- **Input validation** in process: JSON input is checked for structure, data types, and business constraints.
- **Three quality criteria** identified: system responsiveness during computation, protection against invalid requests, and API key-based access control.
- **Updated sprint backlog** shared with the customer before the meeting, including JSON file verification and independent loader/truck operation sub-tasks.

---

## UAT Results
 
UAT was not executed live during the Sprint Review meeting. The customer recorded a screen-capture video independently after the meeting and shared it with the team.
 
**UAT scenarios that passed:**

UAT-001 (Server Health Check) - PASS

UAT-002 (Start Background Solution) - PASS

UAT-003 (Retrieve Solution) - PASS (with comments)

**UAT scenarios that failed or need product changes:**

No scenarios failed outright. However, UAT-003 was marked as "PASS (with comments)" and requires improvements to enhance the user experience during computation.


**Most important feedback points received:**

The customer pointed out that it was unclear how long to wait for a solution (UAT-003), because only the "computing" status was visible without an estimated waiting time or progress indicator.
The calculation process lacks interactivity, users cannot determine when calculations will be completed or how much time remains.
To address this, it was decided to add a waiting time estimate to the status display, providing users with better visibility into the solution retrieval process.


[Resulting PBIs or issues](https://github.com/iu-students/route-optimization-platform/issues/71)

---

## Quality Evidence Discussed

- The customer noted that the **"check status" button** returns only "processing" with no time estimate, making it unclear when computation will finish. This was identified as a usability gap.
- The team confirmed that **API key-based access** is partially implemented.
- **Input validation** for incorrect requests is planned for completion this week.

---

## Feedback

1.  **Swagger UI Feedback:** The system needs progress indication or estimated time of completion during long calculations.
2.  **Algorithm Direction:** The customer suggested exploring route fragment generation combined with an assignment problem approach to optimize loader distribution more globally.
3.  **Time Window Management:** The loader and vehicle routing algorithms are still planned separately; the customer suggested linking them via time window management to improve joint optimization. 
4. **Penalty:** The customer suggested analyzing the penalty structure and order coverage gap between versions to understand where performance is lost.
---

## Approvals or Requested Changes

- **Approved:** Updated sprint backlog and user story structure.
- **Approved:** Baseline comparison metrics presented in the summary spreadsheet.
- **Approved:** UAT format: customer will record independently over the weekend.
- **Approved:** GitHub repository structure verified; user stories conform to stated requirements.
- **Requested:** Add a progress indicator or time estimate to the status endpoint so the user understands when computation will complete.
- **Requested:** Continue improving algorithm quality based on directions discussed (penalty analysis, loader–vehicle linking, clustering).
- **Requested:** Fix mandatory order skipping in version B before it can be considered production-ready.

---

## Risks

| Risk | Mitigation |
|---|---|
| The experimental CP Solver (Version B) might incorrectly skip mandatory orders if penalty weights are not properly calibrated during integration. | Tighten penalty weights and re-run tests before next review. |
| The continued decoupling of vehicle and loader algorithms could be limiting overall solution quality on several test cases. | Explore time window sharing between sub-algorithms as a first integration step. |
| The greedy algorithm (Version A) still underperforms the baseline on 4 out of 10 tests, risking overall project success. | Analyze penalty structure and order coverage gaps; adjust weights or explore assignment-problem approach for loader scheduling. |
| Customer may encounter unclear system behavior during UAT due to missing progress feedback. | Implement basic progress indicator. |

---

## Action Points

- Implement a basic progress indicator or estimated completion time for long-running calculations.
- Log algorithm improvement directions from this meeting (penalty analysis, loader–vehicle linking via time windows, route fragment generation, order clustering).
- Tighten penalty weights in version B to prevent mandatory orders from being skipped.
- Complete input validation implementation this week.


---

## Resulting Product Backlog or Scope Changes

- **Added to backlog:** Task to implement a progress indicator / time estimate for the calculation status endpoint.
- **Algorithm Direction:** Algorithm will be improve based on customer feedback: penalty structure analysis, loader–vehicle time window linking, route fragment generation with assignment model, order clustering by geography and time windows.
- **Scope confirmed:** Optional order handling (done this sprint) and input validation (to be completed this week) remain in scope.
- **Deferred:** Manager metrics dashboard (added to backlog, not planned for this sprint).
