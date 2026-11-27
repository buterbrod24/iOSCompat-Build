import Foundation

// Explicit monotonic playback clock. No wall-clock or frame-count dependency.
struct CompatPlayback {
    let duration:Double
    private(set) var elapsed:Double=0
    private(set) var started:Double?
    init(duration:Double) { self.duration=duration.isFinite ? max(0,duration) : 0 }
    func position(now:Double)->Double {
        guard let started,now.isFinite else { return elapsed }
        return min(duration,elapsed+max(0,now-started))
    }
    mutating func play(now:Double) {
        guard now.isFinite,started==nil,duration>0 else { return }
        if elapsed>=duration { elapsed=0 }
        started=now
    }
    mutating func pause(now:Double) {
        elapsed=position(now:now);started=nil
    }
    mutating func reset() { elapsed=0;started=nil }
    mutating func finishIfNeeded(now:Double) {
        if started != nil && position(now:now)>=duration { pause(now:now) }
    }
    var running:Bool { started != nil }
}
enum PlaybackChecks {
    static func run()->[(String,Bool)] {
        var p=CompatPlayback(duration:2)
        var r:[(String,Bool)]=[]
        r.append(("initial",p.position(now:10)==0 && !p.running))
        p.play(now:10)
        r.append(("elapsed time",p.position(now:10.5)==0.5))
        p.play(now:10.5)
        r.append(("duplicate play ignored",p.position(now:11)==1))
        p.pause(now:11)
        r.append(("pause freezes",p.position(now:100)==1 && !p.running))
        p.play(now:100)
        r.append(("resume preserves position",p.position(now:100.5)==1.5))
        r.append(("clamp at end",p.position(now:110)==2))
        p.finishIfNeeded(now:110)
        r.append(("completion stops clock",!p.running && p.elapsed==2))
        p.play(now:120)
        r.append(("replay from start",p.position(now:120)==0))
        p.reset()
        r.append(("reset stops and clears",!p.running && p.elapsed==0))
        p.play(now:.nan)
        r.append(("invalid clock rejected",!p.running))
        return r
    }
}
