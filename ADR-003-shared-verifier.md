@startuml sequence-diagram
title Route Optimization Platform — Sequence Diagram (Dynamic View): /solve, /solution, /validate, /metrics, /history

actor "API Client" as Client
participant "Flask API\n(Web/app.py)" as API
participant "Validator\n(Web/validator.py)" as Validator
participant "History\n(Shared/history.py)" as History
participant "Solver Thread" as Thread
participant "Orchestrator\n(CP-SAT/main.py)" as Orchestrator
participant "Vehicle Routes Solver\n(CP-SAT/vehicle_routes.py)" as VehicleSolver
participant "Loader Routes Solver\n(CP-SAT/loader_routes.py)" as LoaderSolver
participant "Verifier\n(Shared/verifier.py)" as Verifier
database "Data Storage\n(input.json / output.json,\ndata/inputs, data/outputs)" as Storage
database "history.db" as DB

== POST /solve ==

Client -> API : POST /solve\n(X-API-Key, JSON payload)
activate API
API -> API : require_api_key()
API -> Validator : validate_input(data)
activate Validator
Validator --> API : ok / ValidationError
deactivate Validator

alt validation failed
  API --> Client : 400 {status: error, errors}
else validation ok
  API -> History : start_calculation(input_data)
  activate History
  History -> DB : INSERT (status="processing")
  History -> Storage : write data/inputs/{id}.json
  History --> API : calculation_id
  deactivate History
  API -> Storage : write input.json (live scratch file)
  API -> API : solver_state = {status: computing,\ncalculation_id, stage: "starting"}
  API -> Thread : start(target=run_solve, args=(calculation_id,))
  activate Thread
  API --> Client : 202 {status: started, calculation_id}
  deactivate API

  Thread -> Orchestrator : solve_pipeline(input_path, output_path,\non_stage, run_feedback, time_limit,\nmax_total_time)
  activate Orchestrator
  Orchestrator -> Orchestrator : deadline = now + max_total_time

  Orchestrator -> Thread : on_stage("parsing")
  Thread -> Thread : solver_state.stage = "parsing"
  Orchestrator -> Orchestrator : parse(input.json)

  Orchestrator -> Thread : on_stage("solving")
  Thread -> Thread : solver_state.stage = "solving"

  Orchestrator -> Thread : on_stage("solving_vehicles")
  Thread -> Thread : solver_state.stage = "solving_vehicles"
  Orchestrator -> VehicleSolver : find_vehicles_routes(scenario, deadline, ...)
  activate VehicleSolver
  note right of VehicleSolver
    Clarke-Wright savings + randomized insertion
    heuristics build a route pool within its own
    pool_deadline; CP-SAT selects the optimal
    subset via set-partitioning.
  end note
  VehicleSolver --> Orchestrator : solution, missed_count, vehicle_pool
  deactivate VehicleSolver

  Orchestrator -> Thread : on_stage("consolidating_vehicles")
  Thread -> Thread : solver_state.stage = "consolidating_vehicles"
  Orchestrator -> VehicleSolver : consolidate_routes(solution, scenario)
  activate VehicleSolver
  VehicleSolver --> Orchestrator : consolidated vehicles
  deactivate VehicleSolver
  Orchestrator -> VehicleSolver : merge_multi_trip_routes(solution, scenario)
  activate VehicleSolver
  VehicleSolver --> Orchestrator : merged vehicles
  deactivate VehicleSolver

  Orchestrator -> Thread : on_stage("solving_loaders")
  Thread -> Thread : solver_state.stage = "solving_loaders"
  Orchestrator -> LoaderSolver : find_loaders_routes(solution, scenario, deadline, ...)
  activate LoaderSolver
  LoaderSolver --> Orchestrator : loaders
  deactivate LoaderSolver
  Orchestrator -> Orchestrator : calculate_statistics(solution)

  alt unprofitable optional orders found\n(loader cost > order_penalty)\nAND time remaining > MIN_TIME_FOR_FEEDBACK
    Orchestrator -> Thread : on_stage("feedback_iteration")
    Thread -> Thread : solver_state.stage = "feedback_iteration"
    Orchestrator -> Orchestrator : filter vehicle_pool\n(drop routes touching bad optional orders)
    Orchestrator -> VehicleSolver : select_routes_from_pool(filtered_pool,\nreduced_scenario, deadline, ...)
    activate VehicleSolver
    VehicleSolver --> Orchestrator : solution2, missed_count2
    deactivate VehicleSolver
    Orchestrator -> VehicleSolver : consolidate_routes() +\nmerge_multi_trip_routes() (reduced_scenario)
    activate VehicleSolver
    VehicleSolver --> Orchestrator : solution2 (post-processed)
    deactivate VehicleSolver
    Orchestrator -> LoaderSolver : find_loaders_routes(solution2, reduced_scenario, deadline, ...)
    activate LoaderSolver
    LoaderSolver --> Orchestrator : loaders2
    deactivate LoaderSolver
    Orchestrator -> Orchestrator : calculate_statistics(solution2)
    Orchestrator -> Orchestrator : keep cheaper of solution / solution2
  end

  Orchestrator -> Storage : write output.json

  Orchestrator -> Verifier : run_verification(input_path, output_path)
  activate Verifier
  Verifier -> Storage : read input.json
  Verifier -> Storage : read output.json
  Verifier --> Orchestrator : verification result
  deactivate Verifier
  Orchestrator -> Orchestrator : solution["verification"] = verification
  Orchestrator -> Storage : write output.json

  Orchestrator -> Thread : on_stage("done")
  Thread -> Thread : solver_state.stage = "done"
  Orchestrator --> Thread : solution
  deactivate Orchestrator

  Thread -> History : finish_success(calculation_id, output_data,\nexecution_time, objective_function_cost)
  activate History
  History -> Storage : write data/outputs/{id}.json
  History -> DB : UPDATE status="success", execution_time,\nobjective_function_cost, output_json_path
  deactivate History
  Thread -> Thread : solver_state = {status: done, calculation_id}
  deactivate Thread
