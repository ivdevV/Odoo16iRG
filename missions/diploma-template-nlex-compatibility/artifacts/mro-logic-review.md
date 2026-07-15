# MRO and logic review

The compatibility addon explicitly depends on both interacting addons, so it is loaded
after their model extensions. Its `_amount_prod_final()` and `compute_avg_score()` call
`super()` first, preserving the inherited NLEX calculation, then overwrite the result
only when `_get_diploma_final_score()` returns a valid special-template result.

The special value helper retains all activation gates:

- template mode must be `diploma_50_50`;
- course must be identified as Diplomado;
- exactly one compulsory presencial subject must remain;
- at least one ordinary compulsory subject must remain.

Before identifying presencial/ordinary subjects, it excludes every subject for which
`op.subject.irg_is_grade_exempt()` is true. The NLEX addon defines that helper as a
case-insensitive `EX` marker check, which covers the test codes `NLEX01` through
`NLEX99`.

Static inspection finds no direct modification of existing addons and no missing import
or manifest dependency. Runtime MRO/registry behavior remains unverified because the
mandatory Docker compose environment could not be started.
