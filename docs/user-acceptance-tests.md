# User Acceptance Tests

## UAT-001: Server Health Check

**Status:** Active

**User Goal:** The user wants to verify that the service is operational and accessible before submitting tasks to it.

**Preconditions:**
- API server is available at `http://139.100.207.201:5000/docs`
- Target server selected: `http://139.100.207.201:5001` - MVPv1

**Steps:**
1. Send a GET request to the `/health` endpoint.
2. Receive and record the response.

**Expected Result:** The user receives a response with HTTP status code 200 and status "ok".

**Execution Results (Week 4):**

| Execution Date | Tester | Result | Notes |
|----------------|--------|--------|-------|
| | | | |

**Customer Comments / Issues:**
*(To be filled after UAT execution)*

**Resulting PBIs / Backlog Items:**
*(To be filled after UAT execution)*

---

## UAT-002: Start Background Solution

**Status:** Active

**User Goal:** The user wants to start the solution in background mode to obtain results after the algorithm completes.

**Preconditions:**
- API server is available at `http://139.100.207.201:5000/docs`
- Target server selected: `http://139.100.207.201:5001` - MVPv1
- The user has a prepared JSON scenario file

**Steps:**
1. Authenticate with the server — enter the API key in the Authorize section.
2. Send a POST request to the `/solve` endpoint with the JSON scenario as the request body.

**Expected Result:** `POST /solve` returns `{ "status": "started" }` with status code 202.

**Execution Results (Week 4):**

| Execution Date | Tester | Result | Notes |
|----------------|--------|--------|-------|
| | | | |

**Customer Comments / Issues:**
*(To be filled after UAT execution)*

**Resulting PBIs / Backlog Items:**
*(To be filled after UAT execution)*

---

## UAT-003: Retrieve Solution

**Status:** Active

**User Goal:** The user wants to obtain the optimal solution for order distribution, vehicle assignment, and loader allocation.

**Preconditions:**
- API server is available at `http://139.100.207.201:5000/docs`
- Target server selected: `http://139.100.207.201:5001` - MVPv1
- The user has a prepared JSON scenario file
- The user has started the solution in background mode and received a "started" status response

**Steps:**
1. Wait 2 minutes after starting the solution, then send GET requests to the `/solution` endpoint until the status returns "done".
2. Verify the solution structure:
   - Solution contains routes for loaders
   - Solution contains routes for vehicles with depot arrival times
3. Verify strict constraint compliance:
   - Cargo volume does not exceed vehicle capacity
   - Route start time does not exceed the driver's shift end time
   - Arrival (unloading start) falls within the time windows, inclusive

**Expected Result:** `GET /solution` after completion returns status code 200 and a JSON with the following fields:
- `loaders` — routes for assigned loaders. Contains loader IDs and their routes (order IDs, starting and ending at the same point).
- `vehicles` — routes for vehicles. Contains vehicle IDs, their routes (order IDs, starting and ending at depot ID 0), and arrival times at each point.
- `validation` — strict constraint checks. Expected status "success" for:
  - `capacity_verification`
  - `shift_verification`
  - `time_window_verification`

**Execution Results (Week 4):**

| Execution Date | Tester | Result | Notes |
|----------------|--------|--------|-------|
| | | | |

**Customer Comments / Issues:**
*(To be filled after UAT execution)*

**Resulting PBIs / Backlog Items:**
*(To be filled after UAT execution)*

---

## Execution History (Week 4)

| Scenario ID | Status | Tester | Date | Result |
|-------------|--------|--------|------|--------|
| UAT-001 | Pending | | | |
| UAT-002 | Pending | | | |
| UAT-003 | Pending | | | |

**Summary of Week 4 UAT Results:**
*(To be filled after execution)*

**Key Feedback Received:**
*(To be filled after execution)*

**Created/Updated PBIs:**
*(To be filled after execution)*
