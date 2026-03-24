import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data
        
        if isinstance(data, dict) and 'detail' in data:
            response.data = {'error': data['detail']}
        return response

    logger.exception("Uncaught exception by DRF: %s", str(exc))

    message = str(exc) if settings.DEBUG else "An internal server error occurred."
    
    data = {
        "error": message
    }
    
    return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
