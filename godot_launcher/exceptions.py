class CustomException(Exception):
    def __init__(self, message):
        self.message = message
    
class DownloadError(CustomException):
    def __str__(self):
        return f'Download Error -> {self.message}'    

class UnzipError(CustomException):
    def __str__(self):
        return f'Unzip Error -> {self.message}'    
        
class APIError(CustomException):
    def __str__(self):
        return f'API Error -> {self.message}'            