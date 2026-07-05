# Meeting Transcript

Speaker 1 is the customer. More about roles in Report on Moodle.

**[00:00:03] Speaker 2**
I will start with how the last week went. Besides developing the algorithms (which is going with varying success), we focused on reviewing the project architecture and cleaned up some dependencies.

**[00:00:32] Speaker 2**
Also, as you requested, we added visual parts: an endpoint to check the correctness of the input file, a display of the waiting time, and metrics so you can view the results and metrics of the built route via a separate endpoint. We sent the tests you recorded last week to the chat: they will need to be re-run for the report, taking into account the new updates (progress bar, metrics, and validation).

**[00:01:15] Speaker 1**
So, is this what is indicated in the instructions - these are the points that need to be covered? Good.

**[00:01:23] Speaker 2**
We also updated some user stories, but more on that later. Work is underway to optimize the algorithm. The algorithm based on CP Solver is being optimized, and following your hint, we are currently writing an algorithm that will cluster points. Regarding user stories, I pass the floor.

**[00:01:58] Speaker 5**
Hello. Yesterday I sent you files regarding user stories. For the current sprint, we took two stories: displaying metrics for managers and minimizing the number of vehicles used. We also added two technical tasks (not related to user stories): based on your feedback about displaying time (so it's visible that the algorithm is working and not just hanging) and adding an endpoint for input JSON file validation.

**[00:02:45] Speaker 1**
Look, when I launch a calculation, I will see how much time it took in the end. We have an established limit, and it needs to be adhered to so that I can check it directly through the interface rather than running your algorithm separately. Also regarding validation: you included the validation result in the plan - which rules are violated and what is the difference in the objective function. This is needed so I can look at the values from your service and compare them with the baseline. All of this looks necessary.

**[00:03:50] Speaker 1**
Also, perhaps a useful feature would be to store the history of calculations. So that one could run calculations and then look at the metrics for all of them - something like a table or dashboard. This is probably beyond the scope of the calculation service itself, an additional feature for analyzing a group of calculations. It's not mandatory, at your discretion. Overall, I can gather the data for each calculation separately.

**[00:04:58] Speaker 5**
Could you explain in more detail what that means? We run the algorithm, and during the calculation, it leaves in history which routes it calculated, which it discarded, or what does it mean? I didn't quite understand.

**[00:05:13] Speaker 1**
No, it means that having launched 10 scenarios, I can see them all in the interface and check what the objective function was and what the answer was. Either download the solution file or open a separate window with the JSON of this solution. It would be convenient for me to see this as a table showing the solution time and the objective function.

**[00:05:54] Speaker 1**
And, of course, if calculations violate hard constraints, it's necessary to understand whether there were violations or not. This concerns interface expansion. We would have to think about storing results, databases, or something similar. It's optional, upon request. If there are no more critical tasks for the interface, then this priority feature would reduce verification time.

**[00:06:48] Speaker 1**
It would be ideal to embed the baseline to immediately see the scenario and its baseline. But we might deviate from fixed scenarios and test changing parameters, in which case we won't have a baseline, and it's unclear how to bypass that. Therefore, we won't touch the baseline. A history of calculations with key metrics (execution time and objective function) would be enough.

**[00:07:38] Speaker 5**
Understood. Are there any other questions regarding the current user stories, or can we add something else?

**[00:07:48] Speaker 1**
Not regarding user stories for now.

**[00:07:51] Speaker 5**
Okay, understood. Overall, I think that's all for this part. I pass the floor.

**[00:08:15] Speaker 3**
Currently, we have two versions of the algorithm. We moved away from the first one I talked about in the last call, as it reached its performance limit. I will tell you about the newest version: it is not the main one yet, but in theory, it should be the most efficient. Here, vehicles and loaders are built in parallel; we don't use PyVRP. First, a greedy distribution of vehicles and loaders is built.

**[00:09:10] Speaker 3**
Next, we randomly select 5% to 10% of the points and cut them out of the routes (in the cut-out places, a direct road simply appears between the previous and the next point). Then we look for how to combine the cut-out points into existing routes. At the same time, the loaders that were cut out are "forgotten," and when inserting a point into a route, we look for new loaders who could process it.

**[00:10:08] Speaker 3**
We repeat this until the time limit is reached. At each stage, a more optimal variation is selected; this way, we should get a sufficiently optimized algorithm. If we see no significant changes, we do a stress test: we cut out 30-50% of the points at once and try to reform the slices. On the largest test case (1000 points), we manage to do about 8000 iterations. So far, this is an algorithm under development.

**[00:11:25] Speaker 1**
There is an analogy here with a genetic algorithm. There are also heuristics like 2-opt and 3-opt. You can look into them - they are for solving VRP problems. In the solvers you considered, they are already built-in, but for your purposes, it might be useful to consider them separately. Returning to your solution: the initial solution was built on PyVRP, how many cases were you able to surpass the baseline?

**[00:12:24] Speaker 3**
On PyVRP - 5, but now we have an algorithm that surpasses it in 7-8 cases out of 10.

**[00:12:40] Speaker 1**
And what is the execution time?

**[00:12:45] Speaker 3**
15 minutes.

**[00:12:54] Speaker 1**
That is an acceptable calculation time. 7 out of 10 is a good result. No questions regarding the algorithm for now. Last week, if I'm not mistaken, we said it was only 1 out of 10? Or did I misunderstand?

**[00:13:51] Speaker 3**
My colleague will tell you about that. If there are no questions about this algorithm, I pass the floor, and we will talk about the algorithm that is currently running.

**[00:14:03] Speaker 1**
Okay.

**[00:14:12] Speaker 4**
Good afternoon. Last week you gave a hint on how to optimize the algorithm via CP Solver and route generation. We started working on it, but encountered difficulties integrating this algorithm. I decided to focus on a more trivial task: whether optional orders can be removed when recalculating costs for loaders. Previously, the algorithm compared the cost of vehicles (whether it's cheaper to pay a penalty rather than paying for vehicle transport and salary). In the current solution, it performs another operation: it checks if savings can be made considering loader salaries and movements. But so far, there have been glitches - the algorithm exceeds the time limit. In recent cases, it takes more than 15 minutes to generate and solve routes.

**[00:15:35] Speaker 4**
In general, I was dealing with architectural solutions: making a complete structure of the algorithm, dividing it into parts, adding logging and outputting metrics for problem-solving.

**[00:15:54] Speaker 1**
I have a question, more about attentiveness. When you looked at the problem statement, did you notice that one vehicle can have multiple routes?

**[00:16:33] Speaker 4**
We haven't even calculated that yet. We only factored in capacity and volume, using one route per vehicle.

**[00:16:44] Speaker 1**
We need to proceed from the data. This is a spoiler: there is such a possibility, and it might be that we have disproportionate weights. It turns out we fulfill orders, the route ends up very short, but we can't add anything more to it because the volume is full. In this case, we can sift through all the selected short routes and try to stitch them together, getting rid of several vehicles by grouping orders into two routes for a single vehicle.

**[00:17:55] Speaker 1**
You can do analytics in this direction: how many short routes are generated right now. If there are many, evaluate the feasibility of adding logic for two routes. This doesn't fall within the scope of classic VRP solvers, although some have settings where one vehicle can perform multiple routes - you just need to activate it. The question is how well it will calculate. You can evaluate this yourselves. This direction is not being actively explored, but there are opportunities there.

**[00:18:57] Speaker 4**
Okay, understood. One of the tasks of our algorithm is to reduce the number of vehicles by increasing the number of orders per route. Am I correct in understanding that there still remain small routes with orders that are inconvenient to fit into others? If we take them all together, group them, and use a separate algorithm to check if they can be combined into one route, will we be able to reduce the number of vehicles?

**[00:19:35] Speaker 1**
Yes. I would suggest considering heavy orders in a separate iteration - identify those that take up a lot of space. Because right now your routes might dilute large orders with small ones, resulting in a decent long route. But you could add more small orders and remove the large ones, inserting them into a second iteration.

**[00:19:35] Speaker 1**
First of all, look at the scenario data: sort the volumes, estimate how much space an order takes. If it takes about 30% of the volume, you can group 3 such orders of 30%. This will result in a dense short route that can be executed quickly. Large orders can be handled before or after general optimization.

**[00:21:08] Speaker 4**
Okay, understood. We still have the question of whether it's profitable to mix this algorithm, as the current solution slightly exceeds the time limits and needs revisiting. Alright, we have noted the suggestion.

**[00:21:27] Speaker 1**
When breaking down the task, the pieces work much faster. Decomposition leads to losing some optimality, but you get a more targeted search where heuristically you calculated it to be profitable. We don't lose that much optimality compared to solving the problem all at once. How promising this direction is - is up to you to decide. I'm not forcing it, just highlighting that the conditions state this can be done. In the routine of development, this possibility slipped your mind; this is a reminder.

**[00:22:45] Speaker 4**
Alright. My colleague and I will continue working on the new algorithm, which indirectly describes your idea from the last call. We will consider all the accumulated ideas separately.

**[00:23:05] Speaker 1**
Okay, thank you.

**[00:23:18] Speaker 2**
Hello again. I would like to discuss the quality criteria that should be reflected in the report. From last week, we have: service responsiveness (regardless of the calculation stage), input data validation, and the impossibility of accessing the API without a key. This week we added a point about documentation (where we will describe the repository and project structure in more detail). We also moved from user stories to quality criteria the point that the algorithm must execute within 15 minutes.

**[00:24:38] Speaker 1**
I have a suggestion regarding the progress bar. Inside the algorithm, there are certain stages; you can tie them to the progress bar and output the percentage of stages completed. We are focusing not on time remaining, but on stages: how many stages have been completed and how many are left, to understand the phase when requesting the solution. Right now, waiting is like a black box: I get a "calculating" status back, but if there is an error and the status hangs, how do I know the calculation hasn't died? With stages, you could see that it's stuck at a certain percentage and hasn't changed for a long time.

**[00:26:02] Speaker 1**
Right now, the indicator is binary: either we are calculating, or it's 100% done - this creates uncertainty. I suggest introducing a progress bar based on algorithm stages. There is no stable version of the algorithm right now, so defining the stages is problematic, but closer to the 21st, it would be nice to add a percentage for the stages. You can estimate it yourselves: 15 minutes can be tied to stages, but it's statistical work. Even if stages vary, just seeing that a stage is completed is a plus. It will clear up the misunderstanding of what is happening.

**[00:27:45] Speaker 2**
Okay. Another question: should we still stay within the API framework, with endpoints showing metrics, or do we need some visual representation?

**[00:28:12] Speaker 1**
That's a question of what you want.

**[00:28:16] Speaker 2**
We would prefer, as originally planned, to stay within the endpoints.

**[00:28:25] Speaker 1**
Yes, then we will stick with them.

**[00:28:32] Speaker 2**
I think that's all we wanted to discuss. Once again, we ask you to record the tests we sent in your free time, taking the new functionality into account.

**[00:28:47] Speaker 1**
Okay, go through all these scenarios, through the history, right?

**[00:28:52] Speaker 2**
For the report, we will need to go through them again, including the old ones.

**[00:28:58] Speaker 1**
Yes, saw it. Okay, I will do it. I'll send it over the weekend in the same format.

**[00:29:10] Speaker 2**
Thank you. That's all from our side.

**[00:29:15] Speaker 1**
I have no questions for now. If any thoughts arise regarding interaction or something critical is missing, I won't wait for a status update, I'll write in the chat. I hope everything will be okay. Have a good day, everyone. Thank you.

**[00:29:37] Speaker 2**
Goodbye. You too.
