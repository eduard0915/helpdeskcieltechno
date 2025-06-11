from .models import Company


def company_info(request):
    """
    Context processor to make company information available in all templates
    """
    try:
        # Try to get the company information
        company = Company.objects.first()
        return {
            'company': company
        }
    except:
        # Return an empty dict if there's an error (e.g., table doesn't exist yet)
        return {'company': None}
