# Journal failure policy

Do not start a test unless JSON state and TXT report have both been atomically written. On pre-test failure attempt restoration of the previous in-memory checkpoint and stop. On post-test failure stop before the next test and retain the result in memory for retry. Sharing requires a successful refresh. Each file is atomic independently; this is not a two-file transaction. A process death between writes may leave a stale TXT report or an interrupted checkpoint. This change is source-reviewed only, not device-tested.
