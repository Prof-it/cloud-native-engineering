# Constructed ZAP Reports

`zap-target.json` and `zap-canary.json` are **constructed by hand**, not recorded. They follow the structure of ZAP's traditional JSON report (`-J` in the packaged scans): `@version`, `site[].alerts[]` with `pluginid`, `riskcode` 0 to 3, `confidence`, `riskdesc` and `instances[]`. The alerts are real ZAP passive rules:

| Plugin | Alert | Risk | Where |
|---|---|---|---|
| 10021 | X-Content-Type-Options Header Missing | Low (1) | target, `GET /health` |
| 10049 | Storable and Cacheable Content | Informational (0) | target, `GET /health` |
| 10038 | Content Security Policy (CSP) Header Not Set | Medium (2) | canary, `GET /canary/no-csp` |

A real scan needs a container runtime and the service under test. `solution/ci/run-control.sh dast` shows the commands; run it in a pipeline and replace these files with its output to see how much a real report differs.
