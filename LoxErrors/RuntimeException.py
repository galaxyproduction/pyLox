class RuntimeException(RuntimeError):
    def __init__(self, token, message):
        self.token = token
        super(RuntimeError, self).__init__(message)