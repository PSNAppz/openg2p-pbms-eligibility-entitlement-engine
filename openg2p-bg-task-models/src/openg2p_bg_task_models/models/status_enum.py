import enum


class StatusEnum(enum.Enum):
    pending = "pending"
    processing = "processing"
    failed = "failed"
    complete = "complete"
    not_applicable = "not_applicable"
