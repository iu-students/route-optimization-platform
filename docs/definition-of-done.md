# Definition of Done

This document defines the shared minimum completion standard for work in that repository. A Product Backlog Item (PBI) may be marked as **Done** only when its issue-specific acceptance criteria and
the team Definition of Done are satisfied.

## Minimum Completion Standard

A PBI is considered "Done" when:

1.  **Acceptance Criteria Satisfied**
    - All issue-specific acceptance criteria defined in the PBI are met and verified.

2.  **Peer Review**
    - The work has been reviewed and approved by at least one other team member.
    - For code changes, this is demonstrated through a reviewed and approved Pull Request (PR) or Merge Request (MR).

3.  **Verification Evidence**
    - For user stories, the linked supporting PBIs (e.g., implementation, testing) provide the required implementation, review, and verification evidence.
    - Verification evidence is preserved in the normal workflow artifacts (e.g., PR comments, test reports, CI/CD logs).

4.  **Required Tests or Checks Pass**
    - All Continuous Integration (CI) or automated checks (e.g., linters, unit tests, integration tests, build steps) pass successfully.
    - If manual testing is required, a summary of the test results is added to the PBI or PR.

5.  **Changelog Updated**
    - `CHANGELOG.md` has been updated in accordance with the [Repository Requirements](#repository-requirements).
    - A user-visible entry has been added under the `[Unreleased]` section using the appropriate category (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`).
    - This requirement is waived if the PR/MR template's changelog checklist explicitly selects "Not applicable because the change is not user-visible."

6.  **Merged to Default Branch**
    - For supporting or implementation PBIs (e.g., code tasks), the issue-linked PR/MR is merged into the protected default branch (main).
