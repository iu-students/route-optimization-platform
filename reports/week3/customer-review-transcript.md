# Meeting Transcript

Speaker 3 is the customer. More about roles in Report on Moodle.

**[00:00:03] Speaker 1:** I’ll probably start with what has been done since our last meeting. Right now, the first version of the MVP is ready. It’s comparable to the baseline, and in some cases, it even slightly outperforms it, within the margin of error. I’ll pass the floor to another team member to discuss this in more detail during today's meeting.

**[00:00:38] Speaker 1:** We also formed the product backlog: user stories were edited, and technical tasks for the first MVP were created based on them. We’d like to discuss them in more detail today as well. We sent the edited file to the general chat.

**[00:01:00] Speaker 3:** Yes, I saw it.

**[00:01:06] Speaker 1:** Currently, the MVP isn't deployed on the server yet, but within a couple of hours after our call, I’ll send a link where you can test it all out.

**[00:01:23] Speaker 3:** Will I have access to your server or not? Is your server deployed in a local environment?

**[00:01:39] Speaker 1:** No, everything is forwarded to a public IP address.

**[00:01:49] Speaker 3:** Good.

**[00:01:50] Speaker 1:** That’s briefly on the results of the week, and now I’ll pass the floor for more details.

**[00:02:01] Speaker 4:** Hello. Yesterday I sent a file with the user stories corrected according to your feedback. There are also prioritized user stories that are described in more detail - they already include technical tasks. This is all done within the backlog, meaning this is what we need to implement.

**[00:02:32] Speaker 3:** Now, while we are still on the topic of user stories. I looked at the recent ones. I would also recommend adding something regarding optional orders. There is a story that orders must be fulfilled within a time window. But we have some orders that we might not fulfill within the window, or not fulfill at all. We need to add another story for the manager so they can see and understand which orders have been completed.

**[00:03:12] Speaker 3:** Additionally, maybe we should add something about mandatory orders - as a hard constraint, they should also be highlighted. This is what needs to be added regarding the essential stories.

**[00:03:27] Speaker 3:** As for additional features - the manager needs to see certain metrics and calculation indicators to understand their efficiency. There is a story related to routes being optimal, but at the same time, there should be an ability to view the overall objective function and calculation statistics. This is an additional thing worth adding. For the rest of the stories, I think it’s enough.

**[00:04:19] Speaker 4:** Do the rest of the user stories match the feedback, is everything okay?

**[00:04:24] Speaker 3:** Yep.

**[00:04:26] Speaker 4:** Great. We also wrote down the technical tasks for this week. They are labeled TT-1, TT-2, and so on. They are distributed among the user stories they are linked to, they have descriptions, and we have criteria to understand if a task is completed or not. Are there any inaccuracies there, anything to improve or fix?

**[00:05:00] Speaker 3:** I just didn't see any tasks regarding the calculation mechanism itself; there are no tasks for it right now. Is that because it's not related to the stories?

**[00:05:21] Speaker 4:** Yes, it’s slightly unrelated to the format of our stories. Most of our current stories are related to verification functions. Since our main algorithm works - it builds the route itself without the help of the additional functions required from us, but we need to verify them. I think our developers will tell you more about this.

**[00:06:16] Speaker 3:** Okay, I understand, so it’s out of scope. I also wanted to clarify the UI. What did you decide to settle on for the user interface? We initially discussed that a terminal line would be enough. Do you have any corrections or suggestions? Do you want to leave it as originally planned?

**[00:06:41] Speaker 1:** For now, we’ve settled on it working in an API and endpoint format: we send requests, we get data. However, as an interface, to make it more convenient and visual to interact with, we chose Swagger UI. I sent a link earlier showing what it looks like. It also serves as documentation on how requests should be structured. There are also a couple of examples and windows where you can manually send these requests.

**[00:07:29] Speaker 3:** A small comment regarding the repository. Didn't you create a separate account for the project?

**[00:07:43] Speaker 1:** We created a separate organization that includes all team members. The repository belongs to this organization's name.

**[00:08:03] Speaker 3:** I’m just looking now, and this seems to be the old repository, which, if I’m not mistaken, is yours, Maxim, the repository where the account is deployed.

**[00:08:18] Speaker 1:** The link might be old, but it still redirects to the right one via GitHub. After the call, I’ll send all the up-to-date links again.

**[00:08:40] Speaker 3:** I checked because the university might have a requirement that it shouldn't be tied to a personal repository. I don't know if you have additional criteria for how the project result will be evaluated. If they can be shared, please send them. But I suspect that at the very least, the account must be created separately for the project. These are just comments, potentially worth paying attention to. Alright, I understand about this. Regarding the algorithm... Who will talk about the results?

