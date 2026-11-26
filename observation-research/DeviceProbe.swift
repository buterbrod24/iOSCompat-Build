import SwiftUI
import Foundation
import Darwin

@main struct ObservationDeviceProbe: App {
    var body: some Scene { WindowGroup { ProbeView() } }
}

private struct ProbeView: View {
    @State private var report = "Ready — isolated Observation candidate"
    @State private var ran = false
    @State private var reportURL: URL?
    private let names = ["tracking returns value", "unrelated property ignored",
                         "tracked mutation notifies", "willSet observes old value",
                         "one-shot notification", "independent registrar identity",
                         "tracking can be installed again", "throwing mutation propagates error"]
    var body: some View {
        VStack(spacing: 16) {
            Text("Observation Probe 0.1.0").font(.title2.bold())
            Button("Run checks") { run() }.disabled(ran)
            if let url = reportURL { ShareLink(item: url) { Text("Share TXT report") } }
            ScrollView { Text(report).font(.system(.body, design: .monospaced)).textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading) }
        }.padding()
    }
    private func run() {
        ran = true
        var rows = ["iOSCompat Observation Probe 0.1.0", "OS: " + ProcessInfo.processInfo.operatingSystemVersionString]
        defer {
            report = rows.joined(separator: "\n")
            let url = FileManager.default.temporaryDirectory.appendingPathComponent("iOSCompat-ObservationReport-0.1.0.txt")
            do { try report.write(to: url, atomically: true, encoding: .utf8); reportURL = url }
            catch { report += "\nReport save failed: " + error.localizedDescription }
        }
        guard let frameworks = Bundle.main.privateFrameworksPath,
              let h = dlopen(frameworks + "/libObservationResearch.dylib", RTLD_NOW | RTLD_LOCAL | RTLD_FIRST) else {
            rows.append("FAIL load: " + (dlerror().map { String(cString: $0) } ?? "no library"))
            return
        }
        // Keep loaded for the process lifetime: Swift metadata can outlive a call.
        rows.append("PASS isolated dylib loaded")
        guard let symbol = dlsym(h, "ioscompat_observation_controls") else {
            rows.append("FAIL missing test entry"); return
        }
        typealias Entry = @convention(c) () -> Int32
        let mask = unsafeBitCast(symbol, to: Entry.self)()
        guard mask >= 0 && mask <= 255 else { rows.append("FAIL invalid test result"); return }
        var passed = 0
        for (i, name) in names.enumerated() {
            let ok = mask & (Int32(1) << i) != 0
            if ok { passed += 1 }
            rows.append("\(ok ? "PASS" : "FAIL") \(name)")
        }
        rows.append("TOTAL \(passed)/8")
    }
}
