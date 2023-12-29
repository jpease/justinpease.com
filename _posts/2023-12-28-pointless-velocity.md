---
title:  "Pointless Velocity"
layout: post
post-image: /assets/images/velocity-fox.jpeg
tags:
- agile
- the words we use
- engineering management
author:
- Justin Pease
published: true
---

Languages are dynamic. They grow and change shape. Existing words are repurposed
to describe new ideas. Sometimes it's helpful. Often it's harmless. But in some
cases, like today's example, it results in **layers of absolute and utter
nonsense that compound gloriously**.

## What is velocity?

The scientific definition of velocity is precise and useful:

> v = the change of distance in a given direction &divide; the change in time

Thus, a car that moves 60 miles east between 3:00 and 4:00 pm has a velocity of
60 mph east.

Alternatively, in casual conversation, many use velocity and speed
interchangeably when referring to any rate of change. This too makes sense as a
formula:

> v = measurement of change &divide; the change in time

## Velocity, according to SDLC methodologies

If you're following Scrum, or another software development methodology with
fixed length work cycles (i.e. [Sprints](https://justinpease.com/2023/01/02/the-words-we-use-sprint.html)),
the commonly accepted formula for velocity is:

> v = story points completed &divide; work cycle

Therefore, a team that completes 80 story points in a sprint could be said to
have a velocity of 80 story points/sprint, or commonly simplified to 80 points.

Does this formula make sense? To answer that, we first need to define our unit
of measurement. What exactly is a story point?

## A measurement of time by any other name

Ron Jeffries, likely the inventor of the story point, explains they were [first
used to estimate time](https://ronjeffries.com/articles/019-01ff/story-points/Index.html).
However, a recent [informal poll on LinkedIn](https://www.linkedin.com/posts/justinapease_i-have-an-idea-for-an-article-id-like-to-activity-7137539997569601536-h6Kb)
shows story points are also used to factor effort, complexity, risk, and
uncertainty into work estimates.

Does that change anything? No.

If you use story points to figure out how much work can fit in a fixed time
period&mdash;**story points are always an estimation of time**. Call it what you
want, but know that time is the subject matter.

## But we don't want to talk about time

In the article linked above, Ron Jeffries explains the switch from Days to
Points was an attempt to abstract estimations away from time. Why? The rationale
is intriguing. When using clear and direct language, guess what happened? The
stakeholders understood that time estimates were time estimates.

So what was the problem? With this understanding, stakeholders were focusing
on disparities between estimated time and actual time. It's not hard to imagine
that Mr. Jeffries and team found this to be an unhelpful distraction that did
not contribute to the performance of an engineering team. And thus, points.

As time has passed, this verbal sleight of hand has grown increasingly complex.
One team may adopt the Fibonacci sequence. Another, in an attempt to emphasize
the inexactness of the estimates, may use round numbers to lower the implied
precision of that sequence (e.g. 20 vs 21). Still others will avoid numbers
altogether and use T-shirt sizes, although they are often later translated back
to... you guessed it!... numbers. The purpose of all this? To pretend we're not
talking about time.

Lest we fall prey to our own tricks of misdirection, if points are being used to
fit work into a defined time period, all of these schemes reduce down to a
measurement of time. Yes, this point was made earlier, but it bears repeating.

## And then there was velocity

Much effort has gone into clouding the direct relationship between points and
time. As a result, **story points have no standard unit of measurement**. We
know this. It is the reason comparing points between teams is generally
recognized as bad practice. Apples, meet oranges.

So back to our question, does this formula for velocity make any sense?

> v = story points completed &divide; work cycle

With no standard unit of measurement for story points, velocity&mdash;in the
general case&mdash;must be understood as:

> v = \<*undefined term*\> &divide; work cycle

That, dear reader, is utter nonsense. **But wait, there's more!** After all,
you were promised this nonsense would come in gloriously compounding layers.

## The need for speed

Can you guess what happens when management hears about velocity?

> "You have a way to measure engineering speed? Great, we need to go faster!"

Meet your new KPI: Continuously Improving Velocity.

To be abundantly clear, this is not good. We established that velocity, as a
general measurement, is meaningless. Now, our success is being measured by...
doing more of it. &#128580;

However, I'm in a glass-half-full kind of mood. So, is this KPI salvageable?

Putting the general case aside, let's argue that within a single team a story
point will be used consistently enough to make it a useful quantifier. In that
setting, does increasing velocity make sense as a measurement of engineering
performance?

## In pursuit of increasing velocity

Our fictional team has chosen to use each story point to represent the work that
could reasonably be completed in one working day. Effort, complexity, and risk
are factored into their estimates.

* Team size: 8 people
* Working days in cycle: 10 (i.e 2 weeks)
* Team capacity: 80 points

In each of the following three scenarios, the team selects 80 points of work for
the cycle. They do not work any overtime.

### Scenario 1: Perfect Estimates

This seems improbable, but let's roll with it. The team completes the exact 80
points of work scheduled.

Now tell me, how does this team increase velocity? Given that story points are
an estimation of time, not output, there is only one way for a team with perfect
estimates to increase velocity:

1. Work more hours

### Scenario 2: Overestimated effort required

A more likely scenario, the team's estimates are imperfect. They overestimated
how long tasks would take. As a result they were able to complete 90 points.

It's critical to note that capacity did not increase to 90. Points ultimately
represent time. The team did not figure out a way to make more time. So what
happened? They guessed wrong.

What's morbidly interesting is that if their prior cycle's estimate was more
accurate, then **this estimation error will appear as "increased velocity".**
Good job, team! &#128077;

But that's just one cycle. How can the overestimating team continue to increase
velocity? They have an additional option over Scenario 1:

1. Work more hours, or
2. Overestimate story points by an ever increasing amount

### Scenario 3: Underestimated effort required

Perhaps the most realistic scenario, the team underestimates the time required.
The work cycle ends and the team completed 70 points.

Unfortunately, if prior cycles' estimation accuracy was higher, this wrong guess
will show up on KPI reports as a velocity decrease. &#128201;

With rumors of layoffs swirling, how does the underestimating team increase
their velocity? They have the most options. Too bad they're all terrible:

1. Work more hours, or
2. Overestimate story points by an ever increasing amount, or
3. Seek estimating perfection, but as discussed in Scenario 1, achieving it is a
dead end

## Velocity is pointless

Yes, of course, the pun is intended.

One last detail that is exceptionally important to internalize is that in all
three scenarios **exactly the same amount of work and value was delivered.** The
only thing that changed was the accuracy of the estimates.

## The root problem

This is an example where the choice of wording, specifically velocity, has done
a great disservice. I'm not blaming anyone. I mean to imply no malintent.
Regardless, the outcome is the same.

So let's drop the jargon and call things as they are. The formula for what we've
been talking about is:

> estimated time &divide; actual time

Looking at that formula, what does it describe? Accuracy of estimation. Does the
label matter? Yes! If we called it what it is, estimation accuracy, imagine
what would immediately become plain:

* Has no direct correlation to value creation, efficiency, or productivity
* 10% under is just as wrong as 10% over, although neither may matter
* Improvement has a fixed upper limit of 100%
* Unless estimation accuracy is a top business priority, focus may be better
spent elsewhere

## But... we use velocity to measure output

That's a shame. Because if you're using story points to do so, it's not what
your numbers mean.

## One last gloriously ironic layer of nonsense

I find this last piece painfully amusing. You'll recall from earlier in the
article, story points were introduced to do what? To avoid focus on deviations
between work estimates and actual time spent.

And what have we done?

**Under the name of Velocity, we've memorialized and spotlighted this very
thing as a core metric.** But we couldn't just stop there, could we? Oh no. 
We've also managed to make it far more confusing along the way.

&#128079; Bravo! Bravo. &#128079;