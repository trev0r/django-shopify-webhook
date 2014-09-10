import json
from functools import wraps

from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.conf import settings

from .helpers import domain_is_valid, hmac_is_valid, proxy_signature_is_valid


def webhook(f):
    """
    A view decorator that checks and validates a Shopify Webhook request.
    """

    @wraps(f)
    def wrapper(request, *args, **kwargs):
        # Try to get required headers and decode the body of the request.
        try:
            topic   = request.META['HTTP_X_SHOPIFY_TOPIC']
            domain  = request.META['HTTP_X_SHOPIFY_SHOP_DOMAIN']
            hmac    = request.META['HTTP_X_SHOPIFY_HMAC_SHA256'] if 'HTTP_X_SHOPIFY_HMAC_SHA256' in request.META else None
            data    = json.loads(request.body)
        except:
            return HttpResponseBadRequest()

        # Verify the domain.
        if not domain_is_valid(domain):
            return HttpResponseBadRequest()

        # Verify the HMAC.
        if not hmac_is_valid(request.body, settings.SHOPIFY_APP_API_SECRET, hmac):
            return HttpResponseForbidden()

        # Otherwise, set properties on the request object and return.
        request.webhook_topic   = topic
        request.webhook_data    = data
        request.webhook_domain  = domain
        return f(request, args, kwargs)

    return wrapper


def app_proxy(f):
    """
    A view decorator thats checks and validates a Shopify Application proxy request.
    """

    @wraps(f)
    def wrapper(request, *args, **kwargs):

        # Verify the signature.
        if not proxy_signature_is_valid(request, settings.SHOPIFY_APP_API_SECRET):
            return HttpResponseBadRequest()

        return f(request, args, kwargs)

    return wrapper
