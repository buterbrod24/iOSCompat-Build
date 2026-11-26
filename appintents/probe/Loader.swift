import UIKit
import Darwin

@main final class AppIntentsCallableProbe: UIResponder, UIApplicationDelegate {
    var window: UIWindow?
    func application(_ application: UIApplication,
        didFinishLaunchingWithOptions options: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        let w = UIWindow(frame: UIScreen.main.bounds)
        let host = UIViewController()
        let log = UITextView()
        log.isEditable = false
        log.font = .monospacedSystemFont(ofSize: 14, weight: .regular)
        log.translatesAutoresizingMaskIntoConstraints = false
        host.view.addSubview(log)
        NSLayoutConstraint.activate([
            log.topAnchor.constraint(equalTo: host.view.safeAreaLayoutGuide.topAnchor, constant: 12),
            log.bottomAnchor.constraint(equalTo: host.view.safeAreaLayoutGuide.bottomAnchor, constant: -12),
            log.leadingAnchor.constraint(equalTo: host.view.safeAreaLayoutGuide.leadingAnchor, constant: 12),
            log.trailingAnchor.constraint(equalTo: host.view.safeAreaLayoutGuide.trailingAnchor, constant: -12)
        ])
        w.rootViewController = host
        window = w
        w.makeKeyAndVisible()
        log.text = "iOSCompat AppIntents Callable 0.1.0\nOS: \(UIDevice.current.systemVersion)\n"
        DispatchQueue.main.async {
            var passed = 0
            func check(_ name: String, _ ok: Bool) {
                if ok { passed += 1 }
                log.text += "\n\(ok ? "PASS" : "FAIL") \(name)"
            }
            func error() -> String { dlerror().map { String(cString: $0) } ?? "unknown error" }
            guard let dir = Bundle.main.privateFrameworksPath,
                  let h = dlopen(dir + "/libAppIntentsCompat.dylib", RTLD_NOW | RTLD_LOCAL) else {
                check("Compatibility library loads", false)
                log.text += "\n" + error() + "\n0/6 total"
                return
            }
            check("Compatibility library loads", true)
            check("Shortcut initializer resolves", dlsym(h, "$s10AppIntents0A8ShortcutV6intent7phrases10shortTitle15systemImageNameACx_SayAA0aC6PhraseVyxGG10Foundation23LocalizedStringResourceVSSYttcAA0A6IntentRzlufC") != nil)
            check("Default getter resolves", dlsym(h, "$s10AppIntents0A6IntentPAAE14isDiscoverableSbvgZ") != nil)
            guard let stock = dlopen(dir + "/libAppIntentsStockClient.dylib", RTLD_NOW | RTLD_LOCAL) else {
                check("Independent stock client loads", false)
                log.text += "\n" + error() + "\n\(passed)/6 total"
                return
            }
            check("Independent stock client loads", true)
            guard let entry = dlsym(stock, "ioscompat_stock_shortcut_test") else {
                check("Stock test entry resolves", false)
                log.text += "\n\(passed)/6 total"
                return
            }
            check("Stock test entry resolves", true)
            typealias Test = @convention(c) () -> Int32
            check("Stock shortcut construction returns", unsafeBitCast(entry, to: Test.self)() == 1)
            log.text += "\n\n\(passed)/6 total\n\nDefault getter address checked only. No shortcut registration or intent execution. Protocol descriptors not adapted."
        }
        return true
    }
}
