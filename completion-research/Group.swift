import Foundation

// Explicit completion for cooperating drivers only, not a SwiftUI transaction hook.
@MainActor
final class CompatCompletionGroup {
    enum Criterion { case logical, removed }
    enum Result:Equatable { case completed, cancelled }
    struct Token:Hashable { fileprivate let id=UUID() }
    private struct Track { var logical=false; var removed=false }
    private var tracks:[Token:Track]=[:]
    private var sealed=false
    private var callback:((Result)->Void)?
    private let criterion:Criterion
    private(set) var result:Result?
    init(_ criterion:Criterion, completion:@escaping(Result)->Void) {
        self.criterion=criterion;callback=completion
    }
    func register()->Token? {
        guard !sealed,result==nil,tracks.count<4096 else { return nil }
        let token=Token();tracks[token]=Track();return token
    }
    func seal() { sealed=true; evaluate() }
    func logical(_ token:Token) {
        guard result==nil,var track=tracks[token] else { return }
        track.logical=true;tracks[token]=track;evaluate()
    }
    func removed(_ token:Token) {
        guard result==nil,var track=tracks[token] else { return }
        track.logical=true;track.removed=true;tracks[token]=track;evaluate()
    }
    func cancel() { finish(.cancelled) }
    private func evaluate() {
        guard sealed,result==nil else { return }
        let done=tracks.values.allSatisfy{ criterion == .logical ? $0.logical : $0.removed }
        if done { finish(.completed) }
    }
    private func finish(_ value:Result) {
        guard result==nil else { return }
        result=value
        let notify=callback
        callback=nil
        tracks.removeAll()
        notify?(value)
    }
}
