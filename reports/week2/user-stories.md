
# User Story

## US-01: Display final route map

**Requirement status:** Removed

**Previous MoSCoW priority:** Won't Have

As a driver,
I want to see an interface with the final map,
so that I can see the current route clearly.


**Reason:** 

User Story US-01 has been removed because in its original form it had a "Won't Have" priority, but the customer asked not to include such stories in the backlog. Additionally, it was a story about a "map", whereas the actual driver's need, according to the customer's feedback, is to receive a ready-made route and not have to plan it themselves. Therefore, this story has been replaced with US-11.


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

**MoSCoW priority:** Should Have

As a manager,
I want the system to remain fast and responsive as the number of orders grows,
so that I can expand the customer base without losing quality of management.

### Notes and constraints

This user story originally had a "Must Have" priority but was downgraded to "Should Have". The system architecture must support client base growth without performance degradation; however, full scalability is not required for the MVP.


## US-04: Track deliveries for one vehicle

**Requirement status:** Removed

**Previous MoSCoW priority:** Won't Have

As a manager,
I want to see how many deliveries each vehicle has completed,
so that I can make decisions about bonuses.


**Reason:**

The story does not align with the target roles and interests defined by the customer. The manager is interested in resource optimization and quality of management, not in calculating bonuses. This functionality does not affect route planning and is not required for the MVP.

## US-05: Optimal routing

**Requirement status:** Removed 

**Previous MoSCoW priority:** Should Have

As a driver,
I want to have the most optimal routing possible,
so that I can save time and money on fuel.

**Reason:**

US-05 has been removed because in its original formulation "saving money on fuel" was specified as a driver's need. However, according to the customer's feedback, the driver's interest is to reduce responsibility and comply with shift duration, not to save company resources. Fuel economy is a manager's task for resource optimization. Therefore, the story has been rewritten and moved to US-12


## US-06: One vehicle per client

**Requirement status:** Active

**MoSCoW priority:** Could Have

As a manager,
I want to use only one vehicle for each client,
so that I can reduce the total number of vehicles needed.

### Notes and constraints

This user story has priority "Could Have" because it offers a possible improvement for fleet efficiency, but it is not essential for the basic system to work.


## US-07: Prioritizing delivery refusals

**Requirement status:** Removed

**MoSCoW priority:** Won't Have

As a manager,
I want to decide when to decline a delivery and when not to,
so that I can always process the most important orders first.

**Reason:**

The story contradicts a key technical constraint specified by the customer: the system recalculates routes once per morning with no dynamic changes during the day. Prioritizing delivery rejections would require real-time route recalculation, which the customer has excluded from the current scope of work. This story has been removed because it cannot be implemented within the agreed constraints.


## US-08: Independent work of loaders and trucks

**Requirement status:** Active

**MoSCoW priority:** Should Have

As a manager,
I want the program to build independent routes for trucks and loaders,
so that I can increase efficiency.

### Notes and constraints

This user story has priority "Should Have" because this feature improves work organization, but it is not critical for the MVP. It can be implemented when expanding functionality.


## US-09: Account for loaders' time windows

**Requirement status:** Removed

**Previous MoSCoW priority:** Must Have

As a manager,
I want the program to account for loaders' time windows,
so that all routes are feasible and loaders finish their shift on time.


**Reason:**

This story was written from the manager's perspective, but the customer explicitly defined that drivers and loaders have a direct interest in "adhering to shift duration" and "reducing responsibility." The requirement to respect time windows primarily serves the interests of drivers and loaders, not the manager. Therefore, the story has been rewritten from the correct role perspective and moved to US-13. 


## US-10: Account for vehicle capacity

**Requirement status:** Active

**MoSCoW priority:** Must Have

As a manager,
I want the program to account for vehicle capacity,
so that it builds feasible routes that respect all constraints.

### Notes and constraints

This user story has priority "Must Have" because accounting for vehicle capacity is important for correct order distribution and building feasible routes.



## US-11: Receiving a pre-planned route (revised from US-01)

**Requirement status:** Active

**MoSCoW priority:** Must Have

As a driver or loader,
I want to receive a specific, pre-planned route,
so that I do not have to plan it myself.

### Notes and constraints

*This is a revised version of US-01.*

This story has a "Must Have" priority because drivers and loaders are interested in reducing responsibility and want to follow ready-made routes rather than doing their own planning. The route should be fixed for the shift.


## US-12: Optimal routing for resource savings (revised from US-05)

**Requirement status:** Active

**MoSCoW priority:** Should Have

As a manager,
I want the system to build routes that are optimally efficient in terms of time and mileage,
so that I can reduce fuel costs and shorten delivery times.

### Notes and constraints

*This is a revised version of US-05.*

This story has a "Should Have" priority because the manager is interested in optimizing resource usage and reducing operational costs. The basic version may use simple algorithms.

## US-13: Respecting time windows to finish shift on time (revised from US-09)

**Requirement status:** Active

**MoSCoW priority:** Must Have

As a driver or loader,
I want the system to take my individual time windows into account,
so that I can finish my shift on time.

### Notes and constraints

*This is a revised version of US-09.*

This story has a "Must Have" priority because drivers and loaders are interested in adhering to shift duration. Without respecting time windows, the system might assign routes that exceed working hours, making the plan infeasible. The original version was rewritten from the manager role to the executor role in accordance with the target interests defined by the customer.


## Initial proposed MVP v1 scope

The following active Must Have user stories are proposed for the initial MVP v1 scope. This scope ensures that drivers and loaders receive a ready-made route that respects basic feasibility constraints: vehicle capacity and individual time windows. The system will produce a fixed, feasible route per shift without requiring real-time changes or advanced optimization.

- US-10: Account for vehicle capacity

- US-11: Receiving a pre-planned route (revised from US-01)

- US-13: Respecting time windows to finish shift on time (revised from US-09)
