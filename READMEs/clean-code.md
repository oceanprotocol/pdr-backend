<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Clean Code ✨ Guidelines

Guidelines for core devs to have clean code.

Main policy on PRs:

> ✨ **To merge a PR, it must be clean.** ✨ (Rather than: "merge the PR, then clean up")

Clean code enables us to proceed with maximum velocity.

## Summary

Clean code means:

- No DRY violations
- Great labels
- Dynamic type-checking
- Tik-tok, refactor-add
- No "TODOs"
- Passes smell test
- Have tests always. TDD
- Tests are fast
- Tests are clean too

This ensures minimal tech debt, so we can proceed at maximum velocity. Senior engineers get to spend their time contributing to features, rather than cleaning up.

Everyone can "up their game" by being diligent about this until it becomes second nature; and by reading books on it.

The following sections elaborate:

- [What does clean code look like?](#what-does-clean-code-look-like)
- [Benefits of clean code](#benefits-of-clean-code)
- [Reading list](#reading-list)

## What does clean code look like?

**No DRY violations.** This alone avoids many complexity issues.

**Great labels.** This makes a huge difference to complexity and DX too.

- Rule of thumb: be as specific as possible, while keeping character count sane. Eg "ohlcv_data_factory" vs "parquet_data_factory".
- In functions of 2-5 lines you can get away with super-short labels like "c" as long as it's local, and the context makes it obvious.
- Generally: "how easily can a developer understand the code?" Think of yourself that's writing for readers, where the reader is developers (including yourself).

**Dynamic type-checking**, via @enforce_typing + type hints on variables.

- Given that bugs often show up as type violations, think of dynamic type-checking as a robot that automatically hunts down those bugs on your behalf. Doing dynamic type-checking will save you a ton of time.
- Small exception: in 2% of cases it's overkill, eg if your type is complex or if you're fighting with mock or mypy; then skip it there.

**Tik-tok, refactor-add.** That is: for many features, it's best to spend 90% of the effort to refactor first (and merge that PR). Then the actual change for the feature itself is near-trivial, eg 10% of the effort.

- It's "tik tok", where "tik" = refactor (unit tests typically don't change), and "tok" = make change.
- Inspiration: this is Intel's approach to CPU development, where "tik" = change manufacturing process, "tok" = change CPU design.

**No "TODOs".** If you have a "TODO" that makes sense for the PR, put it in the PR. Otherwise, create a separate issue.

**Does it pass the smell test?** If you feel like your code smells, you have work to do.

**Have tests always. Use TDD.**

- Coverage should be >90%.
- You should be using test-driven development (TDD), ie write the tests at the same time as the code itself in very rapid cycles of 30 s - 5 min. The outcome: module & test go together like a hand & glove.
- Anti-pattern outcome: tests are very awkward, having to jump through hoops to do tests.
- If you encounter this anti-pattern in your new code or see it in existing code, refactor to get to "hand & glove".

**Tests run fast.** Know that if a test module publishes a feed on barge, it adds another 40 seconds to overall test runtime. So, mock aggressively. I recently did this for trader/, changing runtime from 4 min to 2 s (!).

**Tests are clean too.** They're half the code after all! That is, for tests: no DRY violations; great labels; dynamic type-checking; no TODOs; passes "smell test"

## Benefits of clean code

_Aka "Why this policy?"_

- Helps **ensure minimal technical debt**
- Which in turn means we can **proceed at maximum velocity**. We can make changes, refactor, etc with impunity
- I was going to add the point "we're no longer under time pressure to ship features." However that should never be an excuse, because having tech debt slows us down from adding new features! Compromising quality _hurts_ speed, not helps it. Quality comes for free.
- From past experience, often "clean up later" meant "never" in practical terms. Eg sometimes it's put into a separate github issue, and that issue gets ignored.
- Senior engineers should not find themselves myself on a treadmill cleaning up after merged PRs. This is high opportunity cost of them not spending time on what they're best at (eg ML).
- What senior engineers _should_ do: use PR code reviews to show others how to clean up. And hopefully this is a learning opportunity for everyone over time too:)

## Reading list

To "up your game", here are great books on software engineering, in order to read them.

- Code Complete 2, by Steve McConnell. Classic book on code construction, filled to the brim with practical tips. [Link](https://www.goodreads.com/book/show/4845.Code_Complete)
- Clean Code: A Handbook of Agile Software Craftsmanship, by Robert C. Martin. [Link](https://www.goodreads.com/book/show/3735293-clean-code)
- A Philosophy of Software Design, by John Osterhout. Best book on managing complexity. Empasizes DRY. If you've been in the coding trenches for a while, this feels like a breath of fresh air and helps you to up your game further. [Link](https://www.goodreads.com/book/show/39996759-a-philosophy-of-software-design).
- Refactoring: Improving the Design of Existing Code, by Martiwn Fowler. This book is a big "unlock" on how to apply refactoring everywhere like a ninja. [Link](https://www.goodreads.com/book/show/44936.Refactoring).
- Head First Design Patterns, by Eric Freeman et al. Every good SW engineer should have design patterns in their toolbox. This is a good first book on design patterns. [Link](https://www.goodreads.com/book/show/58128.Head_First_Design_Patterns)
- Design Patterns: Elements of Reusable Object-Oriented Software, by GOF. This is "the bible" on design patterns. It's only so-so on approachability, but nonetheless the content makes it worth it. But start with "Head First Design Patterns". [Link](https://www.goodreads.com/book/show/85009.Design_Patterns)
- The Pragmatic Programmer: From Journeyman to Master, by Andy Hunt and Dave Thomas. Some people really love this, I found it so-so. But definitely worth a read to round out your SW engineering. [Link](https://www.goodreads.com/book/show/4099.The_Pragmatic_Programmer)

A final one. In general, _when you're coding, you're writing_. Therefore, books on crisp writing are also books about coding (!). The very top of this list is [Strunk & White Elements of Style](https://www.goodreads.com/book/show/33514.The_Elements_of_Style). It's sharper than a razor blade.

## Recap

Each PR should always be both "make it work" _and_ "make it good (clean)". ✨

It will pay off, quickly.
