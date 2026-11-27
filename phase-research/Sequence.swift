import Foundation

// Independent phase sequencing. A driver must acknowledge completion.
// No timers pretend to observe SwiftUI's native transaction completion.
public struct CompatPhaseSequence<Phase:Equatable, Trigger:Equatable> {
    public enum Mode { case once, repeating }
    public struct Step {
        public let token:UUID
        public let from:Phase
        public let to:Phase
    }
    public let phases:[Phase]
    public let mode:Mode
    public private(set) var index=0
    public private(set) var pending:Step?
    public private(set) var running=false
    private var lastTrigger:Trigger?
    public var phase:Phase { phases[index] }

    public init?(phases:[Phase],mode:Mode,initialTrigger:Trigger?=nil) {
        guard !phases.isEmpty,phases.count<=4096 else { return nil }
        self.phases=phases;self.mode=mode;self.lastTrigger=initialTrigger
    }

    // One-phase sequences are deliberately inert.
    public mutating func start()->Step? {
        guard !running,phases.count>1 else { return nil }
        running=true
        return advance()
    }
    // Local policy: ignore duplicate triggers; restart from the currently
    // requested phase when a distinct trigger arrives. Invalidate old tokens.
    public mutating func trigger(_ value:Trigger)->Step? {
        if let lastTrigger,lastTrigger==value { return nil }
        lastTrigger=value
        if running { cancel() }
        index=0
        return start()
    }
    public mutating func complete(_ token:UUID)->Step? {
        guard running,let step=pending,step.token==token else { return nil }
        pending=nil
        if index==0 && mode == .once {
            running=false
            return nil
        }
        return advance()
    }
    public mutating func cancel() {
        pending=nil;running=false
    }
    public mutating func reset() {
        cancel();index=0
    }
    private mutating func advance()->Step {
        let old=phase
        index=(index+1)%phases.count
        let step=Step(token:UUID(),from:old,to:phase)
        pending=step
        return step
    }
}
