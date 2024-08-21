from . import external_api_views
from celery import shared_task

@shared_task
def billing_request_process(request, **kwargs):
    GoCardless = external_api_views.GoCardlessIntegration()
    GoCardless.billing_request_process(request, **kwargs)

@shared_task
def cancel_billing_request(request, **kwargs):
    GoCardless = external_api_views.GoCardlessIntegration()
    GoCardless.cancel_billing_request(request, **kwargs)