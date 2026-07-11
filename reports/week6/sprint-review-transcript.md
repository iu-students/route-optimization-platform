# Meeting Transcript

Speaker 2 is the customer. More about roles in Report on Moodle.

**[00:00:02] Speaker 1**
Let's talk a little about how things are going right now. We continue to refine our algorithms. Currently, one of the algorithms passes 9 out of 10 tests, and in one test it still outperforms the baseline. But I will pass the floor to discuss this as well. This week we also added metrics and calculation history so that it can be tracked, as you requested.

**[00:00:41] Speaker 1**
We will also send you the user tests that need to be recorded. And as part of this week's report, we need to ask you about transitioning the project directly into your hands. Let's probably start with this: do you consider the product ready for transition at the moment, and what needs to be added to finally hand it over to you?

**[00:01:26] Speaker 2**
A few clarifications. On my side, I will have to deploy your solution and run a test scenario. Is that what the handover consists of?

**[00:01:47] Speaker 1**
In addition to that, we wanted to grant you admin rights to the repository. Overall, this is one part of the handover: you test it, run it, use it.

**[00:02:19] Speaker 2**
Regarding functionality, I will also look at the history. And we can consider it ready. Everything we agreed upon is there.

**[00:02:29] Speaker 2**
All that's left is to verify that the launch history can be viewed. Then this week, please send me the repository that I can deploy and run on my side. I will try to deploy it.

**[00:02:50] Speaker 2**
If it goes without problems, then overall we close this issue with the handover.

**[00:03:21] Speaker 2**
If there are any questions, I will send them to you in the chat. You can either consult me there, or give hints if needed, and I will try again.

**[00:03:37] Speaker 2**
How urgent is it, in terms of handover deadlines? How urgent and in what form should I confirm? Or for you, is the handover just granting rights and that's it?

**[00:03:48] Speaker 1**
For us, it is granting rights and having you test it. This is expected within the next two weeks. Right now we are finalizing the project to a digestible state, and overall, at the end of the seventh week, the final transition into your operation takes place.

**[00:04:20] Speaker 2**
Then you can send the link now so I can deploy it on my side. If the algorithm doesn't cover all scenarios yet, I will accept the algorithm separately. I can accept the interface and the current scenario now.

**[00:04:45] Speaker 1**
Also after the meeting, along with the user tests, as in previous weeks, we will send you files regarding the handover for your written approval and confirmation.

**[00:05:12] Speaker 1**
As I said, regarding the algorithm, we don't cover all scenarios at the moment; 9 out of 10 are covered, so active work is underway in this direction. The next items we need to reflect in the report are: are you already using the project? If so, how? Are you already using the project in its current form, the link to which we gave you, where the testing and so on takes place?

**[00:06:14] Speaker 2**
I ran it there, made recordings. What does "use" mean? In an industrial capacity?

**[00:06:20] Speaker 1**
Yes, as far as we understand, the question implies industrial use.

**[00:06:34] Speaker 2**
The question is ambiguous because the set of requirements was reduced in terms of functionality. To use it in production, a large scale of work is still needed. Actually, at the start of the project, it wasn't assumed that there would be industrial use; here the maximum is using the idea of the solution, algorithms at this level, so to speak, yes.

**[00:07:07] Speaker 2**
But for an industrial version, I don't know how to handle it here. If this is some critical point, let's think about how it can be considered.

**[00:07:20] Speaker 1**
Overall, as far as I understand, this is exhaustive, if it was initially considered within certain limits. We can, of course, discuss whether there are any minor requirements for putting it into operation. But if they greatly exceed the limits of what is currently available, then I think we can stick to the original version.

**[00:08:03] Speaker 2**
We will not expand the rules, because it might break the whole algorithm, and we won't have time to rebuild it. Therefore, we focused on this from the start: it is mostly a presentation of a working idea that is better than some existing ones. There was no goal to implement and roll it out for use.

**[00:08:33] Speaker 1**
Okay, another point of the question is: how to increase the likelihood that the product remains useful after our interaction ends. Overall, I think this has already been answered.

**[00:08:55] Speaker 2**
Yes.

**[00:08:57] Speaker 1**
As I said, after the meeting we will send several files for approval regarding the handover.

**[00:09:10] Speaker 1**
There will be a file on how we hand it over to you, and a file responsible for collaboration so that AI agents and other developers can interact with our repository. The question regarding additional user stories: at the moment, it seems everything we discussed is closed or is being closed in one way or another. Are there any additions?

**[00:10:12] Speaker 2**
No, there will be no additions. Everything is being closed now. Everything except the history, which I haven't looked at yet. Except for the history, everything is okay.

**[00:10:28] Speaker 1**
Regarding the questions about the handover report, that's all. Next, I will pass the floor so they can talk a bit more about the last user story and say a few words about the algorithms: how successfully the tests are passing.

**[00:11:04] Speaker 3**
Hello. Yesterday I sent a file regarding user stories. We added the launch history display story, broken down into technical tasks, which also mentions adding a database. In this sprint, we focused more on refining the algorithm rather than on additional features in user stories, as well as preparing the repository for handover. Overall, are there any questions on the user stories?

**[00:11:40] Speaker 2**
No, no questions, I looked, everything is fine.

**[00:12:16] Speaker 3**
Thank you. Then I pass the floor to our developer.

**[00:13:18] Speaker 4**
Hello. Last week we discussed the part of the algorithm using CP Solver, and you suggested the idea of using multiple vehicles for multiple routes at once.

**[00:13:32] Speaker 4**
We integrated this idea into the existing solution, and on the instances attached to your repository, it was shown that they only took effect on the tenth case. On the previous ones, they weren't particularly used. We also mentioned that the previous version of the algorithm was losing on two or three cases.

