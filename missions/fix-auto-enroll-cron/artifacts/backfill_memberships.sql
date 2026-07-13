-- One-shot template. Review membership-gaps-report.sql first and replace the final
-- ROLLBACK with COMMIT only after operations has approved the reported candidates.
BEGIN;

SELECT
    count(*) FILTER (WHERE admission_id IS NULL) AS admission_missing_before,
    count(*) FILTER (WHERE op_subject_id IS NULL) AS subject_missing_before
  FROM slide_channel_partner;

WITH candidates AS (
    SELECT scp.id AS membership_id, oa.id AS candidate_id
      FROM slide_channel_partner scp
      JOIN op_admission oa
        ON oa.partner_id = scp.partner_id
       AND oa.batch_id = scp.batch_id
     WHERE scp.admission_id IS NULL
), unique_candidates AS (
    SELECT membership_id, min(candidate_id) AS candidate_id
      FROM candidates
  GROUP BY membership_id
    HAVING count(*) = 1
)
UPDATE slide_channel_partner scp
   SET admission_id = unique_candidates.candidate_id
  FROM unique_candidates
 WHERE scp.id = unique_candidates.membership_id
   AND scp.admission_id IS NULL;

WITH candidates AS (
    SELECT DISTINCT scp.id AS membership_id, ostb.subject_id AS candidate_id
      FROM slide_channel_partner scp
      JOIN op_subject_to_batch ostb ON ostb.batch_id = scp.batch_id
      JOIN op_subject os
        ON os.id = ostb.subject_id
       AND os.slide_channel_id = scp.channel_id
     WHERE scp.op_subject_id IS NULL
    UNION
    SELECT DISTINCT scp.id AS membership_id, rel.op_subject_id AS candidate_id
      FROM slide_channel_partner scp
      JOIN op_course_op_subject_rel rel ON rel.op_course_id = scp.course_id
      JOIN op_subject os
        ON os.id = rel.op_subject_id
       AND os.slide_channel_id = scp.channel_id
     WHERE scp.op_subject_id IS NULL
       AND scp.batch_id IS NULL
), unique_candidates AS (
    SELECT membership_id, min(candidate_id) AS candidate_id
      FROM candidates
  GROUP BY membership_id
    HAVING count(*) = 1
)
UPDATE slide_channel_partner scp
   SET op_subject_id = unique_candidates.candidate_id
  FROM unique_candidates
 WHERE scp.id = unique_candidates.membership_id
   AND scp.op_subject_id IS NULL;

SELECT
    count(*) FILTER (WHERE admission_id IS NULL) AS admission_missing_after,
    count(*) FILTER (WHERE op_subject_id IS NULL) AS subject_missing_after
  FROM slide_channel_partner;

ROLLBACK;
