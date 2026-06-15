# IRG Course eLearning Featured Section

Adds a course-level featured block configured once on `op.course` and shown at the top of each linked eLearning subject channel.

## Usage

1. Open a course.
2. Go to the `Destacado eLearning` tab.
3. Enable `Mostrar destacado en eLearning`.
4. Fill in title, content, optional embed code and optionally a button URL.
5. Open any eLearning subject linked to the course; the block is rendered above the normal content list.

## Notes

- The module does not create or duplicate eLearning sections.
- The block is resolved from `slide.channel.op_subject_ids` and falls back to complementary `op.course.slide_channel_ids` when available.
- If the featured block is disabled or has no title/body, nothing is rendered.
- Embed snippets such as iframes must be added in `Código embebido`, not in the standard HTML editor field.
