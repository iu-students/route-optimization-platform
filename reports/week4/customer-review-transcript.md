# Meeting Transcript

Speaker 1 is the customer. More about roles in Report on Moodle.

**[00:00:02] Speaker 3:** 
I’ll probably start with the current stage of the project and what we’ve done since our last meeting. Overall, this week we focused more on testing from different angles: from the user experience perspective and the correctness of the provided solution. 

**[00:00:38] Speaker 3:** 
We are also continuing to develop two versions of the algorithm in parallel. One is the current MVP with greedy distribution, and we are improving its performance. The second is the one we discussed last time, with CP Solver.

**[00:01:08] Speaker 3:** 
As part of one of the reports, we need you to follow the instructions we sent before the meeting to evaluate the product from a user's perspective: how convenient and understandable it is to use. At the end of the meeting, the developers will once again talk about the baseline comparison results and the current state of the algorithm. 
From the tests checking quality, we highlighted three main ones. First, the system must be responsive regardless of the computation stage; it should be clear that it is working. Second, protection against incorrect requests. Third, access to the solver only via API key (which is already partially implemented). Regarding user stories, we will discuss that too. I pass the floor.

**[00:02:56] Speaker 4:** 
Hello. I sent a file with the new sprint. It includes new user stories based on your feedback: about handling optional orders and metrics for the manager. We decided not to take the manager metrics into the current sprint; we will do it later. In this sprint, we are looking at the independent work of loaders and trucks, as well as handling optional orders. Everything is broken down into subtasks, and JSON file verification was added as a technical task.

**[00:03:48] Speaker 4:** 
That's all for user stories. But regarding the report, we need to discuss how accurately we are following your feedback. From the last meeting: we added a story about optional orders and took it into the sprint. We also added a story about the manager so they can track route efficiency. There were questions about GitHub formatting - we checked against the requirements, and our repository complies with them. And you asked for a baseline comparison - we will discuss that later with other team members.

**[00:04:45] Speaker 1:** 
I didn't have time to familiarize myself with all the files. I read the user stories; they are complete now. No questions on technical issues either. I have a question regarding the solution: since there are user stories, we need to introduce some statistics on the solution's quality. The validator roughly provides this; we could tailor the code to the validator to parse and output this information.

**[00:05:33] Speaker 1:** 
Regarding interaction with the model: I launched the calculation, and there wasn't enough interactivity. I sit there like in a closed box, click "check status", and it just says "processing", and it's unclear when it will end. 
I didn't have time to look at the rest of the files. I started opening the comparison, but we'll touch on that now. I didn't look at the UAT, but I assume it's an instruction I need to follow, recording a video as confirmation. Meaning, format the requests, record everything, and send you my user experience?

**[00:06:55] Speaker 4:** 
Actually, according to the task, this should be done right on the call. But if it's more convenient for you this way, I think it's possible.

**[00:07:07] Speaker 1:** 
You sent me a case. Do I need to test this specific case, or should I generally test my own?

**[00:07:22] Speaker 5:** 
There is already a test example on the server. In general, you can test your own data, it makes no difference. We sent you a file with input data for convenience. Choose what's more convenient: we can do it right now, verbally walk through the process, record a screen demonstration, or you can do it all later independently and send it. What is more convenient for you right now?

**[00:08:15] Speaker 1:** 
Let me check on my side and record a video. Just a screen broadcast without my video, record it anonymously, and send it, right?

**[00:08:26] Speaker 5:** 
Yes, that will be enough.

**[00:08:29] Speaker 1:** 
Good. Regarding scenarios: you provided yours, but I tried substituting my own. I think I'll run a few of my own. The question is about calculation delay: do I need to record the video including the waiting time?

**[00:08:54] Speaker 5:** 
The requirements state that a response is expected within two minutes. We have a time limit: if the calculation exceeds the limit, it terminates. It would be great to show in real time that the system actually meets this requirement.

**[00:09:17] Speaker 1:** 
So, three scenarios will take six minutes. Good. Is there an option to validate the result? To send it for validation.

**[00:09:47] Speaker 5:** 
Yes, in version MVP 1, the solution file outputs the solution itself first, and then the validator's response. It's all in the same output data.

**[00:10:08] Speaker 1:** 
I tried launching the file via the form. It seems a JSON format was returned. Okay, I'll figure it out or check with you.

