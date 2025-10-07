import enum


class StatusEnum(enum.Enum):
    pending = "pending"
    processing = "processing"
    complete = "complete"
    not_applicable = "not_applicable"
    failed = "failed"


class ListWorkflowStatusEnum(enum.Enum):
    INITIATED = "initiated"
    APPROVED_FINAL_ENROLMENT = "approved_final_enrolment"
    APPROVED_FOR_DISBURSEMENT = "approved_for_disbursement"


class ListStageEnum(enum.Enum):
    ENROLLMENT = "enrollment"
    DISBURSEMENT = "disbursement"
