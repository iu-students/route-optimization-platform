# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security


## [1.0.0] - 2026-07-18

### Added

- Inter-route order exchange: solver now attempts to move or swap orders between vehicles, accepting only cost-reducing moves that preserve route validity
- `optional_penalty_factor` request parameter to tune optional-order skip aggressiveness without affecting final cost comparison

### Changed

- Vehicle departure time is now chosen to minimize idle-on-shift: the vehicle waits at the depot instead of arriving early and burning shift time at customer sites
- Optional order skipping now evaluates two candidate sets (conservative and aggressive), runs both, and keeps the cheaper result
- Solver runs multiple attempts from scratch on small tests (when time permits) and returns the best result
- Remaining time budget is fully utilized: a squeezed attempt runs if possible, followed by continuous polish of the best solution until the deadline
- Progress output is flushed immediately for better visibility in Docker/log environments
- OR-Tools (when enabled) runs once at startup instead of once per attempt

### Removed

- PyVRP pipeline - fully removed; all solving now goes through the CP-SAT solver

### Fixed

- Route-merge function no longer overwrites correct departure times with the old formula - this was silently breaking optimized departure times and causing false shift-overrun violations


## [0.4.0] - 2026-07-12

### Added

- Implemented SQLite database schema for calculation history ([#TT-19](https://github.com/iu-students/route-optimization-platform/issues/96))
  - `calculation_history` table with columns: `calculation_id`, `timestamp`, `execution_time`, `objective_function_cost`, `status`, `input_json_path`, `output_json_path`
  - Automatic creation of `data/inputs/` and `data/outputs/` directories on application startup
  - Input JSON saved as a file in `data/inputs/` before solving begins, with database status set to "processing"
  - Output JSON saved as a file in `data/outputs/` after successful completion
  - Database record updated with `output_json_path`, `execution_time`, `objective_function_cost`, and `status` set to "success" on completion
  - On failure or timeout: status set to "error" with error details written to output file
- Added `GET /history` endpoint returning a JSON array of past calculations with summary metadata ([#TT-20](https://github.com/iu-students/route-optimization-platform/issues/97))
  - Each record contains `calculation_id`, `timestamp`, `execution_time`, `objective_function_cost`, and `status`
- Added `GET /history/{calculation_id}` endpoint returning full calculation details including input/output JSON files and metadata ([#TT-20](https://github.com/iu-students/route-optimization-platform/issues/97))
- Added 404 response for requests to non-existent `calculation_id` ([#TT-20](https://github.com/iu-students/route-optimization-platform/issues/97))

## [0.3.0] - 2026-07-05

### Added

- Implemented Clarke-Wright savings algorithm for vehicle minimization ([TT-3](https://github.com/iu-students/route-optimization-platform/issues/79))
  - Initial state creates N separate routes, one per order, each served by a dedicated vehicle
  - Evaluates route merges by calculating savings from `take_vehicle` penalty saved and `fuel_cost` for distance reduction
  - Merges routes when positive savings are detected, reducing active vehicle count by 1 per merge
- Added time window and capacity constraint enforcement during route merging ([TT-4](https://github.com/iu-students/route-optimization-platform/issues/80))
  - Combined order volume is validated against `vehicle_capacity` before merge is accepted
  - Delivery sequence arrival times are recalculated and checked against each order's `time_window`
  - Merge is rejected immediately if any capacity or time window violation is detected
  - Final optimized route plan guarantees minimum vehicle count without violating constraints
- Implemented objective function calculation based on final routes and weights ([#TT-7](https://github.com/iu-students/route-optimization-platform/issues/78))
  - Fuel cost: total distance traveled by all vehicles multiplied by `fuel_cost`
  - Vehicle and loader salaries: count of unique vehicles × `take_vehicle`, count of unique loaders × `add_loader`
  - Loader work cost: total time (travel + waiting + service) spent by all loaders multiplied by `loader_work`
  - Penalties: number of skipped optional orders multiplied by `order_penalty`
- Added statistics object to API and output JSON response ([#TT-6](https://github.com/iu-students/route-optimization-platform/issues/77))
  - Response includes a `statistics` block with keys: `total_cost`, `fuel_cost`, `vehicle_salaries`, `loader_salaries`, `loader_work_cost`, `penalties`
  - `total_cost` equals the exact sum of all component costs
  - Statistics are persisted inside the output JSON file and returned via `GET /solution` and `GET /metrics`
- Added `GET /metrics` endpoint returning cost breakdown and summary metrics ([#TT-6](https://github.com/iu-students/route-optimization-platform/issues/77))
- Added `POST /validate` endpoint to validate input scenario without solving ([#TT-5](https://github.com/iu-students/route-optimization-platform/issues/81))
  - Returns `{"status": "ok"}` on valid input
  - Returns `{"status": "error", "errors": [...]}` with detailed field-level messages on invalid input
- Computation endpoints now report detailed stage during solving ([#TT-6](https://github.com/iu-students/route-optimization-platform/issues/77))
  - `GET /solution` and `GET /metrics` return `"stage": "parsing"`, `"stage": "solving_vehicles"`, `"stage": "solving_loaders"`, etc. instead of plain `"status": "computing"`

## [0.2.0] - 2026-06-28

### Added

- Implemented optional order penalty system: orders with `"optional": 1` are assigned a skip cost from `order_penalty` in weights; orders with `"optional": 0` have infinite skip cost ([#TT-1](https://github.com/iu-students/route-optimization-platform/issues/59)) 
- Added fulfillment cost calculation for optional orders, summing all additional costs (fuel, loader work, etc.) ([#TT-1](https://github.com/iu-students/route-optimization-platform/issues/59)) 
- Implemented decision-making logic that compares skip cost vs fulfillment cost to determine whether an order should be skipped ([#TT-2](https://github.com/iu-students/route-optimization-platform/issues/60)) 
- Created separate `Truck` and `Loader` data models with dedicated fields ([#TT-3](https://github.com/iu-students/route-optimization-platform/issues/62)) 
- Added database migrations for the new entity models with data migration support ([#TT-3](https://github.com/iu-students/route-optimization-platform/issues/62)) 
- Implemented independent route generation for vehicles and loaders - routes no longer depend on each other ([#TT-4](https://github.com/iu-students/route-optimization-platform/issues/63)) 
- Added arrival time synchronization logic to minimize difference between vehicle and loader arrival times at delivery points ([#TT-4](https://github.com/iu-students/route-optimization-platform/issues/63)) 
- Implemented input JSON validation function that checks for mandatory blocks and fields, correct data types, and physical meaning of values ([TT-5](https://github.com/iu-students/route-optimization-platform/issues/64)) 
  - Validates presence of all required blocks (depot, orders, weights, general parameters)
  - Validates order fields (id, x, y, volume, time_window, vehicle_service_time, loader_cnt, loader_service_time, optional)
  - Validates depot fields (id, x, y, load_time) and weights fields (order_penalty, take_vehicle, add_loader, fuel_cost, loader_work)
  - Validates numeric constraints (non-negative volumes, positive capacities/speeds, time window ordering, optional field 0/1)
  - Returns HTTP 400 with detailed error JSON on validation failure
- Added validation integration into API: invalid input is rejected before routing begins ([TT-5](https://github.com/iu-students/route-optimization-platform/issues/64))

### Changed

- Routing algorithm now produces separate independent routes for vehicles and loaders ([TT-4](https://github.com/iu-students/route-optimization-platform/issues/63)) 
- Route generation evaluates optional order profitability before including orders in final routes ([#TT-2](https://github.com/iu-students/route-optimization-platform/issues/60))

## [0.1.0] - 2026-06-21

### Added

- Implemented JSON file reading mechanism for vehicle, loader, and order data ([#TT-1](https://github.com/iu-students/route-optimization-platform/issues/35))
- Implemented JSON file generation function for individual driver/loader daily routes ([#TT-5](https://github.com/iu-students/route-optimization-platform/issues/39))
- Added route capacity validation for trucks to ensure orders do not exceed vehicle capacity ([#TT-2](https://github.com/iu-students/route-optimization-platform/issues/36))
- Added verification that truck capacity constraints are respected during route generation ([#TT-2](https://github.com/iu-students/route-optimization-platform/issues/36))
- Added shift duration verification for loaders and drivers to ensure route start times do not exceed shift end times ([#TT-3](https://github.com/iu-students/route-optimization-platform/issues/37))
- Added order time window verification to ensure estimated arrival times at each delivery point fall within specified intervals ([#TT-4](https://github.com/iu-students/route-optimization-platform/issues/38))
- Added REST API endpoints for submitting routing problems and receiving solutions ([#TT-6](https://github.com/iu-students/route-optimization-platform/issues/41))
  - `POST /solve` - Accepts JSON with vehicle, loader, and order data; starts computations
  - `GET /solution` - Returns generated routes or status of computations   
  - `GET /health` - Service health check endpoint
- Deployed MVP v1 to production hosting ([#TT-7](https://github.com/iu-students/route-optimization-platform/issues/40))
- Application now accessible via public URL ([#TT-7](https://github.com/iu-students/route-optimization-platform/issues/40))

### Changed
- Route generation now validates truck capacity before creating final routes ([#TT-2](https://github.com/iu-students/route-optimization-platform/issues/36))
- Route generation now validates shift constraints for loaders and drivers before assigning routes ([#TT-3](https://github.com/iu-students/route-optimization-platform/issues/37))
- Route generation now validates time window constraints for all delivery points sequentially ([#TT-4](https://github.com/iu-students/route-optimization-platform/issues/38))
