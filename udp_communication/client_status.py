import enum


class ClientStatus(enum.Enum):
    GROUP_CREATOR = enum.auto()
    GROUP_JOINER = enum.auto()


class AcceptanceChoice:
    YES = "Y"
    NO = "N"
