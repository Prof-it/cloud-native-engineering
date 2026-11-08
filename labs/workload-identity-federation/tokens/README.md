# Token Claim Sets

Each file holds the claims of one GitHub Actions OIDC token for the fictitious repository `sharetable/website` (owner ID 51234567, repository ID 712345678). The claim names and the two subject formats follow GitHub's OIDC reference; the values are invented. Tokens are claims only: signature and expiry are verified by the cloud and are not part of this lab. Where a file has no `aud`, the evaluator uses the default audience of the cloud being checked, as the official login actions request it.

| Token | Situation |
|---|---|
| t1 | Push to `main`, repository not yet on immutable subjects: `repo:sharetable/website:ref:refs/heads/main` |
| t2 | Push to `main` after the switch: `repo:sharetable@51234567/website@712345678:ref:refs/heads/main` |
| t3 | Deploy job with `environment: production`: `...:environment:production` |
| t4, t10 | Pull request from a branch of the same repository, new and old format |
| t5 | Push to a feature branch |
| t6 | Another repository of the same owner |
| t7 | Name takeover: same owner and repository **names**, new **IDs** |
| t8 | Token minted for a different audience |
| t9 | Same claims from a different issuer |

[intended.json](intended.json) states who should be able to deploy: t1, t2 and t3.
