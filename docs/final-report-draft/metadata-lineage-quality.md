# Metadata, Lineage, and Data Quality

The final architecture polish adds three inspection tools.

First, the feature registry explains stored feature keys. The storage layer only
sees strings such as `feature:user:42:click_count`. The registry gives that key
a meaning, source, value type, and list of models that use it.

Second, the quality layer validates raw events before they become features. It
checks simple rules such as required `user_id`, known `event_type`, valid
timestamps, and non-negative amounts. Invalid events are reported and skipped.

Third, the lineage layer records which feature keys were used by a prediction
and which prediction keys were written. This gives a small trace from input data
to model output.

Together, these pieces do not make the system bigger. They make it easier to
inspect:

```text
quality checks protect the input
feature registry explains the stored data
lineage explains the prediction
```

This is useful for the final report because it connects data systems with MLOps.
A model prediction is not only a number. It should be possible to ask what data
it used, whether anything was missing, and what the input features meant.
