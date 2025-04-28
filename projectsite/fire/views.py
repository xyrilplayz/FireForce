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