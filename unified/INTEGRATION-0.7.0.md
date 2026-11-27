# Unified Probe 0.7.0 integration

48 top-level journaled cases (42 existing and six new batches), 52 new subchecks. Witness, opaque and mutation fixtures now load via three separate C-callable diagnostic client dylibs, with bitmask results and named checks. Main executable must not directly link those fixtures or clients. 15 embedded libraries expected. A loader failure becomes a test failure; a fatal call can still interrupt the current batch. No private ABI substitutions. CI and device execution unverified.
