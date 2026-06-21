## Learning points

### Product Backlog Migration and Refinement
The team learned the importance of traceability when migrating user stories. We discovered that backlog refinement is iterative: we started with 13 stories and added 1 new story (US-14) for order time windows. Consequently, we have 9 active user stories in Backlog.

### Backlog Refinement and DEEP Expectations
The team learned that user stories alone are insufficient for execution. Decomposing Must Have stories into technical tasks (TECH-01, TECH-02, TECH-03, TECH-04, TECH-05) and identifying infrastructure needs (DEVOPS-01, API-01) was essential for effective work.

### Estimation and Sprint Planning
Estimating revealed significant gaps in our understanding. US-11 seemed simple until we broke it down into acceptance criteria and discovered the need for multiple subtasks—generating individual JSON files, formatting outputs correctly, and handling edge cases. The total Product Backlog size came to 192 Story Points, and the Sprint 1 came to 63 Story Points much higher than our initial expectations. The amount of work required exceeded our expectations due to the complexity of integrating PyVRP with a greedy algorithm, implementing constraint checks, configuring the API, and deploying it.

### MVP v1 Delivery and Customer Review
The Sprint Review meeting on 19.06.2026 confirmed that the customer accepted our MVP v1 implementation. The customer validated that the core functionality meets expectations, approving the backlog, sprint plan, and timeline. Requested changes for the next iteration include adding optional orders, mandatory order constraints, metrics display, and economic viability cost estimates.

### Workflow Enforcement
The full repository workflow - issue templates, branch naming, PR reviews, SemVer releases - was challenging but valuable.

### Release Preparation
The team prepared and published SemVer release v0.1.0 mapped to MVP v1, tagged on the protected main branch. The root CHANGELOG.md was updated with all user-visible changes, including PyVRP integration, API endpoints, and deployment setup. The release includes deployment instructions, a public IP access link for the running MVP, and a sanitized video demonstration showcasing the working system.

---

## Validated assumptions

from customer feedback
### Confirmed
- **Drivers need ready-made routes**: The customer validated US-11—drivers should receive fixed routes, not plan themselves.
- **Time windows are critical**: Implementing US-13 and US-14 revealed they're interdependent with capacity constraints for feasibility.
- **MVP algorithm approach**: The PyVRP + greedy algorithm approach is performing well, outperforming the baseline in some cases.

### Rejected
- **Capacity alone is sufficient**: We assumed capacity was enough, but the customer pointed out order time windows and shift constraints are equally important, leading to US-14 and revised US-13.

---

## Friction and gaps

### Unresolved requirements
1. **Order splitting algorithm** (US-10): Criteria for splitting orders exceeding capacity unspecified.
2. **Economic viability logic** (new): No clear criteria for cost vs. profit evaluation.

### Technical risks
1. **Server stability**: Deployed MVP runs on a single public IP without load balancing or monitoring. Under load, the server may crash.
2. **Algorithm vs. baseline**: PyVRP + greedy does not consistently outperform the baseline across all test cases—risk of failing customer expectations.
3. **Model seam**: Separate vehicle and loader calculations prevent proper economic evaluation.

### Missing scope (deferred to MVP v2 or later versions)
- optional orders, metrics display

### Process friction
- PR reviews took 2-3 days; customer couldn't run project from source-terminal instructions need improvement

---

## Planned response

how the team will respond in the next Sprint or assignment, with links to affected PBIs, milestones, releases, or documentation where relevant.
## Planned response

Based on the friction identified during MVP v1 delivery and customer review, the team will take the following actions in Sprint 2 - https://github.com/iu-students/route-optimization-platform/milestone/2:

1. Re-run tests and provide baseline comparison statistics.
2. Update backlog with new user stories.
3. Implement optional orders handling ---> New US
4. Implement mandatory orders as hard constraints ---> New US
5. Schedule roadmap review with customer ---> roadmap.md

**Affected artifacts:**
*   PBIs: new
*   Milestone: Sprint 2 https://github.com/iu-students/route-optimization-platform/milestone/2
*   Documentation: docs/definition-of-done.md, docs/roadmap.md, reports/week3/customer-review-summary.md
