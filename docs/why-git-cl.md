# Changelists in Git: A Personal History

Back in university, our research group used a homegrown [version control system](https://en.wikipedia.org/wiki/Version_control) built around [RCS](https://en.wikipedia.org/wiki/Revision_Control_System). When it started showing its age, I began reading [Version Control with Subversion](https://svnbook.red-bean.com/) during my train commutes, and it was eye-opening. I began migrating our model code into [Subversion](https://subversion.apache.org), and for the first time, I felt I truly understood what a version control system could offer.

The cool kids were already experimenting with [Git](https://git-scm.com), but I was drawn to the stability of Subversion – and honestly, [Mercurial](https://www.mercurial-scm.org) looked more user-friendly anyway.

After university, I joined a government organisation – code-heavy, using an in-house version control wrapper. This time, it was a wrapper around Subversion called [FCM](https://metomi.github.io/fcm/doc/user_guide/code_management.html). Perfect: I could apply my Subversion experience directly. A few years later, the organisation began migrating from SVN to Git.

That's when I hit my problem.

Subversion’s [changelists](https://svnbook.red-bean.com/en/1.6/svn.ref.svn.c.changelist.html) had been one of its most elegant features – a way to group files by intent before committing. In Git, that model was gone. The staging area was powerful, yes, but flat. I was used to having multiple named staging areas – changelists like 'ok' and 'do_not_commit' – to organise my edits by purpose. I could keep experimental changes in 'playground' while my actual bugfix lived in 'ready_to_commit' – clean separation without complex branching.
I wanted to preserve that mental model.

Knowing that Git was the future, I decided to bring changelist support to it. It wasn't the first time I'd seen this pattern – extending a version control system to fit a particular workflow. First with our RCS wrapper, then with FCM, and now with [git-cl](https://github.com/BHFock/git-cl) – a command-line tool that adds changelists to Git.

If you come from SVN or [Perforce](https://www.perforce.com), changelists may already feel familiar. If you're Git-native, think of them as a pre-staging layer between your working copy and the index – or as sticky notes for your changed files, as I describe in the [git-cl tutorial](https://github.com/BHFock/git-cl/blob/main/docs/tutorial.md). This enables workflows like 'ok'/'do_not_commit', but also more nuanced ones with changelists like 'linter_run_ok', 'manual_review_ok', 'ai_review_ok', and so on – all while preparing your changes for integration. Does this replace branching? No. It’s another layer for organising your work. In fact, changelists help isolate uncommitted changes and move them to feature branches more cleanly.

Changelists aren't just a technical feature for me – they're a way of thinking about change itself. With [git-cl](https://github.com/BHFock/git-cl), I hope others can rediscover that clarity too.
