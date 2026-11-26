import Foundation

@available(iOS 17.0, *)
@inline(never)
public func stockStream<T>(_ type:T.Type, _ policy:AsyncStream<T>.Continuation.BufferingPolicy)
    -> (stream:AsyncStream<T>, continuation:AsyncStream<T>.Continuation) {
    AsyncStream<T>.makeStream(of:type,bufferingPolicy:policy)
}

@available(iOS 17.0, *)
@inline(never)
public func stockThrowingStream<T>(_ type:T.Type, _ policy:AsyncThrowingStream<T,Error>.Continuation.BufferingPolicy)
    -> (stream:AsyncThrowingStream<T,Error>, continuation:AsyncThrowingStream<T,Error>.Continuation) {
    AsyncThrowingStream<T,Error>.makeStream(of:type,throwing:Error.self,bufferingPolicy:policy)
}
