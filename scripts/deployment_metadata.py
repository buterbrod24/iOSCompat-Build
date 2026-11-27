"""Read-only deployment metadata from thin 64-bit Mach-O."""
import struct

PLATFORMS={1:"macOS",2:"iOS",3:"tvOS",4:"watchOS",5:"bridgeOS",6:"Mac Catalyst",
           7:"iOS Simulator",8:"tvOS Simulator",9:"watchOS Simulator",10:"DriverKit",
           11:"visionOS",12:"visionOS Simulator"}
LEGACY={0x24:1,0x25:2,0x2f:3,0x30:4}

def version(value):
    return [value>>16,(value>>8)&255,value&255]

def inspect_deployment(data,target="16.2"):
    if len(data)<32 or struct.unpack_from("<I",data)[0]!=0xfeedfacf:
        raise ValueError("not thin Mach-O 64")
    cpu,subtype,filetype,ncmd,size=struct.unpack_from("<5I",data,4)
    if size>len(data)-32 or ncmd>size//8:
        raise ValueError("invalid load commands")
    pos=32
    records=[]
    for _ in range(ncmd):
        if pos+8>32+size:
            raise ValueError("truncated load command")
        cmd,length=struct.unpack_from("<II",data,pos)
        if length<8 or length%8 or pos+length>32+size:
            raise ValueError("invalid load command")
        if cmd==0x32:
            if length<24:
                raise ValueError("short LC_BUILD_VERSION")
            platform,minimum,sdk,ntools=struct.unpack_from("<4I",data,pos+8)
            if length!=24+ntools*8:
                raise ValueError("invalid build tool count")
            tools=[{"tool":t,"version":version(v)} for t,v in
                   (struct.unpack_from("<II",data,pos+24+i*8) for i in range(ntools))]
            records.append(dict(command="LC_BUILD_VERSION",platform_id=platform,
                platform=PLATFORMS.get(platform,"unknown"),minimum=version(minimum),
                sdk=version(sdk),tools=tools))
        elif cmd in LEGACY:
            if length!=16:
                raise ValueError("invalid legacy deployment command")
            minimum,sdk=struct.unpack_from("<II",data,pos+8)
            platform=LEGACY[cmd]
            records.append(dict(command="LC_VERSION_MIN",platform_id=platform,
                platform=PLATFORMS[platform],minimum=version(minimum),sdk=version(sdk),tools=[]))
        pos+=length
    if pos!=32+size:
        raise ValueError("load command size mismatch")
    target_parts=[int(x) for x in target.split(".")]
    if len(target_parts)>3 or any(x<0 for x in target_parts):
        raise ValueError("invalid target version")
    target_parts += [0]*(3-len(target_parts))
    # Do not infer platform from an architecture alone or normalize conflicting records.
    if not records:
        status="metadata_missing"
    elif len(records)!=1:
        status="multiple_declarations_unverified"
    elif records[0]["platform_id"]!=2:
        status="non_ios_declaration"
    elif records[0]["minimum"]==[0,0,0]:
        status="minimum_unknown"
    elif records[0]["minimum"]>target_parts:
        status="minimum_above_target"
    elif cpu!=0x100000c or subtype&0xffffff!=0:
        status="architecture_unverified"
    else:
        status="declared_minimum_within_target"
    return {"target":target,"status":status,"filetype":filetype,"records":records,
            "scope":"Declared deployment metadata only; not a loader, ABI or runtime compatibility verdict"}
