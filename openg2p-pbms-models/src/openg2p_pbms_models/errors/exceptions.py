from typing import Optional

from .codes import PBMSErrorCodes


class PBMSException(Exception):
    def __init__(
        self,
        code: PBMSErrorCodes,
        payload: Optional[object] = None,
        message: Optional[str] = None,
    ):
        self.code: PBMSErrorCodes = code
        self.message: Optional[str] = message
        self.payload: object = payload
        super().__init__(code, self.message)
