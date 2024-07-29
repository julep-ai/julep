import "../common";

using Common;

namespace Jobs;

//
// JOB MODELS
//

/** Current state (one of: pending, in_progress, retrying, succeeded, aborted, failed) */
enum JobState {
    pending,
    in_progress,
    retrying,
    succeeded,
    aborted,
    failed,
    "unknown",
}

model JobStatus {
    ...HasId;
    ...HasTimestamps;

    /** Name of the job */
    @maxLength(120)
    name: identifierSafeUnicode = "";

    /** Reason for the current state of the job */
    reason: string = "";

    /** Whether this Job supports progress updates */
    has_progress: boolean = false;

    /** Progress percentage */
    @minValue(0)
    @maxValue(100)
    progress: float32 = 0.0;

    /** Current state of the job */
    state: JobState = JobState.pending;
}