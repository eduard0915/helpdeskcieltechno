from django.core.cache import cache
from django.db.utils import OperationalError

from .models import Company

CACHE_KEY = 'company_info'
CACHE_TIMEOUT = 300


def company_info(request):
    """
    Context processor to make company information available in all templates
    """
    company = cache.get(CACHE_KEY)
    if company is None:
        try:
            company = Company.objects.first()
            if company:
                cache.set(CACHE_KEY, company, CACHE_TIMEOUT)
        except (OperationalError, Company.DoesNotExist):
            # La tabla puede no existir todavía (primer arranque / migraciones)
            company = None
    return {'company': company}