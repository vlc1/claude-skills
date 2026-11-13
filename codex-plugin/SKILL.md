---
name: codex-plugin
description: Lessons for running Codex from Claude Code through the openai-codex plugin (/codex:review, /codex:adversarial-review, /codex:status, /codex:cancel). Use when launching a Codex review, choosing its target (--base), writing its focus text, giving Codex access to Kaimon, or diagnosing a run that dies with exit code 137 and no output.
---

# Codex plugin

Each rule below was learned on a real case: plugin `openai-codex/codex` 1.0.6,
codex-cli 0.160.0, Node v22.16.0 (`/usr/local/bin/node`), macOS, reviewing
StencilAlgebra (6 October 2026). Re-check versions before relying on one.

## Setup

- `node <plugin>/scripts/codex-companion.mjs setup --json` reports Node, the
  `codex` CLI and the login (`"ready": true`). Nothing else is needed for a
  review.
- Codex reads its MCP servers from `~/.codex/config.toml`, not from Claude
  Code: Kaimon is `[mcp_servers.kaimon]` there. Codex opens the checkout the
  command runs in, so a Kaimon gate must run in that checkout (the main one,
  not a worktree, when launched from the main checkout). After work in a
  worktree, the main checkout's gitignored Manifest may predate the merged
  `Project.toml` (`using` failed with `KeyError` on a new dependency):
  `Pkg.resolve()` there first.
- A plugin review cannot approve tool calls: every Kaimon call failed with
  "tool approval is required but forbidden by this session's policy". Codex
  calls without asking only the tools marked in `~/.codex/config.toml`, one
  table per tool:
  ```toml
  [mcp_servers.kaimon.tools.investigate_environment]
  approval_mode = "approve"
  ```
  Mark read-only tools (`investigate_environment`, `usage_instructions`,
  `search_methods`, `type_info`, `run_tests`); `ex` runs any code in the
  user's REPL and `edit_code` writes files, so leave them to the user.
- With several gates connected, a Kaimon call without a session key fails
  ("No session matched"): give the key in the brief.
- Tell Codex in the focus text to continue statically when Kaimon is
  unreachable, marking unchecked claims: it then still reports.

## Targets

- Automatic target: the working tree when dirty, else the branch against the
  default branch. On a clean `main` that diff is empty: pass `--base <commit>`
  (the commit before the work to review).
- The diff is inlined in the prompt only for at most 2 files and 256 KB;
  otherwise Codex gets the summary and reads the files itself. Give it a code
  map (which item lives in which file) and the notes to read first.
- `--cwd <path>` reviews another checkout than the session's: the companion
  runs git (`--base`) and Codex there. A review of two repositories ran from
  one with `--cwd` the other (the diff); the brief named the second checkout
  with absolute paths and Codex read it. Job state is per checkout:
  `/codex:status` and `/codex:cancel` need the same `--cwd <path>` (`--cwd`
  without a path fails: "Missing value for --cwd").
- `/codex:review` maps to the built-in reviewer and rejects focus text; use
  `/codex:adversarial-review` for a steered review.
- The adversarial template's attack surface is written for services (auth,
  tenants, migrations). For a library, say what the costly failures are
  instead (silent wrong numbers, broken GPU assumptions, public commitments).

## Focus text

The slash command passes everything as one double-quoted shell argument, which
the companion splits again (`splitRawArgumentString`):

- No backticks, `$` or `"`: the shell interprets them.
- No apostrophes: `'` opens a quote in the splitter (write "do not", not
  "don't"; "the gate of Codex", not "Codex's gate"). `\` escapes.
- Line breaks and runs of spaces collapse to one space: Codex reads one
  paragraph, so use inline markers such as (1), (2).
- Flags first (`--base 31a44ef` before the text); a lone `--` turns what
  follows into text.
- **Length: keep the whole argument under about 950 characters.** On this
  machine, `node <script> <argument>` is killed (SIGKILL, exit 137) once the
  argument is long: the companion ran with 983 characters of flags and text
  and died at 984, in the foreground and in the background alike. The killer
  is outside the plugin and outside the Claude Code sandbox (a one-line
  script dies too, with the sandbox off and with `env -i`), and spares
  `node -e` and `python3`; its identity is unknown.
- For a longer brief, write it to a file outside the repository (an untracked
  file inside would join a working-tree review) and pass a pointer:
  `--base <ref> Read the review brief in <path> and follow it.` Codex read a
  brief in Claude Code's scratchpad (`/private/tmp/…`), outside the checkout.

## Running and diagnosing

- For reviews the companion parses `--background` and `--wait` but always runs
  in the foreground: only `Bash(run_in_background: true)` detaches it.
- Job state lives in `$CLAUDE_PLUGIN_DATA/state/<repo>-<hash>/` (`state.json`,
  `jobs/*.json`, `jobs/*.log`), or `$TMPDIR/codex-companion/` without that
  variable. `status` lists the jobs of the current checkout; `cancel <job-id>`
  stops one.
- Exit 137 with an empty output and no job in `status`: the process died
  before the job was recorded, so Codex never ran. Bisect without contacting
  Codex: `--base no-such-ref-xyz` fails at `git merge-base` with exit 1 once
  the arguments parse, so 137 instead means the launch itself was killed.
  Then vary the argument length (`head -c N /dev/zero | tr '\0' a`).
- A probe with a valid base starts a real review: cancel it at once.
