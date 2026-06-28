# Sprint 4 Retrospective

## What went well
1. **Successful response to customer feedback:** The team effectively translated the customer's feedback from Week 3 into concrete product improvements. We successfully implemented input JSON validation (preventing system crashes on bad requests) and the logic for handling optional orders.
2. **Baseline comparison metrics were prepared and shared.** The team shared a structured summary table covering key characteristics such as vehicle count, fuel consumption, route lengths, and order coverage across three test cases. This directly addressed a gap identified in the previous retrospective.
3. **Effective asynchronous UAT execution:** The customer successfully conducted User Acceptance Testing (UAT) asynchronously by recording a screencast. The system handled the customer's custom test scenarios without crashing.

## What did not go well
1. **Inconsistent algorithm performance against the baseline:** While the enhanced greedy algorithm outperforms the baseline on 5 out of 10 tests (showing significant 20-50% efficiency gains), it still underperforms on 4 tests (up to 15% lower). The experimental CP Solver branch is still not fully integrated.
2. **Lack of interactivity during long calculations:** During UAT, the customer noted that when sending a request, the API returns a "processing" status without indicating progress or an estimated completion time, making the system feel like a "black box" during the two-minute wait.
3. **Architectural "seam" bottleneck:** The separation between the vehicle routing model (PyVRP) and the loader routing model remains a major bottleneck. The loaders' algorithm currently identifies unprofitable points, but excluding them requires rebuilding the entire vehicle route, which is computationally expensive.
4. **The customer had not reviewed all submitted files before the meeting.** The UAT instructions and sprint 2 artifacts were not fully read by the customer prior to the call, leading to some clarification overhead during the meeting itself.

## What you changed compared to the previous Sprint based on the previous Sprint Retrospective
Based on the Week 3 Retrospective action points, we strictly implemented a pre-meeting preparation checklist. Before the Sprint Review with the customer, we ensured that all repository links were structured, access instructions were documented, and exact testing metrics (the baseline comparison statistics) were prepared. Additionally, we conducted internal backlog refinement prior to the meeting, which allowed us to proactively identify and formalize missing business logic (optional/mandatory orders, metrics) before the customer had to point them out. We also structured all project links clearly in the customer chat.

## Action points (Process improvements for the next Sprint)
1. **Improve the progress indication:** Implement progress indication or an estimated time of completion for the routing calculation endpoint, so users are not left guessing during long processing times.
2. **Agree on a file review deadline before each customer meeting.** To avoid situations where the customer has not had time to review submitted materials, sent to the customer the day before the meeting. 
3. **Turn customer algorithm feedback.** The customer provided specific directions for improving solution quality: analyzing the penalty structure, linking the loader and vehicle algorithms through time window management, and exploring route fragment generation with an assignment problem approach.
