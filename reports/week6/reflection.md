# Reflection

## Learning points

1. **Transition readiness requires explicit customer confirmation.** Handover is not just granting repository access and deploying - the customer must confirm that the product is functionally complete enough for their use case. In the Week 6 meeting, the customer accepted the current scope as ready for handover, but noted that industrial deployment was never the goal.

2. **Customer handover documentation is a distinct artifact type.** Writing `docs/customer-handover.md`, `CONTRIBUTING.md`, and `AGENTS.md` required translating months of implicit team knowledge into instructions accessible to both the customer and future contributors.

3. **Customer-facing documentation review confirmed clarity.** During the Week 6 meeting, the customer reviewed the documentation set (`README.md`, `docs/customer-handover.md`, run instructions, known limitations) and confirmed they found everything clear.

4. **Multi-route per vehicle logic substantially improves algorithm performance.** Integrating the customer's multi-route-per-vehicle suggestion into the CP-solver pipeline raised baseline outperformance from 8/10 to 9/10 test cases. The remaining 2% gap on case 4 is vehicle-specific and may require a different algorithmic approach for that input profile.

## Validated assumptions

### Confirmed

- **Customer accepts the product as functionally ready for handover.** The customer confirmed that everything agreed upon is present, pending verification of calculation history and deployment instructions.
- **Documentation-first approach for handover.** Preparing `docs/customer-handover.md`, `CONTRIBUTING.md`, and `AGENTS.md` before requesting customer confirmation made the transition discussion concrete and actionable.
- **CP-solver with multi-route per vehicle outperforms baseline on most cases.** 9 out of 10 test cases now pass, with all runs completing within 10–14 minutes - a significant reliability improvement over the previous sprint.

### Rejected
- **[Customer would deploy the product industrially].** The meeting revealed that the customer always viewed the product as a research-grade algorithmic demonstration.


## Friction and gaps

- **Test case 4 gap unresolved.** The CP-solver loses to the baseline by approximately 2% on the fourth test case due to vehicle routing constraints. The iterative algorithm (removal and reinsertion) is not yet stable enough to cover this gap.
- **Customer has not yet independently deployed the product.** The customer stated they would attempt deployment in Week 7. The handover level is currently `Ready for independent use` with acceptance pending independent deployment.

## Planned response

- Resolve the test case 4 gap by tuning the CP-solver parameters or routing constraints specifically for the vehicle profile of that input.
- Implement a new version of algorithm with a different approach from the previous one.
- Finalize deployment documentation and send clear independent-run instructions to the customer for Week 7 transition confirmation.
- Deliver `MVP v3` with the final algorithm selection, calculation history verified by the customer, and a public sanitized demo video.
- Confirm the handover level (`Ready for independent use`) and obtain the customer's acceptance status for the final report.
