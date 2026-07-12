# Sprint Review Summary

**Date:** 10.07.2026

**Participants:**
- **Maxim Potushinskii** - Team Lead/Interviewer, Speaker 1: Led the meeting, presented weekly progress and transition questions.
- **Dania Galieva** - Moderator/discussion participant, Speaker 3: Presented updated user stories and sprint backlog.
- **Timur Iusupov** - Moderator/discussion participant, Speaker 4: Presented CP-solver algorithm improvements and baseline comparison results.
- **Marsel Tukhvatullin** - Moderator/discussion participant, Speaker 5: Presented the iterative algorithm (point removal and reinsertion) development status.
- **Anastasia Glinskaia** - Note taker: Took detailed notes during interview.


**Recording:** Permitted. Public transcript publication: permitted. Transcript: [sprint-review-transcript.md](./sprint-review-transcript.md)

---

## Sprint Goal Reviewed

Enable data-driven decision-making by providing managers with comprehensive calculation history tracking (US-017) and persistent storage infrastructure (TT-19, TT-20), delivered as part of the v0.4.0 (MVPv2) release on the enhanced data persistence architecture.

---

## Delivered Increment Discussed

- **User stories:** [US-017](https://github.com/iu-students/route-optimization-platform/issues/89) (calculation history) was added with technical sub-tasks including database setup.
- **Calculation history feature:** Metrics and calculation history were implemented this week, allowing past runs to be tracked as the customer requested. Database was also integrated.  
- **Algorithm improvements (CP-solver):** Adjusted time limits separately for route generation and CP-solver phases. The algorithm now handles all 10 test cases within 10–14 minutes. It outperforms the baseline on 9 out of 10 cases. The only remaining gap is test case 4, where the algorithm underperforms by approximately 2% due to vehicle routing.
- **Algorithm improvements (iterative):** Iterative algorithm (point removal and reinsertion) is still in testing. Performance is below baseline on some test cases(2-3 cases). The system for returning vehicles to the depot has not yet been added - team are working on this.
- **Repository preparation for handover:** The team prepared the repository for customer handover, including `CONTRIBUTING.md`, `AGENTS.md`, and `docs/customer-handover.md`.

---

## UAT Results

UAT was not conducted live during this meeting. The team will send UAT scenarios to the customer after the meeting for independent recording, as in previous sprints.

Summary for the report:

UAT scenarios that passed:

UAT-001 (Server Health Check) — PASS

UAT-002 (Start Background Solution) — PASS

UAT-003 (Retrieve Solution) — PASS

UAT-004 (Retrieving Computational Metrics) — PASS

UAT-005 (Input Data Validation Check) — PASS

UAT-006: View Calculation History —  PASS

UAT-007: View Calculation Details by Request ID —  PASS

UAT scenarios that failed or need product changes:

No scenarios failed. All scenarios passed without any outstanding issues or required product changes.

What still needs to be fixed in the product:

Nothing. All identified issues from previous test executions have been fully resolved in version v0.4.0:

Stage-based progress indicator implemented (shows: starting, parsing, solving, solving_vehicles, solving_loaders, feedback_iteration)
History and calculation details endpoints successfully implemented


Most important feedback points received:

The customer confirmed that all issues have been resolved and the product fully meets their expectations.

Resulting PBIs or issues (All Resolved and Closed):

[#71](https://github.com/iu-students/route-optimization-platform/issues/71), 
[#77](https://github.com/iu-students/route-optimization-platform/issues/77),
[#78](https://github.com/iu-students/route-optimization-platform/issues/78),
[#58](https://github.com/iu-students/route-optimization-platform/issues/58),
[#81](https://github.com/iu-students/route-optimization-platform/issues/81),
[#89](https://github.com/iu-students/route-optimization-platform/issues/89),
[#96](https://github.com/iu-students/route-optimization-platform/issues/96),
[#97](https://github.com/iu-students/route-optimization-platform/issues/97)


---

## Feedback

-   **Project Handover and Transition Readiness:** The customer confirmed the product is functionally ready for transition. The handover process will involve granting admin rights and the customer deploying the solution locally to verify it.
-   **Algorithm Strategy:** The customer noted that having two different algorithms performing differently across test cases is acceptable. They advised using a threshold (e.g., switching algorithms based on the number of orders, like a limit of 100) as a normal, ethical practice to handle scale via decomposition.
-   **Industrial Use:** The customer clarified that expanding rules for industrial use is not required. The goal was to present a working idea, not to roll it out for production use.
-   **User Story:** The customer confirmed no additional user stories are needed - all previously discussed requirements are being addressed.
---

## Approvals or Requested Changes

- **Approved:** The customer will attempt to deploy the repository independently on their side during the next week.
- **Approved:** The customer confirmed that the product is functionally ready for handover, except for the calculation history feature which they had not yet reviewed.
- **Approved:** Calculation history user story ([US-017](https://github.com/iu-students/route-optimization-platform/issues/89)) and technical sub-tasks including database integration.
- **Approved:** Repository handover plan - admin access to be granted, customer will deploy independently next week.
- **Approved:** Two-pipeline approach - having two separate algorithms is acceptable and not a workaround, provided the switcher is based on general parameters (e.g. order count), not tied to specific test cases.
- **Approved:** After meeting the customer approved documentation files (customer-handover.md, CONTRIBUTING.md, AGENTS.md). 
- **Requested:** Send deployment instructions and repository link to the customer after the meeting so they can attempt independent deployment.
- **Requested:** Document how to switch between algorithm pipelines and which parameters to adjust.

---

## Risks

| Risk | Mitigation |
|---|---|
| Test case 4 still underperforms baseline by ~2% - may not be resolved before final handover. | Focus algorithm corrections on case 4; consider algorithm switcher if iterative algorithm handles it better. |
| Iterative algorithm still underperforms on some cases and lacks vehicle depot-return logic. | Complete depot-return implementation; re-test all cases before final handover. |
| Customer deployment may encounter issues when deploying independently without team support. | Send clear instructions; remain available for async consultation during the week. |

---

## Action Points

- Send repository link and deployment instructions to the customer after the meeting.
- Grant admin repository access to the customer.
- Document algorithm pipeline switching instructions (which parameter to change and how).
- Implement vehicle depot-return logic in iterative algorithm and re-test all 10 cases.
- Investigate small corrections to case 4 in the CP-solver algorithm to close the remaining 2% gap.
- Determine the need to switch the algorithm based on the number of orders.

---

## Resulting Product Backlog or Scope Changes

- **Realised:** [US-017](https://github.com/iu-students/route-optimization-platform/issues/89) (calculation history) with database integration - completed and verified by customer (after meeting).
- **Added to the scope of application:** Research needs switching algorithms based on the number of orders.
- **Final handover** planned for end of Week 7 after customer successfully deploys and confirms acceptance.
- **No new user stories** requested by the customer - all previously discussed requirements are being addressed.
