#!/usr/bin/env python3
"""Offline replica of the checks Hermes runs when it loads a portable Agent Plugins v1 package.
Regexes and field sets are copied from hermes_cli/agent_plugins.py (NousResearch/hermes-agent, 2026-11-07).
Run: python3 scripts/offline-check.py [plugin dir]. Exit 0 when every check passes."""
import json, pathlib, re, sys
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
PLUGIN_NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
SKILL_NAME_RE = re.compile(r"^(?!.*--)[a-z0-9]+(?:-[a-z0-9]+)*$")
PLUGIN_FIELDS = {"$schema", "name", "version", "description", "author", "homepage", "repository", "license", "keywords", "extensions"}
AUTHOR_FIELDS = {"name", "email", "url"}
REMOTE_FIELDS = {"type", "url", "headers"}
problems = []
def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok: problems.append(msg)
m = json.loads((root / "plugin.json").read_text())
check(m.get("$schema") == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "plugin.json $schema is v1.0.0")
check(isinstance(m.get("name"), str) and 1 <= len(m["name"]) <= 64 and PLUGIN_NAME_RE.fullmatch(m["name"]) is not None, "plugin.json name satisfies v1 constraints")
check(set(m) <= PLUGIN_FIELDS, "plugin.json has only known top-level fields")
check(all(isinstance(m.get(f, ""), str) for f in ("version", "description", "homepage", "repository", "license")), "plugin.json string fields are strings")
check(isinstance(m.get("keywords", []), list) and all(isinstance(k, str) for k in m.get("keywords", [])), "plugin.json keywords are strings")
check(isinstance(m.get("author", {}), dict) and set(m.get("author", {})) <= AUTHOR_FIELDS, "plugin.json author has only name, email, url")
mc = json.loads((root / "mcp.json").read_text())
servers = mc.get("mcpServers", {})
check(bool(servers), "mcp.json declares at least one server")
for n, s in servers.items():
    check(set(s) <= REMOTE_FIELDS and s.get("type") == "streamable-http", f"mcp.json server {n} is streamable-http with known fields")
    check(isinstance(s.get("url"), str) and s["url"].startswith("https://") and "#" not in s["url"] and "@" not in s["url"], f"mcp.json server {n} url is https without user info or fragment")
decl = m.get("extensions", {}).get("com.nousresearch.hermes", {}).get("servers", {})
for n, d in decl.items():
    check(n in servers, f"declaration for server {n} matches an mcp.json entry")
    check(d.get("trust") in (None, "full", "untrusted"), f"declaration for server {n} trust is full or untrusted")
skills = sorted(p for p in (root / "skills").iterdir() if p.is_dir())
check(bool(skills), "skills/ has at least one skill")
try:
    import yaml
except ImportError:
    yaml = None
for d in skills:
    txt = (d / "SKILL.md").read_text(encoding="utf-8-sig")
    check(txt.startswith("---"), f"{d.name}: SKILL.md starts with frontmatter")
    end = re.search(r"\n---\s*\n", txt[3:])
    check(end is not None, f"{d.name}: frontmatter is terminated")
    if end is None or yaml is None:
        continue
    fm = yaml.safe_load(txt[3:end.start() + 3])
    check(fm.get("name") == d.name and SKILL_NAME_RE.fullmatch(d.name) is not None, f"{d.name}: name equals directory and matches the Agent Skills regex")
    check(isinstance(fm.get("description"), str) and 1 <= len(fm["description"]) <= 1024, f"{d.name}: description is 1 to 1024 chars ({len(str(fm.get('description', '')))})")
    check("compatibility" not in fm or (isinstance(fm["compatibility"], str) and 1 <= len(fm["compatibility"]) <= 500), f"{d.name}: compatibility is 1 to 500 chars")
    md = fm.get("metadata", {})
    check(isinstance(md, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in md.items()), f"{d.name}: metadata maps strings to strings")
    check("license" not in fm or isinstance(fm["license"], str), f"{d.name}: license is a string")
print("PASSED" if not problems else f"FAILED {len(problems)}")
sys.exit(1 if problems else 0)
