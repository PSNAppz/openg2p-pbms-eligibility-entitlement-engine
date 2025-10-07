from typing import Optional

from .codes import BGTaskErrorCodes


class BGTaskException(Exception):
    def __init__(
        self,
        code: BGTaskErrorCodes,
        payload: Optional[object] = None,
        message: Optional[str] = None,
    ):
        self.code: BGTaskErrorCodes = code
        self.message: Optional[str] = message
        self.payload: object = payload
        super().__init__(code, self.message)
