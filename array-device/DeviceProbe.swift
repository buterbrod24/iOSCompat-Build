import SwiftUI
import Foundation
import Darwin

@main struct ArrayDeviceProbe: App {
    var body: some Scene { WindowGroup { ProbeView() } }
}

private struct ProbeView: View {
    @State private var report = "Ready — native Swift Core evidence"
    @State private var ran = false
    @State private var url: URL?
    private let specialized: [String] = [
        "$sSa034_makeUniqueAndReserveCapacityIfNotB0yyFyXl_Ts5",
        "$sSa16_createNewBuffer14bufferIsUnique15minimumCapacity13growForAppendySb_SiSbtFyXl_Ts5",
        "$sSa37_appendElementAssumeUniqueAndCapacity_03newB0ySi_xntFyXl_Ts5",
        "$ss12_ArrayBufferV13_copyContents12initializings16IndexingIteratorVyAByxGG_SitSryxG_tFyXl_Ts5",
        "$ss12_ArrayBufferV19_getElementSlowPathyyXlSiFyXl_Ts5",
        "$ss12_ArrayBufferV20_consumeAndCreateNew14bufferIsUnique15minimumCapacity13growForAppendAByxGSb_SiSbtFyXl_Ts5",
        "$ss15ContiguousArrayV034_makeUniqueAndReserveCapacityIfNotD0yyFyXl_Ts5",
        "$ss15ContiguousArrayV12_endMutationyyFyXl_Ts5",
        "$ss15ContiguousArrayV15reserveCapacityyySiFyXl_Ts5",
        "$ss15ContiguousArrayV20_reserveCapacityImpl07minimumD013growForAppendySi_SbtFyXl_Ts5",
        "$ss15ContiguousArrayV36_reserveCapacityAssumingUniqueBuffer8oldCountySi_tFyXl_Ts5",
        "$ss15ContiguousArrayV37_appendElementAssumeUniqueAndCapacity_03newD0ySi_xntFyXl_Ts5",
        "$ss22_ContiguousArrayBufferV20_consumeAndCreateNew14bufferIsUnique15minimumCapacity13growForAppendAByxGSb_SiSbtFyXl_Ts5"
]
    private var reportPath: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("iOSCompat-ArrayReport-0.1.0.txt")
    }
    var body: some View {
        VStack(spacing: 16) {
            Text("Swift Core Array Probe 0.1.0").font(.title2.bold())
            Button("Run checks") { ran = true; run() }.disabled(ran)
            if let url { ShareLink(item: url) { Text("Share TXT report") } }
            ScrollView {
                Text(report).font(.system(.body, design: .monospaced))
                    .textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading)
            }
        }.padding().onAppear {
            if let saved = try? String(contentsOf: reportPath, encoding: .utf8) {
                report = saved; url = reportPath; ran = true
            }
        }
    }
    private func persist(_ rows: [String]) -> Bool {
        report = rows.joined(separator: "\n")
        do {
            try report.write(to: reportPath, atomically: true, encoding: .utf8)
            url = reportPath
            return true
        } catch {
            report += "\nFAIL journal save: " + error.localizedDescription
            return false
        }
    }
    private func run() {
        let version = ProcessInfo.processInfo.operatingSystemVersion
        var rows = ["iOSCompat Array Probe 0.1.0", "OS: " + ProcessInfo.processInfo.operatingSystemVersionString]
        guard version.majorVersion == 16 && version.minorVersion == 2 else {
            rows.append("STOP: this probe is restricted to iOS 16.2"); _ = persist(rows); return
        }
        rows.append("START native public API controls")
        guard persist(rows) else { return }
        let checks = ArrayOwnershipChecks.run()
        for (name,ok) in checks { rows.append("\(ok ? "PASS" : "FAIL") \(name)") }
        rows.append("TOTAL \(checks.filter { $0.1 }.count)/12")
        rows.append("START read-only lookup in libswiftCore with RTLD_FIRST")
        guard persist(rows) else { return }
        guard let handle = dlopen("/usr/lib/swift/libswiftCore.dylib", RTLD_LAZY | RTLD_LOCAL | RTLD_FIRST) else {
            rows.append("FAIL native provider load: " + (dlerror().map { String(cString: $0) } ?? "unknown")); _ = persist(rows); return
        }
        defer { dlclose(handle) }
        var specializedPresent = 0, genericPresent = 0
        for symbol in specialized {
            let present = dlsym(handle,symbol) != nil
            if present { specializedPresent += 1 }
            rows.append("SPECIALIZED \(present ? "PRESENT" : "ABSENT") \(symbol)")
            // Syntactic generic spelling hypothesis only, not a compatible replacement.
            guard symbol.hasSuffix("yXl_Ts5") else { rows.append("FAIL unexpected suffix"); _ = persist(rows); return }
            let generic = String(symbol.dropLast("yXl_Ts5".count))
            let found = dlsym(handle,generic) != nil
            if found { genericPresent += 1 }
            rows.append("GENERIC_QUERY \(found ? "PRESENT" : "ABSENT") \(generic)")
            guard persist(rows) else { return }
        }
        rows.append("LOOKUP specialized \(specializedPresent)/\(specialized.count); generic query \(genericPresent)/\(specialized.count)")
        rows.append("NOTE: lookup only. No private function called; no ABI compatibility inferred.")
        rows.append("COMPLETE")
        _ = persist(rows)
    }
}
