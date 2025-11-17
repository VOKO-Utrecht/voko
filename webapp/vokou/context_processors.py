# Context processor to make organization settings available in templates
from django.conf import settings


def organization(request):
    """
    Add organization-specific settings to template context.

    Makes the following variables available in all templates:
    - org_name: Full organization name
    - org_short_name: Short organization name
    - org_legal_name: Legal entity name
    - org_kvk: Chamber of Commerce number
    - org_email: General contact email
    - org_supplier_email: Supplier contact email
    - org_website: Public website URL
    """
    return {
        'org_name': settings.ORGANIZATION_NAME,
        'org_short_name': settings.ORGANIZATION_SHORT_NAME,
        'org_legal_name': settings.ORGANIZATION_LEGAL_NAME,
        'org_kvk': settings.ORGANIZATION_KVK,
        'org_email': settings.ORGANIZATION_EMAIL,
        'org_supplier_email': settings.ORGANIZATION_SUPPLIER_EMAIL,
        'org_website': settings.ORGANIZATION_WEBSITE,
    }
