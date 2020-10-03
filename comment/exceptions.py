from comment.messages import ExceptionError

try:
    from rest_framework.exceptions import APIException
except ModuleNotFoundError:
    APIException = Exception


class CommentBadRequest(APIException):
    status_code = 400
    default_detail = ExceptionError.BAD_REQUEST

    def __init__(self, detail=None, status_code=None):
        if status_code:
            self.status_code = status_code
        if not detail:
            detail = self.default_detail
        self.detail = detail
