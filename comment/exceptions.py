from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST


class CommentBadRequest(APIException):
    status_code = HTTP_400_BAD_REQUEST
    default_detail = 'Bad Request'

    def __init__(self, detail=None, status_code=None):
        if status_code:
            self.status_code = status_code
        if not detail:
            detail = self.default_detail
        self.detail = detail
