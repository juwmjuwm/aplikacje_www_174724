from django.http import HttpResponse

def welcome_view(request):
    return HttpResponse("Witaj w The Timetable Planner!")
