# Contributing

We are glad to know that you would like to contribute.
This should be as easy as possible for you but there are a few things to consider when contributing.
The following guidelines for contribution should be followed if you want to submit a pull request. If you have any troubles, just come and ask us for help on our IRC channel.

## Basic Overview
*   Read [Github documentation](http://help.github.com/) and [Pull Request documentation](http://help.github.com/send-pull-requests/)
*   Fork the repository
*   Edit the files, add new files
*   Check the files with [`pep8`](https://pypi.python.org/pypi/pep8), fix any reported errors
*   Check that the files work as expected
*   Create a new branch with a descriptive name for your feature (e.g. feature/random_plugin)
*   Commit changes, push to your fork on GitHub
*   Create a new pull request, provide a short summary of changes in the title line, with more information in the description field.
*   After submitting the pull request, join our [Telegram channel](https://telegram.me/botdevgroup) and give us a link so we know you submitted it.
*   After discussion, your pull request will be accepted or rejected.

## Reporting bugs

A bug is a _demonstrable problem_ that is caused by the code in the repository.
Good bug reports are extremely helpful - thank you!

Guidelines for bug reports:

1.  **Use the GitHub issue search** &mdash; check if the issue has already been reported.
2.  **Check if the issue has been fixed** &mdash; try to reproduce it using the latest `master` or development branch in the repository.
3.  **Isolate the problem** &mdash; create a [reduced test case](http://css-tricks.com/reduced-test-cases/) and a live example.

A good bug report shouldn't leave others needing to chase you up for more
information. Please try to be as detailed as possible in your report. What is
your environment? What steps will reproduce the issue? What browser(s) and OS
experience the problem? What would you expect to be the outcome? All these
details will help people to fix any potential bugs.

Example:

> Short and descriptive example bug report title
>
> A summary of the issue and the environment in which it occurs. If
> suitable, include the steps required to reproduce the bug.
>
> 1.  This is the first step
> 2.  This is the second step
> 3.  Further steps, etc.
>
> `<url>` - a link to the reduced test case
>
> Any other information you want to share that is relevant to the issue being
> reported. This might include the lines of code that you have identified as
> causing the bug, and potential solutions (and your opinions on their
> merits).

## How to prepare

*   You need a [GitHub account](https://github.com/signup/free)
*   Submit an [issue ticket](https://github.com/BotDevGroup/python-telegram-bot/issues) for your issue if there is no one yet.
*   Try to describe the issue and include steps to reproduce if it's a bug.
*   If you are able and want to fix this, fork the repository on GitHub

## Make Changes

*   In your forked repository, create a topic branch for your upcoming patch. (optional)
*   Make sure you stick to the coding style that is used already.
*   Make use of the [`.editorconfig`](http://editorconfig.org/) file. (TODO)
*   Make commits that make sense and describe them properly.
*   Check for unnecessary whitespace with `git diff --check` before committing.
*   Check your changes with [`pep8`](https://pypi.python.org/pypi/pep8). You can usually ignore messages about line length, but we like to keep lines shorter then 120 characters if at all possible.

## Submit Changes

*   Push your changes to a topic branch in your fork of the repository.
*   Open a pull request to the original repository and choose the `develop` branch.
*   If not done in commit messages (which you really should do) please reference and update your issue with the code changes. But _please do not close the issue yourself_.

# Additional Resources

*   [General GitHub documentation](http://help.github.com/)
*   [GitHub pull request documentation](http://help.github.com/send-pull-requests/)
*   [Read the Issue Guidelines by @necolas](https://github.com/necolas/issue-guidelines/blob/master/CONTRIBUTING.md) for more details
*   [This CONTRIBUTING.md from here](https://github.com/anselmh/CONTRIBUTING.md)
