from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

def error_404_handler(request, exception=None):
    return JsonResponse({
        "error": "Route not found or resource does not exist."
    }, status=404)

def error_500_handler(request, exception=None):
    logger.error("Internal Server Error: %s", exception)
    return JsonResponse({
        "error": "An internal server error occurred."
    }, status=500)

def error_400_handler(request, exception):
    return JsonResponse({
        "error": "Bad Request."
    }, status=400)

def error_403_handler(request, exception=None):
    return JsonResponse({
        "error": "Permission Denied (Forbidden)."
    }, status=403)
