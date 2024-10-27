from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Dice(_message.Message):
    __slots__ = ("dice",)
    DICE_FIELD_NUMBER: _ClassVar[int]
    dice: str
    def __init__(self, dice: _Optional[str] = ...) -> None: ...

class DiceResult(_message.Message):
    __slots__ = ("input", "result")
    INPUT_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    input: str
    result: str
    def __init__(self, input: _Optional[str] = ..., result: _Optional[str] = ...) -> None: ...
