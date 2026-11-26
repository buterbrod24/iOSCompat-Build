import SwiftUI
import AppIntents

@main struct ActivityDeviceProbe: App {
    var body: some Scene {
        WindowGroup { ActivityChecks() }
    }
}

private struct ActivityChecks: View {
    @State private var report = "Ready — independent protocol only"
    @State private var running = false
    var body: some View {
        VStack {
            Button("Run local protocol checks") {
                running = true
                Task { @MainActor in
                    var rows: [String] = []
                    @MainActor func check(_ name: String, _ ok: Bool) {
                        rows.append("\(ok ? "PASS" : "FAIL") \(name)")
                        report = rows.joined(separator: "\n")
                    }
                    let local = LocalActivityIntent()
                    check("inherited generic witness", localThroughActivity(LocalActivityIntent.self))
                    check("native SystemIntent generic witness", localThroughSystem(LocalActivityIntent.self))
                    check("positive dynamic cast", localDynamic(local))
                    check("negative dynamic cast", !localDynamic(42))
                    check("native SystemIntent conformance", (local as Any) is any SystemIntent)
                    do {
                        _ = try await local.perform()
                        check("perform", true)
                    } catch { check("perform", false) }
                    report += "\nTOTAL \(rows.filter { $0.hasPrefix("PASS") }.count)/6"
                    running = false
                }
            }.disabled(running)
            ScrollView { Text(report).font(.system(.body, design: .monospaced)).textSelection(.enabled) }
        }.padding()
    }
}
