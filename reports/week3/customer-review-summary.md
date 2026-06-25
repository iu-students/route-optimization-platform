**Date:** 19.06.2026

**Participants:**
*   **Maxim Potushinskii** - Speaker 1, Team Lead/Interviewer: Presented weekly results, server access, UI, and repository structure.
*   **Dania Galieva** - Speaker 4, Moderator/discussion participant: Listened, helped the team sync their understanding, explained the MVP algorithm implementation (PyVRP + greedy algorithm).
*   **Marsel Tukhvatullin** - Speaker 2, Moderator/discussion participant: Listened, helped the team sync their understanding, presented the updated backlog and user stories.
*   **Timur Iusupov** - Speaker 5, Note taker/discussion participant: Took detailed notes during interview, explained the experimental branch integrating CP Solver.

**Artifacts demonstrated:**
1. Updated user story
2. Product Backlog (prioritized user stories and technical tasks TT-1, TT-2, etc.).
3. First version of MVP (vehicle and loader distribution algorithm).
4. Swagger UI (as an interface for API interaction).
5. GitHub Repository (organization structure, stable and experimental branches).

**Scope reviewed:**
1. **User stories update:** Adding stories for optional orders (which can be skipped or not fulfilled within the time window) and highlighting mandatory orders as a hard constraint.
2. **Metrics and statistics:** Adding requirements for the manager to view the overall objective function and calculation statistics to evaluate route efficiency.
3. **User interface:** Review and approval of using Swagger UI for API interaction.
4. **Current MVP algorithm:** Review of the greedy algorithm mechanics (distributing loaders over PyVRP routes, minimizing vehicle idle time) and baseline comparison results (better in some cases).
5. **Algorithm development:** Considering an experimental approach using CP Solver for the assignment problem to jointly optimize vehicles and loaders.
6. **Architectural "seam" between models:** Discussing the gap between separate calculations for vehicles and loaders; customer recommended adding cost estimates per order to determine if servicing it is economically viable.
7. **Infrastructure:** Checking repository structure and MVP access via public IP.

**Implemented increment discussed:**
*   The first version of the MVP is ready. Vehicle routes are built using PyVRP, and loaders are distributed on top using a greedy algorithm. 
*   The algorithm is being tested successfully, showing results on par with the baseline, and outperforming it in some cases. 
*   Access to the MVP is configured via a public IP address.
*   An experimental branch using CPSolver to generate routes for loaders and vehicles separately has been prepared.

**Approvals or requested changes:**
*   *Approved:* Updated Product Backlog and User Stories (matches previous feedback).
*   *Approved:* Sprint plan / timeline to lock in the MVP status by next week.
*   *Approved:* Publishing meeting transcripts in GitHub (canceling the previous restriction).
*   *Requested changes:* 
    *   Add user stories for optional orders (which can be skipped or not fulfilled within the window).
    *   Add a hard constraint for mandatory orders.
    *   Add a story for the manager to view calculation metrics and statistics (objective function).
    *   Minimize the "seam" between vehicle and loader models: embed an order cost estimate to understand if it's worth fulfilling at all (compare loader hiring costs with order profit).

**Risks:**

| Risk | Mitigation |
| :--- | :--- |
| Separating vehicle and loader models prevents correct order economics evaluation (loader costs are invisible) | Implement a cost estimate for fulfilling a single order and check free capacity before assignment. |
| The customer does not understand how to run the project through the terminal| Refine clear instructions for running the project from the terminal  in the repository. |
| Failing to outperform the baseline| The baseline needs to be exceeded only in the final version of the product, but the MVP already exceeds some tests

**Action points:**
*   Send the test environment link (public IP) to the customer (within a couple of hours after the meeting).
*   Send up-to-date repository links and explicitly state which branch is responsible for what (after the meeting).
*  Refine the description for running the project from source code via terminal to the repository.
*   Re-run tests and provide baseline comparison statistics (in percentages, how many cases are better/worse).
*   Update the backlog with new user stories (optional/mandatory orders, metrics).
*   Think about integrating cost estimates and filtering out unprofitable orders.
*   Investigate ways to minimize the "seam" between models: Explore how to better connect the separate vehicle and loader calculation models to improve overall routing efficiency.
*   Publish meeting transcripts in GitHub.
*   Lock in the MVP achievement status next week.


**Resulting Product Backlog or scope changes:**
*   *Added to Backlog:* User story for optional orders.
*   *Added to Backlog:* User story to highlight mandatory orders as a hard constraint.
*   *Added to Backlog:* User story to display objective function calculation metrics and statistics for the manager.
*   *Scope change:* The algorithm must consider not only waiting time but also economic viability (estimating loader costs to decide whether to take an additional order or not).
*   *Process change:* Meeting transcripts will now be published in GitHub.
