---
name: pr-tour
description: Turn a PR into a guided review tour, a published HTML page that walks the changes in risk order and ties every claim to evidence the agent ran itself. Use for /pr-tour, "walk me through this PR", or help reviewing an AI-written PR.
---

# PR tour

The reader is a human reviewer who can't read every line and doesn't trust the PR's own story. The tour cuts their reading to the risky changes and replaces trust with **proof**: tests you ran, mutations you made, code you read. What the PR body says counts only as a claim.

Files beside this one: `template.html` (the page) and `build.py` (fills it from `tour.json` and the diff). Put working files in a scratch folder outside the repo, called `<work>` below.

## 1. Gather

- `gh pr view <n> -R <repo> --json title,body,author,baseRefName,headRefName,headRefOid,additions,deletions,changedFiles,files`
- `gh pr diff <n> -R <repo> > <work>/pr.diff`
- The ticket the PR links (Linear, Jira, a GitHub issue), read with whatever CLI or tool you have. It is the spec. If no ticket is linked, the PR body's stated goal is the spec.
- A checkout of the head in its own worktree, so the user's checkout stays untouched: `git worktree add <dir> <headRefOid>` (or the user's own worktree tool). Then install deps there.

Done when you hold the diff, the ticket text, and a checkout at the exact head SHA.

## 2. Map

Group hunks by **intent** (one reason to change), not by file. Each group is a step, with one tier:

- `risky`: auth, money, permissions, data deletion or migration, concurrency, anything that changes behaviour for every request, public API.
- `logic`: other behaviour changes, and new tests that carry the PR's proof.
- `mechanical`: renames, wiring, stubs, generated files, lockfiles. Say why each is safe.

Order the steps risky first. Done when every file in the diff belongs to a step (`build.py` fails otherwise).

## 3. Prove

For each `risky` and `logic` step:

- **Read** the connected code at head: callers, other readers of a changed value, the middleware or config it relies on. Record what you checked.
- **Run** the specs that cover it.
- **Mutate**: break the core line of the change (put back the old key, drop a check, widen a trust rule), rerun, then `git checkout -- .`. A red test means the mutant was caught. A green run means it survived: that is a test gap and goes in `gaps`.
- Copy the author's proof (curl matrix, review) as `claimed`. Never upgrade it to `ran`.
- Record each mutation once, as `killed` or `survived` under the step whose code it breaks. The page counts them for the verdict.

Run only the spec files the change touches. Done when every risky step has at least one `ran` or `killed` item, or its "why" says plainly that it is unproven. The worktree must also be clean (`git status --short` empty).

## 4. Question

Write down what the code can't answer, and who can: infra topology, product limits, cost. Mark a question `blocking` when a "no" would make the change unsafe. Compare the ticket with the code: `asked`, `extra` (scope beyond the ticket, with the reason), `missing`.

## 5. Build and publish

Write `<work>/tour.json` in this shape:

```
generatedAt, pr{repo,number,url,title,author,base,branch,head,files,additions,deletions},
verdict{tone: ok|warn|block, label, summary},
spec{ticket,ticketUrl,asked[],extra[],missing[]},
steps[{id,tier,title,say?,why,look[],evidence[{kind: ran|killed|survived|claimed|read, text}],
       questions[],files[{path,add,del}],hunks[{file,start,end,note?,open?}]}],
questions[{blocking,who,text}], gaps[], method
```

`hunks` take new-file line numbers at head, and `build.py` cuts those lines from the diff. Text fields support `` `code` `` only. Keep `why` to 2–4 sentences, written for someone who hasn't seen the code. The page is narrated by Mochi, a cat whose face follows the step's evidence. `say` is her one-line opener for the step, cheerful but factual (what to fear, what got proven); leave it out and a stock line for the tier is used.

```
python3 <this skill's folder>/build.py <work>/tour.json <work>/pr.diff <work>/pr-<n>-tour.html
```

It must print `0 problems`. If an Artifact tool is available, publish the HTML there (icon `code`). Otherwise give the user the file path. Reply with the link or path, the verdict, the blocking questions, and the gaps. Don't post to the PR unless asked. Remove the worktree, or tell the user it is still there.
