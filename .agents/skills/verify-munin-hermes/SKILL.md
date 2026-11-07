---
name: verify-munin-hermes
description: Drive a real Hermes Agent install with this plugin the way a user does (install, enable, OAuth sign-in to Munin, ask for a follow-up and a quote) and leave command transcripts as proof. Use before any catalog PR or SHA bump, and whenever someone asks "does the plugin still work on Hermes X".
---

# verify-munin-hermes

Proves one commit of this repository works for a Hermes user. The plugin has no code of its own, so the surface under test is Hermes itself: its portable-package loader, its MCP OAuth client, and the two bundled skills driving the Munin server.

## Launch

Nothing to start. What has to be true first:

- `hermes --version` prints 0.23.0 or newer (the catalog floor).
- A Munin test account with at least one processed meeting that holds one decision and one proposal nobody agreed to. Never a real meeting, never a production account that holds real data.
- The `munin` entry exists in `~/.hermes/config.yaml` with `auth: oauth`, and a token is on disk from `hermes mcp login munin`. The login needs a person in the browser; it cannot run unattended.
- On a headless host reached over ssh, keep stdin open while the login waits or it exits at once: `sleep 3700 | hermes mcp login munin`, with `oauth.redirect_port: 43827` and `oauth.timeout: 3600` on the server entry, and `ssh -N -L 43827:127.0.0.1:43827 <host>` from the machine whose browser signs in. Verified 2026-11-07 on Hermes 0.23.0.
- A model the host can reach: OpenRouter refuses some model families by egress region ("This model is not available in your region"); pick one that answers a one-line test before blaming the plugin.

## Doctor

Read only. Run first, and again whenever a step fails in a way that smells like the environment.

```bash
hermes --version
hermes mcp test munin        # must list list_meetings, get_meeting, search_transcripts, get_transcript
hermes plugins list          # munin present and enabled
```

Pass: all three print what the comment says. Fail: stop and report the first failing line; do not drive.

## Drive

Run from a checkout at the commit under test, with `$PLUGIN_DIR` pointing at it.

1. Admission check, the same one catalog CI runs:
   ```bash
   hermes plugins validate "$PLUGIN_DIR" --install-deps
   ```
   Pass: `Validation passed.` Record every `⚠` line; they go into the PR description.
2. Install from the commit, the way a user does:
   ```bash
   hermes plugins install Munin-Labs-AI/munin-hermes-plug-in --no-enable   # or --ref <sha>
   hermes plugins enable munin
   hermes plugins list
   ```
   Pass: `munin` listed as enabled.
3. Recall, one shot:
   ```bash
   hermes chat --oneshot -q "Using the munin-recall skill: what did my most recent meeting decide? Cite each item as meeting id, mm:ss and line id."
   ```
   Pass: the answer names the test meeting and every item carries a meeting id and a clock time that `hermes mcp test` or a direct `get_meeting` call confirms.
4. Follow-up, one shot:
   ```bash
   hermes chat --oneshot -q "Using the munin-followup skill: write the follow-up for my most recent meeting."
   ```
   Pass: three sections appear (confirmed, needs confirmation, draft); the decision that the test transcript supports is under confirmed with a citation; the proposal nobody agreed to is under needs confirmation with the line that made it doubtful; the draft carries only the confirmed item.
5. Write guard: in the same account, ask Hermes to rename a speaker. With a read-only sign-in the tool is not listed and Hermes says so; with an editable sign-in Hermes must ask before calling `set_speaker`. Decline the prompt. Record which case applied.

## Evidence

Save each step's full command and output to `review/<date>-<gate>/<step>.txt`. A proof is the real user path: the command as a user types it, the complete answer, and the cross-check of every cited id and time against a tool call. A green `validate` alone is not a pass of steps 3 to 5. Report a skipped step with its reason. The evidence folder stays out of git when it contains meeting text from the test account; the PR links to the validate output only.

## Cleanup

`hermes plugins remove munin` when the install was only for the check. Tokens stay in `~/.hermes/mcp-tokens/`; never copy them anywhere.