end

alt an exception is raised anywhere in run_solve()
  Thread -> Thread : solver_state = {status: error,\ncalculation_id, message}
  Thread -> History : finish_error(calculation_id, error_message,\nexecution_time)
  activate History
  History -> Storage : write data/outputs/{id}.json\n({"error": message})
  History -> DB : UPDATE status="error", output_json_path
  deactivate History
end

== GET /solution (polling) ==

... later, client polls ...

Client -> API : GET /solution
activate API
API -> API : require_api_key()
alt status == computing
  API --> Client : 200 {status: computing, calculation_id, stage: <current stage>}
else status == done
  API -> Storage : read output.json
  Storage --> API : solution JSON
  API --> Client : 200 {status: done, solution}
else status == error
  API --> Client : 500 {status: error, message}
else status == idle (no solve started yet)
  API --> Client : 200 {status: idle, message}
end
deactivate API

== POST /validate ==

Client -> API : POST /validate\n(JSON payload, no API key required)
activate API
API -> Validator : validate_input(data)
activate Validator
Validator --> API : ok / ValidationError
deactivate Validator
alt input valid
  API --> Client : 200 {status: ok}
else input invalid
  API --> Client : 400 {status: error, errors: [{path, message}, ...]}
end
deactivate API

== GET /metrics (polling) ==

Client -> API : GET /metrics
activate API
API -> API : require_api_key()
alt status == computing
  API --> Client : 200 {status: computing, calculation_id, stage: <current stage>}
else status == done
  API -> Storage : read output.json
  Storage --> API : solution JSON (statistics field)
  API --> Client : 200 {status: done, metrics: {total_cost, fuel_cost,\nvehicle_salaries, loader_salaries,\nloader_work_cost, penalties,\nvehicles_used, loaders_used}}
else status == error
  API --> Client : 500 {status: error, message}
else status == idle (no solve started yet)
  API --> Client : 200 {status: idle, message}
end
deactivate API

== GET /history ==

Client -> API : GET /history
activate API
API -> API : require_api_key()
API -> History : get_all()
activate History
History -> DB : SELECT calculation_id, timestamp,\nexecution_time, objective_function_cost,\nstatus ORDER BY calculation_id DESC
History --> API : list of summary records
deactivate History
API --> Client : 200 {history: [...]}
deactivate API

== GET /history/{calculation_id} ==

Client -> API : GET /history/{calculation_id}
activate API
API -> API : require_api_key()
API -> History : get_by_id(calculation_id)
activate History
History -> DB : SELECT * WHERE calculation_id = ?
alt row found
  History -> Storage : read input_json_path\nread output_json_path
  History --> API : full record (metadata + input + output)
  API --> Client : 200 {record}
else row not found
  History --> API : null
  API --> Client : 404 {status: error, message: "Not found"}
end
deactivate History
deactivate API

@enduml
