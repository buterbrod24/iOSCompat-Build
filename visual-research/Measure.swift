import CoreGraphics
import Foundation

@main struct Measure {
    static func main() {
        let base=CompatVisualTransform()
        let center=CGPoint(x:0.5,y:0.5),size=CGSize(width:100,height:80)
        let scaled=base.scale(0.5,anchor:center,size:size)!
        let a=scaled.offset(x:10,y:20)!
        let b=base.offset(x:10,y:20)!.scale(0.5,anchor:center,size:size)!
        let start=CGPoint(x:0,y:0)
        let leading=CompatScrollSample.sample(item:-25...25,viewport:0...100)!
        let trailing=CompatScrollSample.sample(item:75...125,viewport:0...100)!
        let inside=CompatScrollSample.sample(item:20...60,viewport:0...100)!
        let huge=CompatScrollSample.sample(item:-50...150,viewport:0...100)!
        let rtl=CompatScrollSample.sample(item:-25...25,viewport:0...100,reversed:true)!
        let outside=CompatScrollSample.sample(item:110...140,viewport:0...100)!
        let rows:[(String,Bool)]=[
            ("identity transform",base.matrix.isIdentity && base.opacity==1),
            ("center stays fixed",CGPoint(x:50,y:40).applying(scaled.matrix)==CGPoint(x:50,y:40)),
            ("scale then offset",start.applying(a.matrix)==CGPoint(x:35,y:40)),
            ("offset then scale",start.applying(b.matrix)==CGPoint(x:30,y:30)),
            ("modifier order preserved",a.matrix != b.matrix),
            ("opacity multiplication",base.faded(0.5)?.faded(0.5)?.opacity==0.25),
            ("nonfinite effect rejected",base.offset(x:.infinity,y:0)==nil && base.faded(-1)==nil),
            ("leading partial visibility",leading.phase == .leading && leading.progress == -0.5),
            ("trailing partial visibility",trailing.phase == .trailing && trailing.progress == 0.5),
            ("visible identity",inside.phase == .identity && inside.progress==0),
            ("oversized item covering viewport",huge.phase == .identity),
            ("reverse axis direction",rtl.phase == .trailing && rtl.progress==0.5),
            ("fully outside trailing",outside.phase == .trailing && outside.progress==1),
            ("empty viewport rejected",CompatScrollSample.sample(item:1...2,viewport:0...0)==nil)
        ]
        for (n,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(n)") }
        print("TOTAL \(rows.filter{$0.1}.count)/14")
        if rows.contains(where:{!$0.1}) { exit(1) }
    }
}
