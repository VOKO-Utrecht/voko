import csv
from django.http import HttpResponse
import datetime
import simplejson as json


def CSVResponse(data):
    response = HttpResponse(content_type='text/csv')
    writer = csv.writer(response)
    field_names = data[0].keys()
    writer.writerow(field_names)
    for order_round in data:
        row = order_round.values()
        writer.writerow(row)

    return response


def JSONResponse(data):
    def default(o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

    response_data = json.dumps(
        data,
        sort_keys=True,
        indent=1,
        default=default
    )

    return HttpResponse(response_data, content_type="application/json")
