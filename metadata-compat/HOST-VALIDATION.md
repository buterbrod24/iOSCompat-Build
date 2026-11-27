# Independent module host validation

Swift 6.2.1, x86_64-unknown-linux-gnu, Swift language mode 5, separately compiled libraries and clients with library evolution enabled. The source of WitnessFixture/WitnessMeasure and OpaqueFixture/IndependentMeasure was reproduced from commit 54b150af67b960f65906055265d21862ff77291f; Linux shared-library build flags were substituted for Darwin linker flags.

| Fixture | -Onone | -O |
| --- | --- | --- |
| Witness | 8/8 | 8/8 |
| Opaque | 10/10 | 10/10 |

36/36 actual host checks passed. This is Linux host evidence only; it does not validate Mach-O, iOS 16.2, arm64, the legacy private runtime probe, or any of the five missing entrypoints. No binary aliases or system modifications were tested.
