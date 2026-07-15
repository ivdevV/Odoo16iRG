# Static coverage review

The addon contains 17 post-install `TransactionCase` tests. The requested critical
scenarios have explicit assertions:

- `8.44 + six 10 = 9.22`: `test_production_regression_six_tens_and_8_44_is_9_22`.
- Variable module counts and exact `50 / N`: `test_variable_ordinary_module_counts`
  and `test_seven_modules_share_exactly_half_without_rounded_weights`.
- Shared standard template remains standard:
  `test_existing_solo_examen_template_stays_standard`.
- Master unchanged: `test_non_diplomado_keeps_standard_average`.
- Non-Diplomado product category authoritative:
  `test_non_diploma_category_is_authoritative_over_course_name`.
- Diplomado category with empty/inconsistent `course_type_id`:
  `test_category_identifies_diplomado_when_course_type_is_empty`.
- HOMECLASS suffix: `test_real_presential_suffix_is_normalized`.
- Zero/multiple presencial candidates:
  `test_diplomado_without_presential_keeps_standard_average` and
  `test_two_presential_candidates_keep_standard_average`.
- Recovery interaction:
  `test_recovery_uses_special_mode_without_changing_its_contract`.

This confirms intended test coverage only. Runtime correctness remains unverified
because Docker/Odoo could not be started.
