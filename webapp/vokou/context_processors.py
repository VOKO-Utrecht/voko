from django.conf import settings


def organization(request):
    return {
        "org_name": getattr(settings, "ORGANIZATION_NAME", ""),
        "org_short_name": getattr(settings, "ORGANIZATION_SHORT_NAME", ""),
        "org_legal_name": getattr(settings, "ORGANIZATION_LEGAL_NAME", ""),
        "org_kvk": getattr(settings, "ORGANIZATION_KVK", ""),
        "org_email": getattr(settings, "ORGANIZATION_EMAIL", ""),
        "org_supplier_email": getattr(settings, "ORGANIZATION_SUPPLIER_EMAIL", ""),
        "org_website": getattr(settings, "ORGANIZATION_WEBSITE", ""),
    }
