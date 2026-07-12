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

**Execution Results:**

| Execution Date | Tester | Result | Notes |
|----------------|--------|--------|-------|
| 27.06.2026 | Customer | PASS | Received HTTP 200 with {"status": "ok"} |
| 4.07.2026 | Customer | PASS | Received HTTP 200 with {"status": "ok"} |

**Customer Comments / Issues:**
All systems operational. Service is accessible and responsive.

**Resulting PBIs / Backlog Items:**
None.

---

## UAT-002: Start Background Solution

**Status:** Active

**User Goal:** The user wants to start the solution in background mode to obtain results after the algorithm completes.

**Preconditions:**
- API server is available at `http://139.100.207.201:5000/docs`
- Target server selected: `http://139.100.207.201:5001` - MVPv1
- The user has a prepared JSON scenario file

**Steps:**
1. Authenticate with the server - enter the API key in the Authorize section.
2. Send a POST request to the `/solve` endpoint with the JSON scenario as the request body.

**Expected Result:** `POST /solve` returns `{ "status": "started" }` with status code 202.

**Execution Results:**

| Execution Date | Tester | Result | Notes |
|----------------|--------|--------|-------|
| 27.06.2026 | Customer | PASS | Received HTTP 202 with {"status": "started"} |
| 04.07.2026 | Customer | PASS | Received HTTP 202 with {"status": "started"} |

**Customer Comments / Issues:**
Authentication successful. Background process initiated without errors.

**Resulting PBIs / Backlog Items:**
None.

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
- `loaders` - routes for assigned loaders. Contains loader IDs and their routes (order IDs, starting and ending at the same point).
- `vehicles` - routes for vehicles. Contains vehicle IDs, their routes (order IDs, starting and ending at depot ID 0), and arrival times at each point.
- `validation` - strict constraint checks. Expected status "success" for:
  - `capacity_verification`
  - `shift_verification`
  - `time_window_verification`
  
**Execution Results:**

| Execution Date | Tester | Result | Notes |
|----------------|--------|--------|-------|
|27.06.2026 | Customer | PASS (with comments) | Solution retrieved successfully. All validation checks passed. |
|4.07.2026 | Customer | PASS (with comments) | Solution retrieved successfully. All validation checks passed. |

**Customer Comments / Issues:**
The customer noted the system shows no progress during long calculations - "check status" returns only "processing" indefinitely. The customer requested a stage-based progress indicator rather than a simple time estimate - showing which algorithm stage is currently in progress and how many stages remain. This helps distinguish between "computing" and "crashed/frozen".

**Resulting PBIs / Backlog Items:**

https://github.com/iu-students/route-optimization-platform/issues/71 

---

## UAT-004: Retrieving Computational Metrics (NEW)

**Status:** Active

**User Goal:** The user wants to obtain metrics for the computed route.

**Preconditions:**
- API server is available at `http://139.100.207.201:5000/docs`
- The user is authenticated in the system
- Target server selected: `http://139.100.207.201:5002` - MVPv2
- The user has a prepared JSON scenario file
- The user has started the solution in background mode and received a "started" status response

**Steps:**
1. Send a GET request to the `/metrics` endpoint.
2. During computation, receive a response with status "computing" and the remaining time to wait for the response.
3. After that time elapses, send a repeat request and receive a response with status "done" and the metrics of the computed route.

**Expected Result:** `GET /metrics` after completion returns status code 200 and a JSON with the following metrics:
- `total_cost`
- `fuel_cost`
- `vehicle_salaries`
- `loader_salaries`
- `loader_work_cost`
- `penalties`

**Execution Results:**

| Execution Date | Tester | Result | Notes |
|----------------|--------|--------|-------|
| 4.07.2026 | Customer | PASS | All metrics returned successfully. Status "computing" received with estimated wait time, followed by status "done" with complete metrics. |


**Customer Comments / Issues:**

All test cases passed. The metrics endpoint works as expected. The estimated wait time during "computing" status is accurate and helpful for managing user expectations.

**Resulting PBIs / Backlog Items:**
https://github.com/iu-students/route-optimization-platform/issues/77
https://github.com/iu-students/route-optimization-platform/issues/78
https://github.com/iu-students/route-optimization-platform/issues/58

---

## UAT-005: Input Data Validation Check (NEW)

**Status:** Active

**User Goal:** The user wants to ensure that the input data is valid before requesting a solution.

**Preconditions:**
- API server is available at `http://139.100.207.201:5000/docs`
- The user is authenticated in the system
- Target server selected: `http://139.100.207.201:5002` - MVPv2
- The user has prepared JSON scenario files

**Steps:**
1. Send a POST request to the `/validation` endpoint with a default valid JSON request body.
2. Receive a response with HTTP status code 200 and status "ok".
3. Change any number in the request body to a negative value and send a repeat POST request.
4. Receive a response with HTTP status code 400 and an error description.
5. Change the syntax in the request body (remove quotes and/or brackets and/or commas and/or colons) and send a repeat POST request.
6. Receive a response with HTTP status code 400 and an error description.

**Expected Result:**
- On the first (valid) request, the user receives a response with HTTP status code 200 and status "ok".
- On the second (invalid) request, the user receives a response with HTTP status code 400 and an error description - a message about the negative number and the path where it was found.
- On the third (invalid) request, the user receives a response with HTTP status code 400 and an error description - does not conform to JSON format.

**Execution Results:**

| Execution Date | Tester | Result | Notes |
|----------------|--------|--------|-------|
| 4.07.2026 | Customer | PASS | Valid request returned 200 OK with status "ok". Negative value test returned 400 with clear error message identifying the negative number and its exact path in the JSON structure. Malformed JSON test returned 400 with appropriate error description indicating JSON format violation. |

**Customer Comments / Issues:**

All validation scenarios passed successfully. The error messages are clear and informative, making it easy for users to identify and fix issues in their input data. The validation endpoint effectively prevents invalid requests from reaching the computation engine.

**Resulting PBIs / Backlog Items:**

https://github.com/iu-students/route-optimization-platform/issues/81

---

## Execution History

| Scenario ID | Tester | Date | Result |
|-------------|--------|------|--------|
| UAT-001 | Customer | 27.06.2026 | PASS |
| UAT-002 | Customer | 27.06.2026 | PASS |
| UAT-003 | Customer | 27.06.2026 | PASS (with comments) |
| UAT-001 | Customer | 4.07.2026 | PASS |
| UAT-002 | Customer | 4.07.2026 | PASS |
| UAT-003 | Customer | 4.07.2026 | PASS (with comments) |
| UAT-004 | Customer | 4.07.2026 | PASS |
| UAT-005 | Customer | 4.07.2026 | PASS |

