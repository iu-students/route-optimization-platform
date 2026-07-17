# Sprint 5 Retrospective

## What went well

1. **Baseline fully surpassed:** The team successfully closed the remaining 2% gap on test case 4. By optimizing vehicle departure times from the depot, rearranging routes, and adding multi-run checks for small inputs, the algorithm now outperforms the baseline on all 10 test cases.
2. **Final product accepted by the customer:** The customer officially confirmed acceptance of the solution. He successfully pulled the repository and verified that the documentation is sufficient for independent local or corporate deployment.
3. **Documentation and security gaps fixed:** The team addressed the customer's feedback regarding missing port documentation, API version clarity, and the `.gitignore` configuration for runtime data (`data/inputs/`, `data/outputs/`, `data/history.db`).

## What did not go well

1. **Heuristic algorithm variance:** Because the solution uses heuristic algorithms, there is a minor risk that results might vary slightly between runs or on different machines.

## What changed compared to the previous Sprint based on the previous Sprint Retrospective

1. **Test case 4 gap resolved:** Following the action point from the previous retrospective, the team focused algorithm corrections on case 4. By fixing the depot departure logic and adding multi-run checks, the gap was successfully closed.
2. **Independent deployment finalized:** The team provided clear deployment instructions and async support, which allowed the customer to successfully deploy the solution in their local environment, achieving the `Deployed or operated on customer side` handover level.

## Action points

1. **Support:** Remain available for async onsultation during the customer's independent verification. If the customer encounters discrepancies when running the algorithm locally, provide support via chat.
