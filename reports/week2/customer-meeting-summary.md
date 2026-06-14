# Customer Meeting Summary

**Date:** 11.06.2026

**Participants:**
- Maxim Potushinskii - interviewer: conducted a dialogue with the customer
- Timur Iusupov - note taker: took detailed notes during interview
- Dania Galieva - moderator: listened, helped the team sync their understanding

**Artifact demonstrated:**
- User story
- Swagger UI
- Plan MVP to the next week

**Discuss points:**
- Transcript availability - not to be published in the public domain
- The choice of approach focuses on VRP (PyVRP), and an in-house algorithm is also considered (in parallel).
- Testing – take real customer data, cut out the VRP part, test on real scenarios.
- License - the customer allowed to develop the product under the MIT license
- Swagger UI - showed the customer a prototype and discussed what it was for
- Where the calculations will be performed. what the server will be responsible for and what the service will be responsible for
- Basic concept: VRP for machines, then greedy distribution of loaders.
- The customer's recommendation is to combine two subtasks into one for a better solution
- The customer's recommendation is to use assignment issue + CPSolver/PIP
- Format of work - please send all files for review in advance (before the meeting).

**Decisions:**

| Decision | Why |
|----------|-----|
| No public transcripts | The customer requested that the transcript not be made publicly available. |
| Follow current MVP plan | The team and customer agreed to prioritize delivering a working result by next week over exploring alternatives. |
| Consider the assignment problem and CPSolver/PIP | Customer recommended this approach as a potential alternative to PyVRP for better integration of trucks and loaders. |
| Consider combining two subtasks into one | Customer's recommendation |
| Send files before the meeting | It speeds up communication and allows you to resolve customer issues during calls. |

**Action points:**
- Get customer feedback on Swagger UI and User Stories (after meeting)
- Fix user story by customer's requirements (before weekend)
- Cut real test data and start testing VRP on real scenarios (this week)
- Deploy MVP v0 foundation with smoke check (end of this week)
- Build MVP – get any response from server, even if not optimal (end of next week)
- Think about combining trucks and workers into one problem (optional, ongoing)
- Explore Assignment Problem + route generator + CPSolver as an alternative (optional, ongoing)
- Send all documents for review before the next meeting (before each meeting)
- Complete Assignment 2 (before weekend)
- Work on MVP in parallel with Assignment 2 (weekend)

**Risks:**

| Risk | Mitigation |
|------|-------------|
| Customer may not review materials before meeting | Send all materials for review in advance, before the meeting |
| MVP may produce a non-optimal solution, but customer might expect better results | Clearly communicated during the meeting that MVP will be "not optimal, but correct" |
| Alternative approaches (Assignment Problem + CPSolver) may distract the team from the main MVP | Do optional research in parallel, not instead of the main MVP plan |

**Feedback from customer:**
- Connect trucks and workers into one problem, don't just assign workers greedily.
- After meeting we get feedback to User points and rewrite it (all changes in github file)
- Try Assignment Problem + CPSolver + smart route generation.
- Send materials before the meeting.
- Swagger is ok

**Customer approvals:**
- Transcript access - do not public in github
- Swagger UI design - approved
- User story - changed based on customer requirements
- MVP plan to the next week - approved
- Publish under MIT licence - approved

**Resulting changes:**
- **Transcript publication:** will not be published publicly, only shared with instructors
- **Testing approach:** switch from synthetic tests to real customer scenarios
- **Material review process:** send all documents in advance, not during the meeting
- **Algorithm direction:** main MVP stays with PyVRP; optionally explore Assignment Problem + CPSolver
- **Workers + trucks:** consider combining them into one problem instead of greedy assignment (optional)

**Important links:**
- The first version of user story: https://github.com/iu-students/route-optimization-platform/blob/6df6f1cf5652cf7e3e717fb203151c7d93b3c0fd/reports/week2/user-stories.md
- The second version of user story: https://github.com/iu-students/route-optimization-platform/blob/c685297bb54fe740eb06e26c24741d77b3453281/reports/week2/user-stories.md
- Swagger UI: https://iu-students.github.io/route-optimization-platform/swagger/
