# Future Ideas for `git-cl`

This document outlines potential features that may be added to `git-cl` in the future. These features are aligned with the long-term vision of `git-cl` as a changelist-centric workflow tool. They reflect the tool’s philosophy of clarity, context, and composable workflows.

> Disclaimer: These ideas are not actively planned or under development.  
> I currently don't have time to work on them or to support community-driven development.  
> Please treat this as a design sketch, not a roadmap.

## Proposed Features

### `git cl stash`
Temporarily shelve changes in a changelist. Preserve the namelist, track stash reference, and show stashed state in `git cl st`.

### `git cl mv list_old list_new`
Rename a changelist without altering its contents.

### `git cl join list_1 list_2 [...] list_new`
Combine two or more changelists into a new one.

### `git cl unstage list`
Unstages all files from a changelist.

### `git cl br list_name [branch_name]`
Create a new Git branch for a changelist, handling file conflicts automatically. This would enable workflows where logical units of work (changelists) can be moved to dedicated branches for focused development or feature isolation.


