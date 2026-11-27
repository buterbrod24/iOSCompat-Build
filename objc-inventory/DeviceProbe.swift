import SwiftUI
import Foundation

@main struct ObjCProbe: App {
    var body: some Scene { WindowGroup { ProbeView() } }
}

@MainActor
private struct ProbeView: View {
    @State private var report="Ready — Objective-C API inventory"
    @State private var ran=false
    @State private var url:URL?
    private var path:URL {
        FileManager.default.urls(for:.documentDirectory,in:.userDomainMask)[0]
            .appendingPathComponent("iOSCompat-ObjCReport-0.1.0.txt")
    }
    var body: some View {
        VStack(spacing:16) {
            Text("Objective-C Probe 0.1.0").font(.title2.bold())
            Button("Run checks") { ran=true; run() }.disabled(ran)
            if let url { ShareLink(item:url) { Text("Share TXT report") } }
            ScrollView {
                Text(report).font(.system(.body,design:.monospaced))
                    .textSelection(.enabled).frame(maxWidth:.infinity,alignment:.leading)
            }
        }.padding().onAppear {
            if let saved=try? String(contentsOf:path,encoding:.utf8) {
                report=saved;url=path;ran=true
            }
        }
    }
    private func persist(_ rows:[String]) -> Bool {
        report=rows.joined(separator:"\n")
        do { try report.write(to:path,atomically:true,encoding:.utf8);url=path;return true }
        catch { report+="\nFAIL journal save: "+error.localizedDescription;return false }
    }
    private func run() {
        var rows=["iOSCompat Objective-C Probe 0.1.0","OS: "+ProcessInfo.processInfo.operatingSystemVersionString]
        rows.append("START registered Objective-C metadata inventory")
        guard persist(rows) else { return }
        for name in ObjCInventory.classes {
            rows.append(ObjCInventory.classLine(name));guard persist(rows) else { return }
        }
        for name in ObjCInventory.protocols {
            rows.append(ObjCInventory.protocolLine(name));guard persist(rows) else { return }
        }
        for q in ObjCInventory.queries {
            rows.append(ObjCInventory.methodLine(q));guard persist(rows) else { return }
        }
        rows.append("TOTAL OBSERVATIONS \(ObjCInventory.classes.count+ObjCInventory.protocols.count+ObjCInventory.queries.count)")
        rows.append("NOTE: metadata only; no tested selector invoked; not observed is not global absence.")
        rows.append("COMPLETE")
        _=persist(rows)
    }
}
