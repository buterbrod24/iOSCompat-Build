#!/usr/bin/env python3
"""Compare exact native factory imports from independently compiled stock clients."""
import pathlib, sys

TARGETS = {
    "normal": "_$sScS10makeStream2of15bufferingPolicyScSyxG6stream_ScS12ContinuationVyx_G12continuationtxm_AG09BufferingE0Oyx__GtFZ",
    "throwing": "_$sScs10makeStream2of8throwing15bufferingPolicyScsyxs5Error_pG6stream_Scs12ContinuationVyxsAE_p_G12continuationtxm_sAE_pmAI09BufferingF0OyxsAE_p__GtsAE_pRs_rlFZ",
}

def main():
    directory = pathlib.Path(sys.argv[1])
    for os in ("16.2", "17.0"):
        for mode in ("Onone", "O"):
            prefix = directory / f"{os}-{mode}"
            imports = set(prefix.with_suffix(prefix.suffix + ".imports").read_text().splitlines())
            details = prefix.with_suffix(prefix.suffix + ".details").read_text().splitlines()
            for name, symbol in TARGETS.items():
                print(f"{os} {mode} {name}: {'DIRECT_IMPORT' if symbol in imports else 'NO_EXACT_IMPORT'}")
                for line in details:
                    if line.split() and line.split()[-1] == symbol:
                        print("  " + line.strip())
            print("  undefined symbols:", len(imports))
    print("Scope: compiler-generated object imports, not a loaded image or runtime execution.")
    print("No exact import does not prove that the fallback is correct or has no newer dependencies.")

if __name__ == "__main__":
    main()