**[00:09:55] Speaker 2:** Hello. Regarding the MVP: the idea of the algorithm is that we use PyVRP to distribute vehicles, and then we don't change these built routes, but add loaders on top. Using a greedy algorithm, we first find the most urgent point among all, and assign a loader there. Then we look at the area they can theoretically cover. Among the points not included in this area, we again select the most urgent one, assign a loader there, and thus get an initial arrangement where a loader can reach every point, assuming they only go to that one.

**[00:10:55] Speaker 3:** Can I ask a question right now? How exactly do you go through this? Do you close points and assign loaders to them first, or do you find the first point, add a loader, and then distribute this loader to all nearby orders? Or do you move to the next critical point?

**[00:11:17] Speaker 2:** First, when we don't have loaders yet, we select the point closest in time to when a vehicle arrives.

**[00:11:25] Speaker 3:** So you selected and fixed a loader.

**[00:11:28] Speaker 2:** We place a loader, and then we have a function that checks available points. A point is considered available if a loader can go there, do the work, and have time to return.

**[00:11:38] Speaker 3:** Got it, I understand. So you start from the loader? You assign the first loader, and then build a route for this loader until the end of their shift?

**[00:11:55] Speaker 2:** First, we build an area of points they can reach. For example, if they only go to this point and immediately return - that's the area they can theoretically cover. Because there are points they can't even reach one of. Then, when we've built such an area for one loader, for the remaining points not in the area, we add other loaders using the same principle. Eventually, we get that for each point in the initial distribution, we can theoretically reach it with any loader. Then we take an individual loader and start building a route for them in a greedy manner: to the most urgent point they need to reach.

**[00:13:08] Speaker 2:** The idea is to never delay the vehicle. A loader can wait at a point, but the vehicle won't wait; it unloads immediately upon arrival. And as soon as we've built such a route for one loader, we fully complete it. The points they processed, if one loader was required there, we mark as completed. And then, among the remaining points, we again select the most urgent one, place a loader there, and repeat.

**[00:13:55] Speaker 3:** So, the greedy approach is generally centered around the loader. But your goal is still to start from the loaders and look for the next order a loader can fulfill. And this way, greedily, you first process one loader, then select the next one, build a route for them. Do you try to pack the shift to the maximum for each loader individually?

**[00:14:39] Speaker 2:** We try to give not the closest order, but the most urgent one in their area, where the vehicle should arrive the earliest.

**[00:14:51] Speaker 3:** That's right. I’ve already adjusted the fact that our orders are already tied to vehicles, we already need to arrive at the vehicles. The closest is the one where a loader needs to be sent because the vehicle will be there. Are wait times accounted for here somehow?

**[00:15:21] Speaker 2:** The fact that a loader will arrive at a point and wait for the vehicle is accounted for.

**[00:15:27] Speaker 3:** So, you look not only at whether they made it to this order and that it's close in time, but also how long they will have to wait. Potentially, an order might be close, but we arrive and wait 20 minutes. Therefore, we potentially send them to another order where they will arrive and not wait.

**[00:15:54] Speaker 2:** Yeah, exactly.

**[00:15:55] Speaker 3:** Okay, and how is your comparison with the baseline?

**[00:16:03] Speaker 2:** For the baseline, there are tests with about a 1% margin of difference. There are tests, for example, the sixth one, where our algorithm performs better. Noticeably better.

**[00:16:22] Speaker 3:** Out of ten cases, in how many are you better and in how many worse? Let's see what threshold has been passed.

**[00:16:44] Speaker 2:** I don't remember. I need to run these tests again, but we can let you know later.

**[00:17:01] Speaker 3:** Because for the MVP we agreed that you were just making an algorithm, but the target project is to do better than the baseline. I wanted to see right now how much better you are. You only mentioned the sixth one so far, meaning, essentially, at least one out of ten is already better. Okay. So, regarding ideas and algorithms, what do you have planned now to improve the algorithm?

**[00:17:49] Speaker 5:** Hello. At the last session, you gave us a little spoiler about how we could try to improve the algorithm - using CP Solver together with the assignment problem. My role in the project right now is to try to create this function.

**[00:18:12] Speaker 5:** Right now, what we have is PyVRP in our function generating hundreds of thousands of different routes. And the CP Solver you mentioned looks for the best combination for them.

**[00:18:26] Speaker 5:** And our idea is to create the best combination not only for vehicles but also for loaders. In one of the branches on GitHub, you can look at the current solution, we can duplicate it and show you after the session. I haven't checked it against the baseline yet, but in principle, the solution seems valid; it at least produces a result. It creates routes for loaders separately and for vehicles separately.