**[00:10:25] Speaker 3:** 
A JSON format is returned. As of the last call, this wasn't there, but now it returns a JSON with the built route and the validator's response (which tests passed and which didn't).

**[00:10:45] Speaker 1:** 
Good. Expect a video from me over the weekend. Please don't turn off or break the current server, leave it accessible. I'll record and send it: if it's a large video - via cloud drive, if not - in the chat. Should I accompany the video with comments? And should I demonstrate that I'm checking the result's correctness somewhere else separately? For example, running the validator on my side and comparing, or is that unnecessary? Good, agreed.

**[00:11:51] Speaker 5:** 
We don't have that in the requirements.

**[00:11:56] Speaker 1:** 
Good, agreed. We can move on to... What are we on now? Did we send it or not?

**[00:12:13] Speaker 2:** 
Hello. As already mentioned, there are two versions of the algorithm: the new one and a modification of the previous one with greedy sampling. You advised adding a check after the algorithm finishes to identify unprofitable points. This check was added, and the algorithm showed an increase in efficiency on 6 out of 10 tests up to 4%. On one test, it lost 1%, and on the rest, it remained unchanged. 
Compared to the baseline: on 5 out of 10 tests, the algorithm significantly beats the baseline (tests 5, 6, 7, 8, 9), with an average increase of 20-50%. On the remaining tests, the algorithm is worse than the baseline by up to 15% (by 4%, 2%, 9%, 15%). So, on the tests where it is better, the gain is more significant than the loss on the others.

**[00:14:12] Speaker 1:** 
By a binary attribute, all should be better. We need to work on the remaining scenarios. Did you analyze the penalty structure of the baseline and your solution? Did you only submit data for three test scenarios?

**[00:14:51] Speaker 2:** 
Yes, we will send the rest a bit later. The data exists, but it's not compiled into a table.

**[00:15:00] Speaker 1:** 
The question is more for you: did you look at where there is potential to reduce penalties?

**[00:15:14] Speaker 2:** 
As far as I noticed, the baseline skips many points unlike our algorithm. Maybe we should look into this: it considers many more points inefficient to visit. That's all for this version of the solution based on the single algorithm.

**[00:15:55] Speaker 1:** 
Do you have ideas on how to improve the other 5 tests?

**[00:16:01] Speaker 2:** 
I have an idea. Right now, only the loaders know which points shouldn't be visited. That's the problem. We plan to exclude these points from the general pool and rebuild routes for the vehicles, but this will require a lot of time, as each route construction is a new calculation. 10 reworks would be too many. We are currently thinking about how to solve this.

**[00:16:52] Speaker 1:** 
Right now, you've done the filtering of optional orders after the calculation. You could also embed the order weight inside the algorithm.

**[00:17:16] Speaker 2:** 
I thought about that. The problem is that the algorithms for vehicles and loaders are still not linked. How to link them is what I plan to work on.

**[00:17:41] Speaker 1:** 
For optional orders without loaders, the issue is resolved. The question here is how to change the penalty for non-fulfillment. We need to consider average statistics on how many loaders will have to be hired to fulfill a particular order. Are you using PyVRP?

**[00:18:39] Speaker 2:** 
PyVRP for vehicles, and our own algorithm for loaders.

**[00:18:47] Speaker 1:** 
I suggest starting with an analysis of the baseline: see the difference in the penalty structure, what causes the loss. Maybe your vehicles are doing too well, and there's no room left for loaders. You could work with delivery windows: narrow the wide windows in the direction needed for loaders. You could first plan the loaders via PyVRP, evaluate the minimized windows, and embed them into the first stage of vehicle planning. Narrowing windows might help if the bottleneck is with the loaders. It also depends on where your bottleneck is.

**[00:20:28] Speaker 2:** 
There is a foundation in the architecture for such an idea. The internal exchange files are designed to save all windows and vehicles.

**[00:21:17] Speaker 1:** 
Do you do a fix? But from the first stage, you already fix the specific arrival time.

**[00:21:33] Speaker 2:** 
It's fixed, but we know how long each order is still available and how much free time the vehicle has within its working hours. We can move these boundaries.

**[00:21:57] Speaker 1:** 
If you know the boundaries, you can form a window for each order and plan the loaders as a VRP.

**[00:22:13] Speaker 2:** 
Yes, but with floating boundaries, we'll have to seriously change the algorithm for loaders. It's more difficult, but it's a direction we can take.

**[00:22:41] Speaker 1:** 
Floating boundaries can be tightened; take the average distance. You can evaluate the loader's first order and calculate a quantile (e.g., 75%) to plan them from the warehouse minus the expected distance. The solution's reliability will drop, but it's workable. Reducing the problem to a VRP via averaging might work for a "good" rather than an optimal solution. The difficulty is in the uncertainty: which distances to take. Routes might turn out suboptimal upon unpacking; we won't be able to remove an order without hiring a new loader. But the direction is effective.

**[00:24:46] Speaker 2:** 
The architecture had a stub to calculate a potential for a point - not the earliest or closest, but something average.

**[00:25:10] Speaker 1:** 
Have you tried the assignment problem? Currently, loaders are distributed greedily, sequentially. That's the downside. The assignment problem looks at distribution across the network as a whole. You could generate "route fragments" (3-4 orders), distribute them to loaders, minimizing the number of loaders and maximizing orders. Then build scenarios further (another 3-4 points) and use an optimization model (assignment problem, set cover problem). You can look deeper (several points ahead) and wider (all loaders at once). It makes sense to go in this direction if the bottleneck is with the loaders.

**[00:28:40] Speaker 1:** 
This is mostly an assignment problem, meaning you generate specific scenarios, specific route fragments, and try to select the highest quality ones from them. You can also go this route by making the first pass truncated, meaning you don't have to fulfill all orders using these routes, but fulfill a certain number of orders and limit the capacity of loaders available. So, you can try going in this direction, but it only makes sense if you see that your bottleneck is couriers.

**[00:29:43] Speaker 6:** 
Good afternoon. Since the last call, I mentioned I was working on an algorithm based on PyVRP and CP Solver, which you mentioned as a possible solution to this problem. During development, I encountered a problem: using PyVRP is not quite suitable for route generation. With multiple calls to PyVRP, we don't have time to find the best route combinations within an acceptable timeframe. Therefore, compared to the baseline and our colleague's solution, my algorithm is a bit sluggish and inferior to the baseline. Besides, it skips some mandatory orders.

**[00:30:40] Speaker 6:** 
Lately, I've been creating a new generator based on two approaches: reducing distance and prioritizing orders that start as early as possible (an approach similar to our colleague's solution). By generating hundreds of thousands of different routes combining orders, we get a large array of data. Then, the CP Solver looks for a combination that can cover all these orders. The same scheme works for loaders: routes are generated, and then the best combinations are assembled via the CP Solver.

