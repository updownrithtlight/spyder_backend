class CustomAPIException(Exception):
    def __init__(self, message="发生错误", status_code=400, code=1):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
