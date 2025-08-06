# Future Ideas for `git-cl`

This document outlines potential features that may be added to [git-cl](https://github.com/BHFock/git-cl?tab=readme-ov-file) in the future.  
These features are aligned with the long-term vision of `git-cl` as a changelist-centric workflow tool.  
They reflect the tool's philosophy of clarity, context, and composable workflows.

> **Disclaimer:** These ideas are not actively planned or under development.  
> I currently don't have time to work on them or to support community-driven development.  
> Please treat this as a design sketch, not a roadmap.

## Proposed Features

### `git cl mv list_old list_new`
Rename a changelist without altering its contents.

- Useful for refining intent as work evolves
- Keeps metadata intact

### `git cl join list_1 list_2 [...] list_new`
Combine two or more changelists into a new one.

- Merges file assignments from multiple lists
- Ideal for consolidating related work

### `git cl br list_name [branch_name]`
Create a new Git branch for a changelist.

- Automatically stashes other changelists
- Keeps target changelist active on new branch
- Enables focused, intent-driven branching

## Philosophy

These ideas extend `git-cl`'s core principle:  
**Organise work by intent, not just by history.**

They aim to support workflows where changelists are first-class citizens — composable, stashable, and branchable — without adding unnecessary complexity.
