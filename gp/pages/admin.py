from django.contrib import admin
from .models import Lecturer, Course, SemesterSchedule, Department, Event
# Register your models here.
admin.site.register(Lecturer)
admin.site.register(Course)
admin.site.register(SemesterSchedule)
admin.site.register(Department)
admin.site.register(Event)