**[00:18:56] Speaker 3:** Okay, I guess I lost the repository because the one I have only has one branch.

**[00:19:09] Speaker 5:** We'll duplicate it after the session and explicitly indicate which branch is responsible for what.

**[00:19:17] Speaker 3:** Yes, I think I found it here. Okay, I'll look at the code. You promised to send it so I could try running it. I assume this is the stable version available right now. And this branch is still for experiments, right?

**[00:19:51] Speaker 5:** Uh-huh.

**[00:19:52] Speaker 3:** Can you describe in more detail where exactly you plan to apply it?

**[00:20:03] Speaker 5:** In principle, this part can be integrated with the existing solution when we assign work to loaders. As for vehicles, it is very similar to what our team member has already done, so there won't be any particular difficulty with integration.

**[00:20:25] Speaker 3:** By the way, OR-Tools, they also have a VRP Solver.

**[00:20:33] Speaker 5:** Yes, we provided a comparison in the document about why we decided to stick with PyVRP for now.

**[00:20:44] Speaker 3:** There probably won't be any serious improvements or deteriorations here. They work about the same. And it would be great if you could send statistics on how much better or worse it is, and maybe calculate percentages. Have you looked into using some derivative metrics to extract and use in calculations?

**[00:21:32] Speaker 5:** We haven't calculated metrics yet. We are currently more focused on building the method to solve this problem. Once the MVP is built and solves the problem normally, we will analyze which metrics will best highlight our solution against the baseline and clearly show the difference.

**[00:21:50] Speaker 3:** There is a disconnect (seam) between the vehicle model and the loader model. Because they are calculated separately, there is a gap related to optional orders, which we initially cannot correctly determine based solely on vehicle assignments. We cannot correctly calculate how much the fulfillment of this order will ultimately cost us because we don't see the loaders.

**[00:22:32] Speaker 3:** And the question arises: do we even need to service this order or not? This is exactly the field to think about. To minimize the impact of this gap on the overall value, we can work with metrics here.

**[00:23:00] Speaker 3:** I recommend looking exactly at this part that connects both models. There are different options: you could embed some estimate.

**[00:23:23] Speaker 3:** You could embed an estimate that roughly we have a certain amount of costs per order. Look at free capacity, how much free capacity we have for vehicles and loaders. And based on this, see whether we can afford to take on an order or not.

**[00:24:17] Speaker 3:** Different characteristics can be applied here, the question is how much it will improve the solution. You could work backwards: we fulfill all orders, and then just drop some orders when we see that an order requires one vehicle and one loader, and the cost is higher than the profit from fulfilling it. Then we can just calculate this economy in post-processing and cut such cases. But the algorithm needs to be organized so that it maximally separates optional orders into independent blocks. Because our routes include multiple orders at once for one vehicle and for loaders too. So this is another tangled ball of yarn to untangle. I understand about the algorithm, thanks for the deep dive.

**[00:24:59] Speaker 5:** Are there any other questions on the algorithm?

**[00:25:00] Speaker 3:** I think that's all for the algorithm, thank you. I'll also look at the organization of the repository. I assume you have some requirements for how it should be structured and what should be there. I'll just look at what's there. Maybe I'll have comments on the general organization of the repository.

**[00:25:48] Speaker 3:** One more question. You said that in two or three weeks we need to lock in regarding the MVP. Whether we've reached the MVP or not. So, three weeks means next week, right?

**[00:26:05] Speaker 1:** Starting this week, ending next week. But overall, we've progressed quite well this week regarding the MVP. As I said, in a couple of hours I’ll send a link to test the solution we currently have.

**[00:26:27] Speaker 3:** Good. And besides this server, I will still try to run it from the source code, via terminal.

**[00:26:43] Speaker 1:** In general, as one of the requirements for the repository, it's a description of how it should be launched, and it's generally there.

**[00:26:52] Speaker 3:** So I'll figure it out there. Good. And regarding the results, do I need to send something somewhere, to someone, or do I just tell you everything is okay?

**[00:27:09] Speaker 1:** So far, we haven't been asked to do that. Well, if anything, we will reach out to you. We sent all the confirmations that were required from you.

**[00:27:17] Speaker 3:** Yes, and some changes. Last time I said not to post the scripts of our meetings. In general, let's move away from that, you can post them to GIT as well. That's a correction.

**[00:27:36] Speaker 3:** Alright, that's all for me then. If there are no questions, I suggest we finish for today.

**[00:27:46] Speaker 1:** Thank you then.

**[00:27:47] Speaker 3:** Okay, thank you. Goodbye, have a good day.

**[00:27:47] Speaker 1:** Goodbye. Have a good day.
