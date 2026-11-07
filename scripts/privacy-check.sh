#!/usr/bin/env bash
# Refuses a commit that would put a secret, a local path or a private host into this public repository.
# Run before every commit: scripts/privacy-check.sh. Exit 1 on any hit. Project-specific words live in a private file
# outside the repository (private/forbidden-words.txt, one regex per line) so the list itself is never published.
set -u
cd "$(dirname "$0")/.."
pat='munin_pat_|[Bb]earer [A-Za-z0-9]{8,}|access_token|client_secret|/Users/|/home/|~/\.hermes/mcp-tokens/[^/ ]+\.json|BEGIN (RSA|OPENSSH) PRIVATE KEY'
hits=$(git ls-files -c -o --exclude-standard | grep -v -E '^(private/|review/|scripts/privacy-check\.sh)' | xargs grep -n -E "$pat" 2>/dev/null)
if [ -f private/forbidden-words.txt ]; then
  extra=$(git ls-files -c -o --exclude-standard | grep -v -E '^(private/|review/|scripts/privacy-check\.sh)' | xargs grep -n -i -E -f private/forbidden-words.txt 2>/dev/null)
  hits="$hits${extra:+
$extra}"
fi
if [ -n "${hits//[[:space:]]/}" ]; then
  echo "PRIVACY_FAIL: these lines must not enter the public repo"; echo "$hits"; exit 1
fi
echo "PRIVACY_OK: no secret, account, local path or internal host in tracked or untracked repo files"
