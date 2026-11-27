import Foundation

// Independent physical oscillator. Explicit SI-style coefficients, not
// Apple's perceptual duration/bounce mapping or SpringKeyframe ABI.
public struct CompatSpring {
    public let omega:Double
    public let ratio:Double
    public init?(mass:Double,stiffness:Double,damping:Double) {
        guard mass.isFinite, stiffness.isFinite, damping.isFinite,
              mass>0, stiffness>0, damping>=0 else { return nil }
        let w=sqrt(stiffness/mass)
        let z=(damping/mass)/(2*w)
        guard w.isFinite,w>0,z.isFinite,z>=0,z<=1000 else { return nil }
        omega=w;ratio=z
    }

    public func sample(from:Double,to:Double,velocity:Double,time:Double) -> (value:Double,velocity:Double)? {
        guard from.isFinite,to.isFinite,velocity.isFinite,time.isFinite,time>=0 else { return nil }
        if time==0 { return (from,velocity) }
        let x=from-to,w=omega,z=ratio,a=z*w
        guard x.isFinite,a.isFinite,(w*time).isFinite else { return nil }
        let displacement:Double, speed:Double
        if abs(z-1)<1e-8 {
            let b=velocity+w*x
            let e=exp(-w*time)
            displacement=e*(x+b*time)
            speed=e*(velocity-w*b*time)
        } else if z<1 {
            let q=w*sqrt((1-z)*(1+z))
            let b=(velocity+a*x)/q
            let angle=q*time
            let c=cos(angle),s=sin(angle),e=exp(-a*time)
            let u=x*c+b*s
            displacement=e*u
            speed=e*(-a*u+q*(-x*s+b*c))
        } else {
            // Stable slow root avoids cancellation when z is large.
            let k=z+sqrt((z-1)*(z+1))
            let r1 = -w/k
            let r2 = -w*k
            let c1=(velocity-r2*x)/(r1-r2)
            let c2=x-c1
            let v1=c1*exp(r1*time),v2=c2*exp(r2*time)
            displacement=v1+v2
            speed=r1*v1+r2*v2
        }
        let value=to+displacement
        guard value.isFinite,speed.isFinite else { return nil }
        return (value,speed)
    }
}
