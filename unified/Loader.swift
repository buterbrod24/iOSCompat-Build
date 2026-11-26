import UIKit
import Foundation

@main final class UnifiedProbe: UIResponder, UIApplicationDelegate {
    var window:UIWindow?
    private let log = UITextView()
    private let run = UIButton(type:.system)
    private let share = UIButton(type:.system)
    private let suite = Suites()
    private var running = false
    private var reportURL:URL { FileManager.default.urls(for:.documentDirectory,in:.userDomainMask)[0].appendingPathComponent("iOSCompat-UnifiedReport-0.2.0.txt") }
    private var stateURL:URL { reportURL.deletingLastPathComponent().appendingPathComponent("unified-progress-0.2.0.json") }
    private struct Progress:Codable { var next = 0; var active:Int?; var lines:[String] = []; var passed = 0; var failed = 0; var evidence = 0; var interrupted = 0 }
    private var progress = Progress()
    func application(_ application:UIApplication,didFinishLaunchingWithOptions options:[UIApplication.LaunchOptionsKey:Any]?=nil)->Bool {
        let w = UIWindow(frame:UIScreen.main.bounds), host = UIViewController()
        log.isEditable = false
        log.font = .monospacedSystemFont(ofSize:13,weight:.regular)
        log.translatesAutoresizingMaskIntoConstraints = false
        run.setTitle("Run / resume all tests",for:.normal)
        share.setTitle("Share full TXT",for:.normal)
        run.addTarget(self,action:#selector(start),for:.touchUpInside)
        share.addTarget(self,action:#selector(send),for:.touchUpInside)
        let buttons = UIStackView(arrangedSubviews:[run,share])
        buttons.axis = .horizontal; buttons.distribution = .fillEqually
        buttons.translatesAutoresizingMaskIntoConstraints = false
        host.view.addSubview(buttons); host.view.addSubview(log)
        let safe = host.view.safeAreaLayoutGuide
        NSLayoutConstraint.activate([
            buttons.topAnchor.constraint(equalTo:safe.topAnchor,constant:8),
            buttons.leadingAnchor.constraint(equalTo:safe.leadingAnchor,constant:8),
            buttons.trailingAnchor.constraint(equalTo:safe.trailingAnchor,constant:-8),
            buttons.heightAnchor.constraint(equalToConstant:44),
            log.topAnchor.constraint(equalTo:buttons.bottomAnchor),
            log.leadingAnchor.constraint(equalTo:safe.leadingAnchor,constant:8),
            log.trailingAnchor.constraint(equalTo:safe.trailingAnchor,constant:-8),
            log.bottomAnchor.constraint(equalTo:safe.bottomAnchor)
        ])
        w.rootViewController = host; window = w; w.makeKeyAndVisible()
        if let data = try? Data(contentsOf:stateURL), let saved = try? JSONDecoder().decode(Progress.self,from:data) { progress = saved }
        if let i = progress.active {
            progress.lines.append("INTERRUPTED test \(i+1): previous process stopped before result; skipped on resume")
            progress.interrupted += 1; progress.next = i+1; progress.active = nil
        }
        refresh()
        return true
    }
    private func refresh() {
        let total = suite.cases().count
        let text = "iOSCompat Unified Probe 0.2.0\nOS: \(UIDevice.current.systemVersion)\nCompleted \(progress.next)/\(total); PASS \(progress.passed); FAIL \(progress.failed); EVIDENCE \(progress.evidence); INTERRUPTED \(progress.interrupted)\n\n" + progress.lines.joined(separator:"\n\n")
        log.text = text
        do {
            try FileManager.default.createDirectory(at:reportURL.deletingLastPathComponent(),withIntermediateDirectories:true)
            try JSONEncoder().encode(progress).write(to:stateURL,options:.atomic)
            try text.write(to:reportURL,atomically:true,encoding:.utf8)
        } catch { log.text += "\nSAVE FAILED: \(error)" }
    }
    @objc private func start() {
        guard !running else { return }
        let tests = suite.cases()
        if progress.next >= tests.count { progress = Progress(); suite.resetBatchAttempt() }
        running = true; run.isEnabled = false
        Task { @MainActor in
            while progress.next < tests.count {
                let i = progress.next, test = tests[i]
                progress.active = i
                progress.lines.append("START \(i+1): \(test.name)")
                refresh() // persistent journal before potentially fatal native call
                await Task.yield()
                do {
                    let result = try await test.run()
                    let evidence = test.name.contains("evidence") || test.name.contains("exports")
                    if evidence { progress.evidence += 1 } else { progress.passed += 1 }
                    progress.lines.append("\(evidence ? "EVIDENCE" : "PASS") \(test.name)\n\(result)")
                } catch {
                    progress.failed += 1
                    progress.lines.append("FAIL \(test.name)\n\(error)")
                }
                progress.active = nil; progress.next = i+1
                refresh()
                await Task.yield()
            }
            running = false; run.isEnabled = true
            run.setTitle("Run again",for:.normal)
        }
    }
    @objc private func send() {
        guard let host = window?.rootViewController else { return }
        refresh()
        let vc = UIActivityViewController(activityItems:[reportURL],applicationActivities:nil)
        vc.popoverPresentationController?.sourceView = share
        vc.popoverPresentationController?.sourceRect = share.bounds
        host.present(vc,animated:true)
    }
}
