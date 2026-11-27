"""Independent diagnostic model of the documented Swift 5.7/5.9 request bits."""
from enum import IntEnum
from dataclasses import dataclass

class State(IntEnum):
    COMPLETE=0x00
    NON_TRANSITIVE_COMPLETE=0x01
    LAYOUT_COMPLETE=0x3f
    ABSTRACT=0xff

@dataclass(frozen=True)
class Request:
    state:State
    nonblocking:bool=False

    def __post_init__(self):
        if not isinstance(self.state,State) or type(self.nonblocking) is not bool:
            raise ValueError("invalid request fields")

    @classmethod
    def decode(cls,bits):
        # Conservative diagnostic decoder: unsupported future bits/states rejected.
        if type(bits) is not int or bits<0 or bits&~0x1ff:
            raise ValueError("unsupported request bits")
        return cls(State(bits&0xff),bool(bits&0x100))

    def encode(self):
        return int(self.state)|(0x100 if self.nonblocking else 0)

    def satisfied_by(self,observed):
        if not isinstance(observed,State):
            raise ValueError("unknown metadata state")
        return observed<=self.state

def assess_response(request,observed):
    """Classify a supplied observation; never inspect a metadata pointer."""
    if request.satisfied_by(observed):
        return "satisfied"
    if request.nonblocking:
        return "incomplete_nonblocking"
    return "inconsistent_blocking_observation"
