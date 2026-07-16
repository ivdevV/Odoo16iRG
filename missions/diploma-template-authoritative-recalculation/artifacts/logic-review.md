# Independent logic review

The addon is a new inheritance bridge and does not edit an existing addon.
Its dependency guarantees it loads after the prior beta detector and the full
50/50/NLEX compatibility chain.

The selected template mode `diploma_50_50` is the functional authority. The
overridden weighting helper intentionally does not consult course category,
type or name, while still requiring exactly one compulsory presencial subject
and at least one ordinary compulsory subject. Grade-exempt NLEX/EX subjects are
filtered through the inherited source of truth.

Both final computes call `super()` first and reapply the special result last.
The explicit `write()` recomputation is limited to `gradebook_id`, protected by
a context flag, and is covered by the observed 9.78 to 9.22 integration test.
Standard templates and invalid presencial topology retain inherited fallback.

No authentication, secrets, migration, destructive write or historical bulk
recomputation is introduced.
