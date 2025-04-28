from django.shortcuts import render
from django.views.generic.list import ListView
from fire.models import Locations, Incident, FireStation
from django.db.models import Q
import json

from django.db import connection
from django.http import JsonResponse
from django.db.models.functions import ExtractMonth

from django.db.models import Count
from datetime import datetime

class HomePageView(ListView):
    model = Locations
    context_object_name = 'home'
    template_name = "home.html"

class ChartView(ListView):
    template_name = 'chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    def get_queryset(self):
        pass

def PieCountbySeverity(request):
    query = '''
    SELECT severity_level, COUNT(*) as count
    FROM fire_incident
    GROUP BY severity_level
    '''
    data = {}
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    if rows:
        # Construct the dictionary with severity levels as keys and counts as values
        data = {severity: count for severity, count in rows}
    else:
        data = {}

    return JsonResponse(data)

def LineCountbyMonth(request):

    current_year = datetime.now().year

    result = {month: 0 for month in range(1, 13)}

    incidents_per_month = Incident.objects.filter(date_time__year=current_year) \
        .values_list('date_time', flat=True)
    
    # Count the number of incidents per month
    for date_time in incidents_per_month:
        month = date_time.month
        result[month] += 1

    # If you want to convert month numbers to month names, you can use a dictionary
    month_names = {
        1: 'Jan',
        2: 'Feb',
        3: 'Mar',
        4: 'Apr',
        5: 'May',
        6: 'Jun',
        7: 'Jul',
        8: 'Aug',
        9: 'Sep',
        10: 'Oct',
        11: 'Nov',
        12: 'Dec'
    }

    result_with_month_names = {
        month_names[int(month)]: count for month, count in result.items()}
    
    return JsonResponse(result_with_month_names)

def MultilineIncidentTop3Country(request):

    query = '''
        SELECT
        fl.country,
        strftime('%m', fi.date_time) AS month,
        COUNT(*) AS incident_count
    FROM
        fire_incident fi
    JOIN
        fire_locations fl ON fi.location_id = fl.id
    WHERE
        fl.country IN (
            SELECT
                fl_top.country
            FROM
                fire_incident fi_top
            JOIN
                fire_locations fl_top ON fi_top.location_id = fl_top.id
            WHERE
                strftime('%Y', fi_top.date_time) = strftime('%Y', 'now')
            GROUP BY
                fl_top.country
            ORDER BY
                COUNT(fi_top.id) DESC
            LIMIT 3
        )
        AND strftime('%Y', fi.date_time) = strftime('%Y', 'now')
    GROUP BY
        fl.country, month
    ORDER BY
        fl.country, month;
    '''

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
    
    # Initialize a dictionary to store the results
    result = {}

    # Initialize a set of months from January to December
    months = set(str(i).zfill(2) for i in range(1, 13))

    # Loop through the query results
    for row in rows:
        country = row[0]
        month = row[1]
        total_incidents = row[2]

        # If the country is not already in the result dictionary, initialize it with all months set to zero
        if country not in result:
            result[country] = {m: 0 for m in months}

        # Update the incident count for the corresponding month
        result[country][month] = total_incidents

    # Ensure there are alwayas 3 countries in the result
    while len(result) < 3:
        # Placeholder name for missing countries
        missing_country = f"Country {len(result) + 1}"
        result[missing_country] = {m: 0 for m in months}

    for country in result:
            result[country] = dict(sorted(result[country].items()))

    return JsonResponse(result)
    
def map_station(request):
    fireStations = FireStation.objects.values('name', 'latitude', 'longitude')

    for fs in fireStations:
        fs ['latitude'] = float (fs['latitude'])
        fs ['longitude'] = float (fs['longitude'])

    fireStations_list = list(fireStations)

    context = {
        'fireStations': fireStations_list
    }

    return render (request, 'map_station.html', context )

def map_incident(request):
    city_filter = request.GET.get('city')
    incidents_qs = Incident.objects.select_related('location')

    if city_filter:
        incidents_qs = incidents_qs.filter(location__city__iexact=city_filter)

    incident_list = []
    for incident in incidents_qs:
        location = incident.location
        incident_data = {
            'name': location.name,
            'latitude': float(location.latitude) if location.latitude else None,
            'longitude': float(location.longitude) if location.longitude else None,
            'address': location.address,
            'city': location.city,
            'country': location.country,
            'date_time': incident.date_time.strftime("%Y-%m-%d %H:%M:%S") if incident.date_time else '',
            'severity_level': incident.severity_level,
            'description': incident.description
        }
        if incident_data['latitude'] and incident_data['longitude']:
            incident_list.append(incident_data)

    cities = Locations.objects.values_list('city', flat=True).distinct()

    context = {
        'incidents': json.dumps(incident_list),
        'cities': sorted(set(cities)),
        'selected_city': city_filter or ''
    }
    return render(request, 'map_incident.html', context)