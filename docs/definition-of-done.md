# Definition of Done

This document defines the shared minimum completion standard for work in that repository. A Product Backlog Item (PBI) may be marked as **Done** only when its issue-specific acceptance criteria and the team Definition of Done are satisfied.

## Minimum Completion Standard

A PBI is considered "Done" when:

1.  **Acceptance Criteria Satisfied**
    - All issue-specific acceptance criteria defined in the PBI are met and verified.

2.  **Peer Review**
    - The work has been reviewed and approved by at least one other team member.
    - Approval visible in PR/MR history
  
3.   **CI checks / Automated tests**
    All CI checks pass:
       - Linting
       - Formatting
       - Package
       - Unit tests
       - Integration tests
       - Automated QRTs
       - Line coverage reporting
       - Additional QA check
       - Lychee link checking

4.  **Quality Requirements**
    - All quality requirements documented in `docs/quality-requirements.md` are satisfied
    - Relevant automated QRTs from `docs/quality-requirement-tests.md` are passing
    - Non-applicable QRTs are documented with rationale
  
5.  **Coverage expectations for critical modules**
    - Each critical module must have automated line coverage ≥ 30%
    - Exceptions require documented rationale and TA approval

6.  **Verification and Testing Evidence**
    - For user stories, the linked supporting PBIs provide the required implementation, review, and verification evidence.
    - Verification evidence is preserved in the PR comments, test reports, CI/CD logs.

7.  **Changelog Updated**
    - `CHANGELOG.md` has been updated in accordance with the [Repository Requirements](#repository-requirements).
    - A user-visible entry has been added under the `[Unreleased]` section using the appropriate category (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`).
    - This requirement is waived if the PR/MR template's changelog checklist explicitly selects "Not applicable because the change is not user-visible."

8.  **Merged to Default Branch**
    - For supporting or implementation PBIs (e.g., code tasks), the issue-linked PR/MR is merged into the protected default branch (main).
    
