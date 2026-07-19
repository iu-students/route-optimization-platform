# Meeting Transcript

Speaker 1 is the customer. More about roles in Report on Moodle.

**[00:00:00] Speaker 2**
I will tell you what was done this week. Most importantly, we beat the baseline with our current algorithm. It now completely outperforms the baseline across all 10 tests. We also fixed the documentation issues you mentioned. The database is now in `.gitignore`, and we corrected a few points in the docs; we sent them for your approval last night.

**[00:00:50] Speaker 2**
Our plans for this week were to release the algorithm and fix the documentation. Are there any other questions regarding the project handover document? Currently, the algorithm and all logic are deployed on the university's virtual machine and forwarded to a public IP via a tunnel. Also, as described in the document, you have administrator rights in the repository.

**[00:01:50] Speaker 1**
Yes, regarding the build, everything is fine, I was able to pull it independently. I haven't pulled the latest updates yet. Regarding the repository handover - I have everything, that question is closed. Regarding the documentation, I was interested in whether I could deploy everything independently. It worked out; the documentation is sufficient to pull and deploy it in my local or corporate environment and start using it. I have no questions, I confirm this.

**[00:02:57] Speaker 1**
Regarding the baseline changes, I haven't run your new version yet to check if your local results match what I will get. I plan to do that. But this doesn't critically block the confirmation that you have handed over the solution, it is in my possession, and I am accepting it, right?

**[00:03:34] Speaker 2**
Yes. And also, like last week, we need you to record the user tests confirming it works.

**[00:04:21] Speaker 1**
Okay, I will make the recording and send it to you.

**[00:04:27] Speaker 2**
Thank you. That's all for the main part regarding documentation and confirmation. I pass the floor to talk about the algorithm.

**[00:04:50] Speaker 3**
Hello. Last time we had two algorithm versions, but we abandoned the less refined one that was similar to a greedy approach. We kept the previous one, which was losing to the baseline on the fourth case. We found a number of issues and fixed them. One issue was that vehicles left the depot as late as possible to arrive exactly at the start of the first order's time window, causing them to spend a lot of time waiting between points.

**[00:05:51] Speaker 3**
Now we have a function that searches for the optimal departure time from the depot so that arrival isn't strictly at the start of the window. Next, we added an additional optimization - rearranging vehicle routes. This check takes about 1% of the execution time but sometimes yields results. For small input sizes, we added a check: we run the program not once, but two or three times with a shorter execution time. This helps when the initial routes are suboptimal. We also fixed minor bugs.

**[00:07:55] Speaker 1**
Did this allow you to improve the fourth case? As I recall, it was close to the solution there. Good. And it passes all tests now?

**[00:08:13] Speaker 3**
Yes.

**[00:08:30] Speaker 1**
Great. I'll look at the details over the weekend and run the tests. Thank you.

**[00:08:56] Speaker 4**
Hello. I worked on the solution in our CP Solver algorithm. I made a modification: I changed the route generation and added another library, which allowed us to add high-quality routes to the general list. According to the metrics, the first and fourth cases are already almost 2% better than the baseline.

**[00:09:50] Speaker 1**
What does the improvement in route quality consist of?

**[00:09:57] Speaker 4**
Previously, most paths were simply discarded, the pool was small, and the CP Solver couldn't choose properly. That's why we were losing on the first, third, and fourth cases. My colleague added more time for route generation and selection, and I changed the generation settings themselves. The Excel metrics show the comparison with the baseline. In some cases, we lose on vehicles, but we win by reducing the number of loaders.

**[00:11:20] Speaker 1**
Okay, I'll look at it after the meeting.

**[00:11:41] Speaker 2**
Overall, I think we've covered and discussed everything we wanted.

**[00:11:50] Speaker 1**
What's left on my side? To conduct the demo across all tests, check the algorithms, and review the comparisons. I'll compare the results locally.

**[00:12:43] Speaker 2**
It's important for us to get the test video by Sunday. The rest can wait until Monday.

**[00:13:09] Speaker 2**
We can mention the remaining risks. Since these are heuristic algorithms, the results might vary slightly on identical input data.

**[00:13:30] Speaker 1**
Need to check that, do multiple runs. But I won't test for stability. We didn't budget for that. I'll prepare the scenario, and the rest by Monday if possible. Any more questions?

**[00:14:23] Speaker 2**
No, that's all from our side.

**[00:14:27] Speaker 1**
Then we can wrap up. I want to leave some brief feedback. Regarding how the university organizes project management practice - it's a very good level. Many development stages are touched upon: analytics, documentation, working in sprints. For first- or second-year bachelor's students, this is an excellent foundation. Without discipline, development is hard and inefficiency arises. From a feedback perspective for the university - very positive.

**[00:16:27] Speaker 1**
As for you: teamwork is not easy. You managed to self-organize and work independently; between status updates, things were bubbling and boiling, you didn't leave everything until the last day. The interaction is structured, formal, as is now customary in large companies. Competent distribution of responsibilities; no one was doing a bit of everything, there was a strict division. You chose the vector yourselves - that's great.

**[00:20:10] Speaker 1**
The main victory is that you developed algorithms that managed to beat the baseline. This is the competitive part, and you brought it to the end, big plus. Thank you for your work and interest in the task. The task was non-standard; planning algorithms is problematic due to uncertainty, which steps outside university standards. I'm glad we interacted; it was productive and efficient, and we learned something from each other.

**[00:22:12] Speakers 2, 3, 4, 5, 6**
We came to say goodbye. Thank you very much for your work. Have a good day.

**[00:22:30] Speaker 1**
All the best to everyone. Goodbye.
