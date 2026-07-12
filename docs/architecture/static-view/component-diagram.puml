@startuml component-diagram
title Route Optimization Platform — Component Diagram (Static View)

skinparam componentStyle rectangle
skinparam wrapWidth 200
skinparam shadowing false

actor "API Client" as Client
actor "Developer (CLI)" as Developer

package "API Layer" {
  [Flask API\n(Web/app.py)] as API
  [Validator\n(Web/validator.py)] as Validator
}

package "Pipeline A — CP-SAT (active, wired to API)" {
  [Orchestrator\n(CP-SAT/main.py)] as MainOrchestrator
  [Vehicle Routes Solver\n(CP-SAT/vehicle_routes.py)] as VehicleRoutesSolver
  [Loader Routes Solver\n(CP-SAT/loader_routes.py)] as LoaderRoutesSolver
  [Common Utils\n(CP-SAT/common_functions.py)] as CommonUtils
}

package "Pipeline B — PyVRP (alternative, CLI-only)" {
  [Orchestrator\n(PyVRP/script.py)] as ScriptOrchestrator
  [PyVRP Model] as PyVRPModel <<external library>>
  [Loaders Solver\n(PyVRP/loaders.py)] as LoadersSolver
}

package "Shared" {
  [Models / Dataclasses\n(Shared/models.py)] as Models
  [Verifier\n(Shared/verifier.py)] as Verifier
  [History\n(Shared/history.py)] as History
  database "Data Storage\n(input.json / output.json,\nlive scratch files)" as DataStorage
  folder "Per-calculation snapshots\n(data/inputs/{id}.json,\ndata/outputs/{id}.json)" as Snapshots
  database "history.db\n(SQLite, calculation_history table)" as HistoryDB <<external library>>
}

package "Offline Comparison Tool" {
  [Tester\n(tester.py)] as Tester
  folder "instances/\n(TASK.json, baseline_TASK.json,\noutput_TASK.json)" as TestCases
  file "comparison.xlsx\n(appends one dated sheet per run)" as ComparisonFile
}

' --- layout hint: force CLI-driven flow below the API-driven flow ---
Models -[hidden]d-> Developer

' --- API-driven flow (Pipeline A) ---
Client --> API : HTTP POST /solve\nHTTP GET /solution\nHTTP POST /validate\nHTTP GET /metrics\nHTTP GET /history\nHTTP GET /history/{id}
API --> Validator : validate_input()
API --> History : start_calculation()\nfinish_success() / finish_error()\nget_all() / get_by_id()
History --> HistoryDB : SQL read/write
History --> Snapshots : write input/output\nJSON per calculation_id
API --> MainOrchestrator : solve_pipeline()
MainOrchestrator --> VehicleRoutesSolver
MainOrchestrator --> LoaderRoutesSolver
VehicleRoutesSolver --> CommonUtils
LoaderRoutesSolver --> CommonUtils
MainOrchestrator --> Models
VehicleRoutesSolver --> Models
LoaderRoutesSolver --> Models
MainOrchestrator --> DataStorage : read input.json\nwrite output.json
MainOrchestrator --> Verifier : run_verification()
API --> DataStorage : read output.json\n(GET /metrics — statistics only,\nno orchestrator call)

' --- CLI-driven flow (Pipeline B, not wired to API) ---
Developer --> ScriptOrchestrator : python script.py
ScriptOrchestrator --> PyVRPModel
ScriptOrchestrator --> LoadersSolver
ScriptOrchestrator --> Verifier
ScriptOrchestrator --> Models
LoadersSolver --> Models
ScriptOrchestrator --> DataStorage : read input.json\nwrite output.json

' --- Offline comparison tool, file-based only ---
Developer --> Tester : python tester.py
Tester ..> TestCases : reads
Tester ..> ComparisonFile : reads (if exists) +\nappends sheet

note bottom of VehicleRoutesSolver
  Builds a candidate route pool via Clarke-Wright
  savings + randomized insertion heuristics
  (restarts), then OR-Tools CP-SAT selects the
  optimal subset via set-partitioning.
  Post-processing (still inside this component):
  consolidate_routes() empties lightly-loaded
  vehicles by re-inserting/swap-evacuating their
  orders; merge_multi_trip_routes() combines
  routes into multi-trip assignments where shift
  time allows.
end note

note bottom of MainOrchestrator
  Runs solve_with_feedback(): after the first
  pass, orders whose loader cost exceeds their
  optional_order_penalty are dropped and a second
  pass re-selects from the SAME route pool
  (filtered, not regenerated) for the reduced
  scenario. The cheaper of the two results is kept.
  A single overall deadline (max_total_time,
  default 840s) is distributed across every stage
  instead of each CP-SAT call having its own
  independent fixed limit — see ADR-005.
end note

note bottom of ScriptOrchestrator
  Pipeline B is not reachable through Web/app.py.
  Invoked manually via CLI for offline
  comparison against Pipeline A.
end note

note bottom of Verifier
  Shared between Pipeline A and Pipeline B.
  Verifies shift times, time windows,
  and vehicle capacity against the solution.
end note

note right of History
  New in this version (see ADR-007).
  Records one row per /solve call: timestamp,
  execution_time, objective_function_cost,
  status (processing/success/error), and paths
  to the per-calculation input/output snapshots.
  Only used by the API layer — Pipeline B (CLI)
  never touches it.
end note

@enduml
