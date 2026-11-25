# Test Keys

These RSA private keys (JWK with the private exponent `d`) exist only to sign and verify tokens in this lab's tests. They were generated for this repository, are used nowhere else and protect nothing. They are published on purpose.

| File | Role in the tests |
|---|---|
| `issuer-key-2026-11.json` | The issuer's current signing key; its public part is in `../jwks.json` |
| `issuer-key-rotated.json` | The issuer's next key; added in `../jwks-after-rotation.json` (T15) |
| `attacker-key.json` | A key that claims the issuer's `kid` (T04) |

Secret scanners may report these files, as well as the literal demonstration secrets in `../plan-flawed.json` and `../../../starter/terraform/platform.tf`. Those findings are expected. Do not copy these keys into anything real.