**[00:14:01] Speaker 4**
We realized what the mistake was: we were generating a small number of routes. Now I have slightly adjusted the time limits specifically for the route generation section and separately for the CP Solver.

**[00:14:20] Speaker 4**
Now all cases from the first to the tenth instance take 10 to 14 minutes. After the meeting, I will send an Excel file with updated metrics. It will show that for all cases except the fourth, we are already beating the baseline.

**[00:14:44] Speaker 4**
On the fourth case, we lose to the baseline by 2%, and this is related only to the vehicles.

**[00:14:59] Speaker 2**
The fourth case turned out to be quite peculiar. Okay.

**[00:15:05] Speaker 2**
It seems we can fight this here, even if we pull just half a percent. Okay. Will the build you provide for acceptance and handover contain the latest version of the algorithm?

**[00:15:21] Speaker 4**
Our project will contain the latest version of the algorithm. There are two different pipelines: my algorithm and Marsel's algorithm. Everything will be fresh.

**[00:15:39] Speaker 2**
And how are these two algorithms structured inside? Did you merge them into one?

**[00:15:47] Speaker 4**
No, we didn't merge them, we just compared them on common cases. We had two proposals for creating algorithms, we tried various things.

**[00:16:00] Speaker 2**
Will you select what you hand over? Can I test what you plan to embed into the service?

**[00:16:11] Speaker 4**
We will help show how to use our separate pipelines. Then, based on the latest metrics of the latest algorithm version, we will choose the final version for operation.

**[00:16:31] Speaker 2**
Good. It will be enough for me to have a repository where a separate pipeline is assembled. Or if they are switched via settings, describe how to switch the algorithm and which parameter to adjust.

**[00:16:52] Speaker 4**
After the meeting, I will send an Excel file with metrics across the ten cases so it's clear in which areas we beat the baseline and where we lose a bit.

**[00:17:06] Speaker 2**
Okay. Regarding when I can look on my side: it won't work out this weekend, so I will only be able to do all the checks next week.

**[00:17:29] Speaker 2**
If you send the links in the chat in advance, I can try to deploy it independently of you. If there are problems or questions, I will address them. If a deeper consultation is needed, we'll call.

**[00:17:50] Speaker 2**
For now, just send instructions on where everything is. I think I'll figure out the launch. Alright, the algorithm part is clear for now.

**[00:18:30] Speaker 2**
Now my colleague will talk about how he created his algorithm.

**[00:18:40] Speaker 5**
Hello. Last time I talked about the idea, and this time I implemented it and am testing it now. So far, it is worse than the baseline on a few tests. I am trying to adjust the sample size that we exclude, and it improves in some places.

**[00:19:19] Speaker 5**
We need to find a dimension that can be stably cut out and inserted back. This algorithm also lacks a system for returning vehicles to the depot, and if added, productivity will increase. This is what I will be doing now.

**[00:19:51] Speaker 2**
If we manage to beat the fourth case, the rest are not so important. The focus is on the fourth right now. Can we then switch the algorithm so that yours runs on the fourth?

**[00:20:17] Speaker 2**
How significant is it that we have two algorithms and they pass tests differently? That's probably not very good.

**[00:20:30] Speaker 2**
It's not very good if you specifically prescribe input data, meaning you tie it to specific data. If we talk about using multiple algorithms that kick in at different stages, it's a perfectly normal practice. There are small tasks that can be solved completely to get the optimal solution. But there are similar tasks where the scale grows. In this case, algorithms no longer allow solving the problem head-on; we have to apply decomposition.

**[00:21:14] Speaker 2**
Decomposition inherently limits the optimality of the solution. We get a suboptimal solution taking into account the assumption on which the decomposition is based. The question is how to perform decomposition, because it can be done in different ways.

**[00:21:42] Speaker 2**
In one case, we lose a lot from the optimal solution, in another, a little. A volume-based switch is a frequently used practice. By the size of the scenario (in this case, by the number of orders), we understand whether the problem can be solved completely. With a limit of fewer than 100 orders, we can solve the problem entirely; the algorithms allow it.

**[00:22:22] Speaker 2**
We make a switch: if there are fewer than 100 orders at the input, one algorithm runs. If more than 100, we turn on another algorithm, and a different solution branch is used. Using two algorithms is quite justified; it's not a hack, an exploit, or cheating.

**[00:22:50] Speaker 2**
But if you tie it to a specific scenario, it's not very noble. If the switch is tied to general parameters (like the number of orders), it's perfectly acceptable. It turns out that the algorithm that handles the fourth scenario should also handle all previous ones, as they increase in order volume.

**[00:23:26] Speaker 2**
That is, a threshold is set: for a certain number of orders, there will be a certain algorithm. We will consider this ethical.

**[00:23:40] Speaker 5**
We believe that in the fourth case, the problem is not just the number of orders, because we can do everything before and after. But the idea of switching algorithms is clear to me. We will use it somehow.

**[00:24:02] Speaker 2**
If it turns out that another algorithm can solve this case stably, we can make a switch.

**[00:24:21] Speaker 2**
Overall, there is nothing illegal here, but one should know the limit. No questions on algorithms. I hope there is still enough time to beat the case; you have come close. Perhaps small adjustments to the current algorithms will lead to defeating it.

**[00:24:54] Speaker 5**
Yes, we hope so too. That's all from me. Thank you.

**[00:29:22] Speaker 2**
Returning to the conclusion of the meeting. Thank you all, have a good day.

**[00:29:25] Speaker 1**
Thank you, goodbye.
