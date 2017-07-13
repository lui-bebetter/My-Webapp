
'''
API errors class.
'''

class APIError(Exception):
    '''
    the base APIError which contains error(required), data(optional) and message(optional).
    '''
    def __init__(self, error, data='', message=''):
        super(APIError, self).__init__(message)
        self.error = error
        self.data = data
        self.message = message

class APIValueError(APIError):
    '''
    Indicate the input value has error or invalid. The data specifies the error field of input form.
    '''
    def __init__(self,error='error:value invalid...', data='', message=''):
        super(APIValueError, self).__init__(error, data, message)

class APIResourceNotFound(APIError):
    '''
    Indicate the resource was not found. The data specifies the resource name.
    '''
    def __init__(self,error='error:resource not found...', data='', message=''):
        super(APIResourceNotFound, self).__init__(error, data, message)

class APIPermissionError(APIError):
    '''
    indicate the api has no permission.
    '''
    def __init__(self, error='error:permission forbidden...', data='permission', message=''):
        super(APIPermissionError, self).__init__(error, data, message)
        