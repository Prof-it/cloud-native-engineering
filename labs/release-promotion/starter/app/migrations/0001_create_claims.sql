-- kind: expand
-- Creates the claims table. legacy_ref holds the reference from the old claims system.
CREATE TABLE claims (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_no    TEXT    NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    status       TEXT    NOT NULL,
    legacy_ref   TEXT
);
