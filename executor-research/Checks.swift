import Foundation
import Dispatch

// Source-level control using the original iOS 16 executor API.
// No new runtime exports or replacement of native protocol descriptors.
final class QueueExecutor: SerialExecutor, @unchecked Sendable {
    private let queue = DispatchQueue(label: "net.ioscompat.executor.control")
    func asUnownedSerialExecutor() -> UnownedSerialExecutor {
        UnownedSerialExecutor(ordinary: self)
    }
    func enqueue(_ job: UnownedJob) {
        let executor = asUnownedSerialExecutor()
        queue.async { job.runSynchronously(on: executor) }
    }
}

actor ExecutorControl {
    private let executor = QueueExecutor()
    nonisolated var unownedExecutor: UnownedSerialExecutor {
        executor.asUnownedSerialExecutor()
    }
    private var count = 0
    private var sequence: [Int] = []
    func append(_ value: Int) { sequence.append(value) }
    func snapshot() -> [Int] { sequence }
    func increment() { count += 1 }
    func value() -> Int { count }
}

enum ExecutorChecks {
    static func run() async -> [(String, Bool)] {
        let actor = ExecutorControl()
        await actor.increment()
        let first = await actor.value()
        await withTaskGroup(of: Void.self) { group in
            for _ in 0..<100 {
                group.addTask { await actor.increment() }
            }
        }
        let total = await actor.value()
        for i in 0..<32 { await actor.append(i) }
        let sequence = await actor.snapshot()
        let other = ExecutorControl()
        await other.increment()
        let otherCount = await other.value()
        let originalCount = await actor.value()
        let rows = [("first job", first == 1), ("100 concurrent submissions", total == 101), ("sequential submissions preserve order", sequence == Array(0..<32)), ("independent actor state", otherCount == 1 && originalCount == 101)]
        return rows
    }
}
