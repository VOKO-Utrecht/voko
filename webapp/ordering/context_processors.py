from ordering.models import PickupLocation


def pickup_locations(request):
    locations = PickupLocation.objects.all()
    return {
        'pickup_locations': locations
    }