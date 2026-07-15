# Logic review

The addon extends only `app.gradebook.student._is_diplomado_course()` and first
delegates to `super()`. Existing structured classification therefore remains valid.

When inherited detection returns false, the normalized course name is accepted only
if `Diplomado` or `Diplomados` appears at the beginning, or immediately after a
separator ` - `. This covers both tested beta forms:

- `Diplomado en ...`
- `TG - Diplomado en ...`

It does not match `Curso en ...`, nor arbitrary mid-sentence references. The addon does
not bypass the independent `diploma_50_50` template gate in the weighting helper, so a
standard template retains the inherited average until the selected template changes.

The dependency on `irg_diploma_gradebook_template_nlex_compat` establishes load order
after the NLEX/weighting bridge and preserves its MRO behavior.
