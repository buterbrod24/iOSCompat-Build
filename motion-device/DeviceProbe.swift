import SwiftUI
import Foundation

@main struct MotionProbe:App {
    var body:some Scene { WindowGroup { ProbeView() } }
}

private struct ProbeView:View {
    @Environment(\.scenePhase) private var scenePhase
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var playback=CompatPlayback(duration:2)
    @State private var report="Run clock checks, then try the visual demo."
    @State private var url:URL?
    private let timeline=CompatMotionTimeline(initial:0,frames:[
        .spring(target:1,duration:1,model:CompatSpring(mass:1,stiffness:20,damping:4)!),
        .cubic(target:0,duration:1,endVelocity:0)])!
    private var now:Double { ProcessInfo.processInfo.systemUptime }

    var body:some View {
        VStack(spacing:16) {
            Text("Motion Probe 0.1.0").font(.title2.bold())
            TimelineView(.animation(minimumInterval:1.0/60,paused: !playback.running || reduceMotion)) { _ in
                let t=playback.position(now:now)
                let s=timeline.sample(at:t)
                VStack(spacing:8) {
                    GeometryReader { g in
                        ZStack(alignment:.leading) {
                            Capsule().fill(Color.secondary.opacity(0.15)).frame(height:8)
                            Circle().fill(Color.blue).frame(width:24,height:24)
                                .offset(x:CGFloat(max(0,min(1.3,s?.value ?? 0))/1.3)*max(0,g.size.width-24))
                        }.frame(maxHeight:.infinity)
                    }.frame(height:44)
                    Text(String(format:"t %.3f  value %.4f  velocity %.4f",t,s?.value ?? 0,s?.velocity ?? 0))
                        .font(.system(.caption,design:.monospaced))
                        .onChange(of:t) { _ in playback.finishIfNeeded(now:now) }
                }
            }
            HStack {
                Button("Play") { playback.play(now:now) }.disabled(reduceMotion || playback.running)
                Button("Pause") { playback.pause(now:now) }.disabled(!playback.running)
                Button("Reset") { playback.reset() }
            }.buttonStyle(.bordered)
            if reduceMotion { Text("Reduce Motion is enabled; visual playback disabled.").font(.caption) }
            Button("Run clock checks") { runChecks() }
            if let url { ShareLink(item:url) { Text("Share TXT report") } }
            ScrollView {
                Text(report).font(.system(.caption,design:.monospaced)).textSelection(.enabled)
                    .frame(maxWidth:.infinity,alignment:.leading)
            }
        }.padding()
            .onChange(of:scenePhase) { phase in if phase != .active { playback.pause(now:now) } }
            .onChange(of:reduceMotion) { enabled in if enabled { playback.pause(now:now) } }
            .onDisappear { playback.pause(now:now) }
    }
    private func runChecks() {
        let checks=PlaybackChecks.run()
        var lines=["iOSCompat Motion Probe 0.1.0","OS: "+ProcessInfo.processInfo.operatingSystemVersionString]
        for (n,ok) in checks { lines.append("\(ok ? "PASS" : "FAIL") \(n)") }
        lines.append("TOTAL \(checks.filter{$0.1}.count)/10")
        lines.append("Visual rendering and timing are manual observations, not automated passes.")
        lines.append("COMPLETE")
        report=lines.joined(separator:"\n")
        let path=FileManager.default.urls(for:.documentDirectory,in:.userDomainMask)[0].appendingPathComponent("iOSCompat-MotionReport-0.1.0.txt")
        do { try report.write(to:path,atomically:true,encoding:.utf8);url=path }
        catch { report+="\nFAIL report save: "+error.localizedDescription }
    }
}