**[00:31:29] Speaker 6:** 
But I want to clarify that this is still a greedy algorithm, as we first look for the best path for vehicles and then assemble the path for loaders. This is not the best approach, so in the future, the task will be to search for routes for both vehicles and loaders in parallel. I also sent metrics to the chat, as you requested on the last call. They show a visual comparison of how our solution beats the baseline. Can you open it so I can comment?

**[00:32:16] Speaker 1:** 
I opened it. I generally understand everything written there. I can't open the demonstration on my computer right now, but I can look on my phone.

**[00:32:25] Speaker 6:** 
The main thing is that you see and understand what I'm talking about.

**[00:32:30] Speaker 1:** 
Yes, opened the summary.

**[00:32:34] Speaker 6:** 
The summary shows how many vehicles, loaders, fuel, and other basic characteristics are used in our solution. It can be noted that Version B (my solution via route generation and CP Solver) skips more mandatory orders, probably due to a low penalty. If we tighten the rules, we can achieve passing all orders, but the total sum will be greatly inflated. Below are pages for cases T1, T2, and T3. They show more clearly how everything works.

**[00:33:29] Speaker 6:** 
I would highlight the ratio of the number of orders to slots for loaders and vehicles. In my solution, they are slightly higher compared to the baseline, as we more densely pack vehicles and loaders to have fewer idle windows. Thus, we save on the number of vehicles and loaders used. And the lengths of routes and chains show how many orders, for example, for vehicles, and how many such routes there are.

**[00:34:00] Speaker 6:** 
For example, for Version B, by route lengths we see "2-3", meaning 2 orders together and there are only 3 such routes. And so on: 4 orders across 5 routes. There is data for the colleague's version and the baseline too. We see that the baseline generally uses a smaller number of orders. Chains are about loaders: for example, 1 order per route means up to 8 loaders.

**[00:34:45] Speaker 1:** 
What does the first number represent?

**[00:34:48] Speaker 6:** 
The first number is the number of orders, and the second is the number of such vehicles. Basically, that's all I had to say.

**[00:35:08] Speaker 1:** 
Density probably increases because fewer resources are used?

**[00:35:13] Speaker 6:** 
Yes, that's the main task, and one of the user story requirements is using fewer vehicles.

**[00:35:22] Speaker 1:** 
But does reduction always lead to improvement? Because there are transport costs, and they can be comparable.

**[00:35:34] Speaker 6:** 
Fuel, salaries, and travel time are all calculated.

