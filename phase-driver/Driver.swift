import Foundation

// Owns only the independent scalar engine, not SwiftUI transactions.
@MainActor
final class CompatPhaseDriver {
    typealias Sequence = CompatPhaseSequence<Double,Int>
    private var sequence:Sequence
    private let duration:Double
    private var lastTime:Double?
    private struct Active {
        let step:Sequence.Step
        let start:Double
        let timeline:CompatMotionTimeline
        let group:CompatCompletionGroup
        let track:CompatCompletionGroup.Token
    }
    private var active:Active?
    private(set) var state:CompatMotionState
    private(set) var completedSteps=0
    var running:Bool { active != nil }
    var requestedPhase:Double { sequence.phase }

    init?(phases:[Double],mode:Sequence.Mode,duration:Double,initialTrigger:Int?=nil) {
        guard phases.allSatisfy({$0.isFinite}),duration.isFinite,duration>0,
              let sequence=Sequence(phases:phases,mode:mode,initialTrigger:initialTrigger) else { return nil }
        self.sequence=sequence;self.duration=duration
        state=CompatMotionState(value:sequence.phase,velocity:0)
    }
    private func accept(_ now:Double)->Bool {
        guard now.isFinite,lastTime.map({now >= $0}) ?? true else { return false }
        lastTime=now;return true
    }
    private func discardActive() {
        active?.group.cancel()
        active=nil
    }
    private func install(_ step:Sequence.Step,now:Double) {
        guard let timeline=CompatMotionTimeline(initial:state.value,velocity:state.velocity,
                   frames:[.cubic(target:step.to,duration:duration,endVelocity:0)]) else {
            sequence.cancel();return
        }
        let group=CompatCompletionGroup(.removed){_ in}
        guard let token=group.register() else { sequence.cancel();return }
        group.seal()
        active=Active(step:step,start:now,timeline:timeline,group:group,track:token)
    }
    func start(now:Double) {
        guard accept(now),let step=sequence.start() else { return }
        install(step,now:now)
    }
    func trigger(_ value:Int,now:Double) {
        guard accept(now) else { return }
        // Sample without acknowledging the old step. A retrigger begins at the
        // physical presentation state, not the requested phase's nominal value.
        if let a=active,let s=a.timeline.sample(at:now-a.start) { state=s }
        guard let next=sequence.trigger(value) else { return }
        discardActive()
        install(next,now:now)
    }
    func tick(now:Double) {
        guard accept(now),let a=active else { return }
        let elapsed=now-a.start
        guard let s=a.timeline.sample(at:elapsed) else {
            discardActive();sequence.cancel();return
        }
        state=s
        guard elapsed>=a.timeline.duration else { return }
        a.group.removed(a.track)
        guard a.group.result == .completed else { return }
        active=nil
        completedSteps+=1
        // At most one transition per tick. No catch-up storm after a long gap.
        if let next=sequence.complete(a.step.token) { install(next,now:now) }
    }
    func cancel(now:Double) {
        guard accept(now) else { return }
        if let a=active,let s=a.timeline.sample(at:now-a.start) { state=s }
        discardActive();sequence.cancel()
        state=CompatMotionState(value:state.value,velocity:0)
    }
    func reset(now:Double) {
        guard accept(now) else { return }
        discardActive();sequence.reset()
        state=CompatMotionState(value:sequence.phase,velocity:0)
        completedSteps=0
    }
}
