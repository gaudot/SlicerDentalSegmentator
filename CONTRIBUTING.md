Contributing to the plugin
==========================
These contributing rules largely
follow [Slicer's contributing documentation](https://github.com/Slicer/Slicer/blob/master/CONTRIBUTING.md).

To contribute, you can :

* Ask a question on the [Slicer forum](https://discourse.slicer.org)
* Use `Issues` to submit a feature request or bug, or
  add to the discussion on an existing issue
* Submit a `Pull Request` to improve this plugin or its
  documentation

We encourage a range of Pull Requests, from patches that include passing tests and documentation, all the way down to
half-baked ideas that launch discussions.

The PR Process, Circle CI, and Related Gotchas
----------------------------------------------

#### How to submit a PR ?

If you are new to Slicer plugin development and you don't have push access to the plugin repository, here are the steps:

1. [Fork and clone](https://help.github.com/articles/fork-a-repo/) the repository.
2. Create a branch.
3. [Push](https://help.github.com/articles/pushing-to-a-remote/) the branch to your GitHub fork.
4. Create a `Pull Request`.

This corresponds to the `Fork & Pull Model` mentioned in
the [GitHub flow](https://guides.github.com/introduction/flow/index.html)
guides.

When submitting a PR, the developers following the project will be notified. That said, to engage specific developers,
you can add `Cc: @<username>` comment to notify them of your awesome contributions. Based on the comments posted by the
reviewers, you may have to revisit your patches.

#### How to write commit messages ?

This plugin follows Slicer's commit message standard :

* `FIX:` Fix for runtime crash or incorrect result
* `COMP:` Compiler error or warning fix
* `DOC:` Documentation change
* `ENH:` New functionality
* `PERF:` Performance improvement
* `STYLE:` No logic impact (indentation, comments)
* `WIP:` Work In Progress not ready for merge

The body of the message should clearly describe the motivation of the commit
(**what**, **why**, and **how**). In order to ease the task of reviewing commits, the message body should follow the
following guidelines:

1. Leave a blank line between the subject and the body. This helps `git log` and `git rebase` work nicely, and allows to
   smooth generation of release notes.
2. Try to keep the subject line below 72 characters, ideally 50.
3. Capitalize the subject line.
4. Do not end the subject line with a period.
5. Use the imperative mood in the subject line (e.g. `FIX: Fix spacing not being considered.`).
6. Wrap the body at 80 characters.
7. Use semantic line feeds to separate different ideas, which improves the readability.
8. Be concise, but honor the change: if significant alternative solutions were available, explain why they were
   discarded.
9. If the commit refers to a topic discussed on the [Slicer forum](https://discourse.slicer.org), or fixes a regression
   test, provide the link. If it fixes a compiler error, provide a minimal verbatim message of the compiler error. If
   the commit closes an issue, use
   the [GitHub issue closing keywords](https://help.github.com/en/articles/closing-issues-using-keywords).

Keep in mind that the significant time is invested in reviewing commits and
*pull requests*, so following these guidelines will greatly help the people doing reviews.

[How to Write a Commit Message](https://chris.beams.io/posts/git-commit/)
post.

Examples:

- Bad: `FIX: Check pointer validity before dereferencing` -> implementation detail, self-explanatory (by looking at the
  code)
- Good: `FIX: Fix crash in Module X when clicking Apply button`
- Bad: `ENH: More work in qSlicerXModuleWidget` -> more work is too vague, qSlicerXModuleWidget is too low level
- Good: `ENH: Add float image outputs in module X`
- Bad: `COMP: Typo in cmake variable` -> implementation detail, self-explanatory
- Good: `COMP: Fix compilation error with Numpy on Visual Studio`

#### How to integrate a PR ?

Getting your contributions integrated is relatively straightforward, here is the checklist:

* All tests pass
* At least one reviewer has approved the changes.
* The maintainer of the project will then merge the changes to the plugin.
