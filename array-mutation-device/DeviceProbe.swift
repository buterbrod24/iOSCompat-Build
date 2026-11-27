import SwiftUI
import Foundation

@main struct MutationProbe: App {
    var body: some Scene { WindowGroup { ProbeView() } }
}

private struct ProbeView: View {
    @State private var report = "Ready"
    @State private var reportURL: URL?
    @State private var ran = false
    private var path: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("iOSCompat-ArrayMutationReport-0.1.0.txt")
    }
    var body: some View {
        VStack(spacing: 16) {
            Text("Array Mutation Probe 0.1.0").font(.title2.bold())
            Button("Run checks") { ran = true; run() }.disabled(ran)
            if let reportURL { ShareLink(item: reportURL) { Text("Share TXT report") } }
            ScrollView {
                Text(report).font(.system(.body, design: .monospaced))
                    .textSelection(.enabled).frame(maxWidth: .infinity, alignment: .leading)
            }
        }.padding().onAppear {
            if let saved = try? String(contentsOf: path, encoding: .utf8) {
                report = saved; reportURL = path; ran = true
            }
        }
    }
    private func persist(_ lines: [String]) -> Bool {
        report = lines.joined(separator: "\n")
        do {
            try report.write(to: path, atomically: true, encoding: .utf8)
            reportURL = path
            return true
        } catch {
            report += "\nFAIL journal save"
            return false
        }
    }
    private func run() {
        let v = ProcessInfo.processInfo.operatingSystemVersion
        var lines = ["iOSCompat Array Mutation Probe 0.1.0",
                     "OS: " + ProcessInfo.processInfo.operatingSystemVersionString]
        guard v.majorVersion == 16 && v.minorVersion == 2 else {
            lines.append("STOP: requires iOS 16.2"); _ = persist(lines); return
        }
        lines.append("START")
        guard persist(lines) else { return }
        let rows = MutationChecks.run()
        for (name, ok) in rows {
            lines.append("\(ok ? "PASS" : "FAIL") \(name)")
            guard persist(lines) else { return }
        }
        lines.append("TOTAL \(rows.filter { $0.1 }.count)/\(rows.count)")
        lines.append("COMPLETE")
        _ = persist(lines)
    }
}
