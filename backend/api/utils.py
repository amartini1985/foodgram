from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and response.status_code == 404:
        response.data = {
            'detail': 'Страница не найдена.',
        }

    if response is not None and response.status_code == 401:
        response.data = {
            'detail': 'Учетные данные не были предоставлены.',
        }

    return response
