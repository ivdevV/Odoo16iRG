-- Read-only inventory for historical slide.channel.partner references.
WITH admission_candidates AS (
    SELECT scp.id AS membership_id, oa.id AS candidate_id
      FROM slide_channel_partner scp
      JOIN op_admission oa
        ON oa.partner_id = scp.partner_id
       AND oa.batch_id = scp.batch_id
     WHERE scp.admission_id IS NULL
), admission_summary AS (
    SELECT membership_id, count(*) AS candidate_count
      FROM admission_candidates
  GROUP BY membership_id
), subject_candidates AS (
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
), subject_summary AS (
    SELECT membership_id, count(*) AS candidate_count
      FROM subject_candidates
  GROUP BY membership_id
)
SELECT
    count(*) FILTER (WHERE scp.admission_id IS NULL) AS without_admission,
    count(*) FILTER (WHERE scp.op_subject_id IS NULL) AS without_subject,
    count(*) FILTER (WHERE scp.admission_id IS NULL OR scp.op_subject_id IS NULL) AS without_either,
    count(*) FILTER (WHERE adm.candidate_count = 1) AS unique_admission_candidates,
    count(*) FILTER (WHERE adm.candidate_count > 1) AS ambiguous_admission_candidates,
    count(*) FILTER (WHERE sub.candidate_count = 1) AS unique_subject_candidates,
    count(*) FILTER (WHERE sub.candidate_count > 1) AS ambiguous_subject_candidates
  FROM slide_channel_partner scp
  LEFT JOIN admission_summary adm ON adm.membership_id = scp.id
  LEFT JOIN subject_summary sub ON sub.membership_id = scp.id;
