from django.http import JsonResponse


class DABResponseData:
    status = 200
    data = None
    error = None
    anonymous = False
    msg = None

    def json(self):
        return {
            'data': self.data,
            'error': self.error,
            'anonymous': self.anonymous,
            'msg': self.msg
        }


class UTF8JsonResponse(JsonResponse):
    def __init__(self, *args, json_dumps_params=None, **kwargs):
        json_dumps_params = {"ensure_ascii": False, **(json_dumps_params or {})}
        super().__init__(*args, json_dumps_params=json_dumps_params, **kwargs)
