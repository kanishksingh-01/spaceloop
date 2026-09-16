class SpaceLoopDomainException(Exception):
    pass

class GeofenceViolationException(SpaceLoopDomainException):
    pass

class InvalidRoomQrTokenException(SpaceLoopDomainException):
    pass

class ConditionDeltaFailedException(SpaceLoopDomainException):
    pass