**[00:35:43] Speaker 1:** 
The higher the costs, the greater the mileage and work. It turns out the amount of resources should increase due to distance. The fewer vehicles we have, the denser they must drive to fit into the shift, and the lower the costs, including fuel. The logic is that reducing the number of vehicles leads to a reduction in transport costs. Understood. Are there any other ideas to try?

**[00:36:40] Speaker 6:** 
Our algorithm is still not perfect, as we first consider paths for vehicles and then for loaders. One of my next ideas is the parallel creation of routes for vehicles and loaders. It seems to me this will allow for more optimized routes and save fuel and salaries.

**[00:37:09] Speaker 1:** 
Initially, we outlined a path of breaking the problem into subtasks by routing layers: loaders in one category, transport in another. Of course, you can decompose it differently. For example, decompose by geography - cluster orders into groups that can be considered independent. Or look at geography and time windows, dividing all orders into several groups. With these groups, using an automated algorithm (like hierarchical clustering), we get several subtasks. These subtasks are smaller, and it's possible to iterate through all combinations and fully optimize them.

**[00:38:28] Speaker 1:** 
How much better this will be needs to be tested. We need to understand how finely we have to split it. For example, if we have 90 orders, should we split them into 3 groups of 30 or 2 of 45 so everything can be calculated and planned. You can go by geography, or by more complex logic considering both geography and time windows.

**[00:39:08] Speaker 1:** 
You can also stratify the orders themselves by time windows and plan based on these levels. First, we try to assign all orders and select the minimum number of couriers to cover the first, most critical level. Overall, this is similar to the sequential algorithm you implemented for loaders, only here the implementation is joint with vehicles and loaders. This is a variant without using VRP, but based on the assignment problem. In general, you can look at it from different angles to see what has potential and what is unpromising.

**[00:40:14] Speaker 6:** 
Okay, understood. I understood it like this: you want us to split orders into groups and then, in parallel, without dividing loaders and vehicles into two categories, run the algorithm jointly and look for the best solution for one group of points, and then for the rest. Am I understanding correctly?

**[00:40:38] Speaker 1:** 
Yes, you understood correctly. This is an idea worth thinking about. You can refine it and not delimit the task so strictly. Perhaps leave some connections between sections or aggregate them. You can also aggregate orders. If orders are close to each other and their windows are roughly the same, you can treat a group of orders as one. You aggregate them, plan routes by these large sections, and then examine them in detail. Once the general route is clear, you just form routes for specific orders.

**[00:41:48] Speaker 1:** 
For example, you grouped 5 orders similar in windows and geography. All orders are grouped, and instead of 100, you get 20. For these 20, you build routes, and inside them, you do the breakdown into specific orders. First you aggregate, then you disaggregate. This is also an idea that can greatly simplify the task. The question is whether important information will be lost during such aggregation, and how critical it is for a high-quality solution. These are just ideas for your evaluation. You don't need to take all the proposed options; you can sift through them or build your own solutions based on them. I'm just showing what mechanisms and options for interpreting the task exist.

**[00:43:12] Speaker 6:** 
Yes, I understand everything. Thank you very much. Your ideas correlate with my further development plans, namely the parallel creation of routes for loaders and vehicles. It looks well-implementable, so we will take it on board. Thank you.

**[00:43:49] Speaker 3:** 
That's probably all from our side. The only thing is, regarding quality assessment criteria: do you have any requirements or suggestions on how fast, responsive, convenient, and secure the system should be? This also needs to be reflected in the report.

**[00:44:23] Speaker 1:** 
Regarding interaction, I already said at the beginning that the uncertainty in waiting is very confusing. It's unclear if something broke or not. An error test is needed. I can run incorrect data myself. The question is: will there be validation? I saw a plan for implementing data format validation.

**[00:44:56] Speaker 3:** 
That is one of the tasks we plan to complete this week.

**[00:45:05] Speaker 1:** 
Excellent. Then I will be able to test it during the recording. A system crash is also an expected scenario that needs to be checked. I plan to record the video on Saturday or Sunday evening. I don't know if there will be an update. If anything, simulate that you updated it, and it can be checked.

**[00:45:37] Speaker 3:** 
Yes, good. It is preferable for us if the recording is closer to Saturday.

**[00:45:47] Speaker 1:** 
I think it's not critical. I will record the video, I hope everything goes smoothly. Alright, the recording and test are on me. We will meet next week. Once everything is ready, I'll drop it in the chat.

**[00:46:22] Speaker 3:** 
Thank you.

**[00:46:23] Speaker 1:** 
If there are no more questions for me, we can wrap up.

**[00:46:28] Speaker 3:** 
Goodbye.

**[00:46:31] Speaker 1:** 
Have a good evening.
