
# User Story

## US-01: Display final route map

**Requirement status:** Active  

**MoSCoW priority:** Won't Have  

As a driver,  
I want to see an interface with the final map,  
so that I can see the current route clearly.

### Notes and constraints

This user story has priority "Won't Have" because a map interface for drivers is not required. Drivers can receive routes in text format or as a list.

## US-02: Fast program startup

**Requirement status:** Active  

**MoSCoW priority:** Should Have  

As a manager,  
I want to receive route plans within 15 minutes,  
so that deliveries can begin without waiting.

### Notes and constraints

This user story has priority "Should Have" because speed is important for responsiveness, but it is not critical for basic functionality.


## US-03: Manage a large number of clients

**Requirement status:** Active 

**MoSCoW priority:** Must Have  

As a manager,
I want the system to remain fast and responsive as the number of orders grows,
so that I can expand the customer base without losing quality of management.

### Notes and constraints

This user story has priority "Must Have" because the architecture must support client base growth without hurting performance.


## US-04: Track deliveries for one vehicle

**Requirement status:** Active

**MoSCoW priority:** Won't Have  

As a manager,  
I want to see how many deliveries each vehicle has completed,  
so that I can make decisions about bonuses.

### Notes and constraints

This user story has priority "Won't Have" because this feature is completely not required for the task we were given, even though it is useful for motivation.


## US-05: Optimal routing

**Requirement status:** Active  

**MoSCoW priority:** Should Have  

As a driver,  
I want to have the most optimal routing possible,  
so that I can save time and money on fuel.

### Notes and constraints

This user story has priority "Should Have" because route optimization is desirable, but the basic version can work with simple algorithms. Full optimization can be added in future iterations.


## US-06: One vehicle per client

**Requirement status:** Active  

**MoSCoW priority:** Could Have  

As a manager,  
I want to use only one vehicle for each client,  
so that I can reduce the total number of vehicles needed.

### Notes and constraints

This user story has priority "Could Have" because it offers a possible improvement for fleet efficiency, but it is not essential for the basic system to work.

## US-07: Prioritizing delivery refusals

**Requirement status:** Active  

**MoSCoW priority:** Won't Have  

As a manager,  
I want to decide when to decline a delivery and when not to,  
so that I can always process the most important orders first.

### Notes and constraints

This user story has priority "Won't Have" because the system recalculates routes only once in the morning with no dynamic changes, as requested by the customer.


## US-08: Independent work of loaders and trucks

**Requirement status:** Active  

**MoSCoW priority:** Should Have  

As a manager,  
I want the program to build independent routes for trucks and loaders,  
so that I can increase efficiency.

### Notes and constraints

This user story has priority "Should Have" because this feature improves work organization, but it is not critical for the MVP. It can be implemented when expanding functionality.


## US-09: Account for loaders' time windows

**Requirement status:** Active  

**MoSCoW priority:** Must Have  

As a manager,  
I want the program to account for loaders' time windows,  
so that all routes are feasible and loaders finish their shift on time.

### Notes and constraints

This user story has priority "Must Have" because without this feature, routes might assign loaders outside their working hours, making routes impossible to complete.


## US-10: Account for vehicle capacity

**Requirement status:** Active  

**MoSCoW priority:** Must Have  

As a manager,  
I want the program to account for vehicle capacity,  
so that it builds feasible routes that respect all constraints.

### Notes and constraints

This user story has priority "Must Have" because accounting for vehicle capacity is important for correct order distribution and building feasible routes.


## Initial proposed MVP v1 scope

The following active Must Have user stories are proposed for the initial MVP v1 scope. This scope ensures that basic route feasibility constraints (vehicle capacity and loaders' time windows) are respected. US-03 is a Must Have for the final product but is excluded from the initial MVP to reduce complexity.

- US-09: Account for loaders' time windows
- US-10: Account for vehicle capacity
