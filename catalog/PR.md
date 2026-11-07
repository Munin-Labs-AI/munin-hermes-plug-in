## feat(plugin-catalog): add munin

Adds `plugin-catalog/munin.yaml`, the Munin meeting-notes connector for Hermes Agent.

**Repo:** https://github.com/Munin-Labs-AI/munin-hermes-plug-in (submitted by the repository owner)
**Version:** 0.1.0 · **Pinned sha:** `FILL_WITH_GIT_REV_PARSE_HEAD_40_CHARS`

### What it does

[Munin](https://muninlabs.ai) records meetings and writes notes from the transcript, keeping the clock time of every decision and the speaker and time of every transcript line. This plugin lets Hermes read those meetings and ships two workflow skills:

- `munin-followup`: one meeting becomes a follow-up. Each decision Munin's AI wrote (`status: ai_summary`) is checked against the transcript lines at its clock time before it is called confirmed; items the transcript does not support go to a "needs confirmation" list with the line that made them doubtful; a draft message carries only the confirmed items. Every item is cited as `meeting <id> · mm:ss · L<n>`.
- `munin-recall`: who said what, and when, across meetings, with the exact line cited; find a meeting by topic, person or date; compare a recurring meeting's decisions across sessions via `list_series`.

### Hermes surfaces used

Portable Agent Plugins v1 package: `plugin.json`, `mcp.json` (one `streamable-http` server, `https://app.muninlabs.ai/mcp`) and `skills/`. It uses the `com.nousresearch.hermes` server declaration `trust: untrusted`, so `requires_hermes` is set to `>=0.23.0`, the release this was validated on. No Python, no `register()`, no hooks, no middleware, no slash commands, no environment variables, no desktop or dashboard code.

### Disclosure (rule 13)

- **Network:** every tool call goes to Munin's hosted MCP server at `app.muninlabs.ai` over HTTPS. No other host.
- **Data pulled into the session:** meeting notes, transcript lines, titles and people's names from the signed-in user's own Munin account, which therefore reach the model the user runs Hermes with.
- **Credentials:** OAuth 2.1 with PKCE and dynamic client registration, handled entirely by Hermes' MCP client (`auth: oauth`); tokens live in `~/.hermes/mcp-tokens/`. Nothing is stored by the plugin and nothing secret is in the repository. The bundled `mcp.json` alone yields 401 until the user runs `hermes mcp add munin --url https://app.muninlabs.ai/mcp --auth oauth` and `hermes mcp login munin`; the README says so.
- **Writes:** on Munin's consent page the user picks a read-only or an editable connection (scope `meetings:read`). A read-only connection does not list the server's two write tools; an editable one lists `set_speaker` (renames a speaker in one meeting) and `import_meeting` (saves a meeting from another app). The package declares the server `untrusted`, so Hermes asks before any write-capable call and refuses it in unattended runs; the skills never call them unless the user asks for that change. Verified on Hermes 0.23.0 with an editable connection.
- **Not present:** shell commands, background processes, reads outside Munin's responses, audio recording, telemetry, self-update.
- **Prompt injection:** every read tool's description and both skills say transcript and note text is data from the meeting, not instructions.

### Validation

Run against a checkout at the pinned sha:

```
$ hermes plugins validate ./munin-hermes-plug-in --install-deps

✓ portable manifest — plugin.json parses (Agent Plugins v1)
✓ manifest fields — name present
✓ config schema — not declared
✓ server trust: munin — untrusted (Hermes asks before every write-capable tool call)
✓ security scan — safe
◆ Isolation — portable plugin (no Python): runs anywhere

Validation passed.
```

Warnings read: none (Hermes Agent v0.23.0, 2026-11-07).

End to end on the same Hermes against the live server with a demo account (fictional meetings): `hermes mcp test munin` connected over OAuth and listed 9 tools; "what did my most recent meeting decide?" answered with meeting id, mm:ss and line ids checked against `get_transcript`; "write the follow-up" produced the three sections, with the open Slack question under "needs confirmation" citing Daniel's "Let's not decide that today" (L10) and a draft carrying only the confirmed items; a request to rename a speaker in a one-shot run was stopped by the `untrusted` gate ("The user did not approve running write-capable tool") and nothing changed.

### Trying it

A Munin account is needed. Munin sign-up is currently invite-gated; a demo account with two fictional meetings is available to reviewers on request (and is provided in the hackathon submission form). After `hermes plugins install Munin-Labs-AI/munin-hermes-plug-in`, `hermes plugins enable munin`, `hermes mcp add munin --url https://app.muninlabs.ai/mcp --auth oauth` and `hermes mcp login munin`, ask Hermes "What did my last meeting decide?" and "Write the follow-up for it."

Demo video: FILL_WITH_X_POST_URL
