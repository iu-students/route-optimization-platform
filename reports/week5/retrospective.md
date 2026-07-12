# Sprint 5 Retrospective

## What went well

1. **Significant algorithm improvement:** CP-solver-based algorithm, extended to account for loader costs when evaluating optional order removal, now outperforms the baseline on 8 out of 10 test cases within 15 minutes, compared to 5 out of 10 with the previous approach. This is a substantial step forward in solution quality.
2. **Successful response to customer feedback:** The team implemented all three feedback items carried over from the previous sprint - progress indicator, objective function metrics endpoint, and standalone input validation endpoint. The customer confirmed these were all necessary and useful.
3. **Architecture documentation completed:** The team produced static, dynamic, and deployment views using PlantUML diagrams and created three Architecture Decision Records linking structural choices to quality requirements. This was new territory for the team and was completed within the sprint.
4. **Effective asynchronous UAT execution:** The customer successfully conducted User Acceptance Testing (UAT) asynchronously by recording a screencast. The system handled the customer's custom test scenarios without crashing.


## What did not go well

1. **CP-solver version still exceeds the time limit:** The CP-solver-based approach with loader cost recalculation currently runs over 15 minutes on some test cases, making it unusable in the current form. The time budget needs to be revisited before this version can be considered for production.
2. **Multi-route per vehicle not investigated:** The customer pointed out that the problem statement allows a single vehicle to complete multiple routes per shift. The team had not noticed this and has not yet analyzed whether it would improve results.

## What changed compared to the previous Sprint based on the previous Sprint Retrospective

1. **Progress indication implemented:** Following the action point from the previous retrospective, the team implemented a progress display showing stage-based progress.
2. **Algorithm feedback from the customer was acted on:** The customer's suggestions regarding penalty structure analysis and route optimization directions were translated into concrete sprint tasks (Clarke-Wright algorithm, constraint validation during merging).

## Action points (Process improvements for the next Sprint)

1. **Add calculation history.** Consider starting implementation. Requires persistent storage for run results - execution time and objective function value per run.
2. **Investigate algorithm directions suggested by the customer:**
   - Analyze the frequency of short routes across test cases; if there are many, evaluate whether combining them into multi-route per vehicle plans would reduce vehicle count.
   - Analyze order volume distribution across test cases; evaluate whether separating high-volume orders into a dedicated routing iteration would improve overall route quality.
   - Look into 2-opt and 3-opt heuristics as potential improvement steps for the current algorithm.
3. **Resolve CP-solver time limit issue.** Identify where the time budget is being exceeded and restructure or limit the solver to stay within 15 minutes on all test cases.
