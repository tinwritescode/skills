# skills

Agent skills I use with Claude Code. Each folder is one skill: a `SKILL.md` plus any files it needs.

| Skill | What it does |
|---|---|
| [pr-tour](pr-tour/SKILL.md) | Turns a PR into a guided review page. Changes are ordered by risk, and each claim is tied to evidence the agent produced itself: tests it ran, mutations it made, code it read. |

## Install

```sh
git clone https://github.com/tinwritescode/skills.git ~/Coding/side/skills
ln -s ~/Coding/side/skills/pr-tour ~/.claude/skills/pr-tour
```

Then run `/pr-tour <PR link>` in Claude Code.

## Requirements

- `pr-tour`: `gh` (logged in), `git`, Python 3. It runs the project's own tests, so the repo's dependencies must install locally.
