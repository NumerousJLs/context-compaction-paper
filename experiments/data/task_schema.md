# Task Schema

Each task record contains:

- `task_id`
- `family`
- `scenario`
- `failure_mode`
- `prefix_turns`
- `recent_turns`
- `candidate_sets`
- `gold`
- `state`

`candidate_sets` contains five labeled fields:

- `goal`
- `file`
- `constraint`
- `detail`
- `next_step`

The evaluator asks the model to return one candidate ID per field.

`state` stores the canonical task state used for artifact construction.
