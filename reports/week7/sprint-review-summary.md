# Sprint Review Summary

**Date:** 17.07.2026

**Participants:**
- **Maxim Potushinskii** - Team Lead/Interviewer, Speaker 2: Presented project status, documentation updates, and coordinated UAT execution.
- **Marsel Tukhvatullin** - Moderator/discussion participant, Speaker 3: Presented algorithm improvements (depot departure optimization, route rearrangement, multi-run checks).
- **Timur Iusupov** - Moderator/discussion participant, Speaker 4: Presented CP Solver enhancements (route generation modifications, pool expansion).
- **Dania Galieva** - Moderator, Speakers 5: Participated in the final meeting.
- **Anastasiia Glinskaia** - Note taker, Speaker 6: Took detailed notes during interview.

**Recording:** Permitted. Public transcript publication: Permitted. Transcript: [sprint-review-transcript.md](./sprint-review-transcript.md)

---

## Sprint Goal Reviewed

Final stabilization, performance optimization, and complete polishing of the product and documentation. Preparation of the final version MVPv3 and delivery of all remaining Product Backlog Items to ensure the platform is fully production-ready.

---

## Delivered Increment Discussed

- **Algorithm Improvements (CP Solver):** The primary algorithm now completely outperforms the baseline across all 10 test cases. Key fixes included optimizing vehicle departure times from the depot, rearranging routes, and running multiple iterations for small input sizes to avoid suboptimal routes.
- **Algorithm Improvements:** Enhanced route generation by adding a new library and expanding the route pool. This yielded a ~2% improvement over the baseline on specific cases (1st, 3td and 4th), primarily by reducing the number of loaders required.
- **Documentation and Security Fixes:** Added `data/history.db` and runtime data directories to `.gitignore` to prevent data leaks. Updated customer-facing documentation based on previous feedback.
- **Handover Completion:** The solution remains deployed on the university VM (public IP), and administrator rights to the repository were formally transferred to the customer.

---

## UAT Results

UAT was not conducted live during this meeting. The team will send UAT scenarios to the customer after the meeting for independent recording, as in previous sprints.

Summary for the report:

UAT scenarios that passed:

UAT-001 (Server Health Check) - PASS

UAT-002 (Start Background Solution) - PASS

UAT-003 (Retrieve Solution) - PASS

UAT-004 (Retrieving Computational Metrics) - PASS

UAT-005 (Input Data Validation Check) - PASS

UAT-006: View Calculation History -  PASS

UAT-007: View Calculation Details by Request ID -  PASS

UAT scenarios that failed or need product changes:

No scenarios failed. All scenarios passed without any outstanding issues or required product changes.

What still needs to be fixed in the product:

Nothing. All issues identified during previous test executions have been resolved as of version v0.4.0 and remain fixed in the current release, v1.0.0.:

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

## Quality Evidence Discussed

- The team demonstrated that the algorithm now passes 100% of the 10 standard test cases, overcoming the 2% deficit on the 4th case noted in Week 6.
- An Excel file with detailed baseline comparison metrics was provided to the customer for local verification.
- The customer validated that the documentation is sufficient to independently pull the repository and deploy the solution in a local or corporate environment.

---

## Feedback

-   **Final Acceptance:** The customer confirmed acceptance of the solution, stating the handover question is closed.
-   **Teamwork and Process:** The customer provided highly positive feedback on the team's self-organization, structured interaction, and strict distribution of responsibilities, noting it aligns with large corporate standards.
-   **Algorithm Success:** The customer praised the team for successfully developing algorithms that beat the baseline, bringing the competitive part of the task to completion.
-   **University Curriculum:** Positive feedback was given regarding the university's project management practice, noting it provides an excellent foundation for early-stage students.

---

## Approvals or Requested Changes

- **Approved:** Final transition and repository handover. The customer confirmed they have everything and are accepting the solution.
- **Approved:** Documentation is sufficient for independent deployment.
- **Approved:** All UAT tests passed.
- **Approved:** User stories - customer confirmed all previously discussed requirements are addressed.
- **Requested:** The customer will run the algorithms locally to verify that their results match the team's metrics.

---

## Risks

| Risk | Mitigation |
|---|---|
| Heuristic algorithms may produce slightly varying results on identical input data across different runs. | The customer will perform multiple runs locally to check for major discrepancies. Customer acknowledged this limitation and confirmed it is within acceptable scope. |
| Customer has not yet run the new algorithm version locally to verify baseline results. | Customer will test independently; team remains available for async consultation if issues arise. |

---

## Action Points

- **Customer:** Run the algorithm locally and compare results with the provided metrics.
- **Team:** Finalize the `MVP v3` SemVer release and Demo Day preparation based on this final acceptance.

---

## Resulting Product Backlog or Scope Changes

- **Project handover confirmed.** No new user stories or scope changes requested.
- **Final sprint** - all agreed requirements are addressed. No backlog additions.
- **Project status:** `Accepted` by the customer. Handover level reached - `Deployed or operated on customer side`
