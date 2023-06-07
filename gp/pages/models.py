from django.core.validators import EmailValidator, RegexValidator
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    uni_id = models.CharField(max_length=20)

    def __str__(self):
        return self.user.username
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()



class Department(models.Model):
    department_name = models.CharField(max_length=100)
    department_code = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.department_name




DAYS_OF_WEEK = (
    ('1', 'Sunday'),
    ('2', 'Monday'),
    ('3', 'Tuesday'),
    ('4', 'Wednesday'),
    ('5', 'Thursday'),
)

class Course(models.Model):
    course_code = models.CharField(max_length=100)
    course_name = models.CharField(max_length=100)
    credit_hours = models.PositiveIntegerField(null=True)
    course_lecturer = models.ForeignKey('Lecturer', on_delete=models.SET_NULL, null=True, related_name='courses_taught')
    course_level = models.PositiveIntegerField(null=True)
    course_lab_lecturer = models.ForeignKey('Lecturer', on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_courses_taught')
    course_past_lecturers = models.ManyToManyField('Lecturer', related_name='past_courses', blank=True)
    course_time = models.TimeField(null=True, blank=True)
    course_day = models.CharField(max_length=1, choices=DAYS_OF_WEEK, null=True, blank=True)
    course_department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    course_building = models.CharField(max_length=100, blank=True, null=True)
    course_section = models.CharField(max_length=100, blank=True)
    course_prerequisites = models.ManyToManyField('Course', related_name='prerequisites', blank=True)

    def __str__(self):
        return self.course_name
    
    def day_name(self):
        return DAYS_OF_WEEK[int(self.course_day)-1][1]
    
class Lecturer(models.Model):
    lecturer_user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    lecturer_name = models.CharField(max_length=100)
    lecturer_email = models.EmailField(validators=[EmailValidator()])
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{10}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.",
    )
    lecturer_number = models.CharField(validators=[phone_regex], max_length=17)
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female')
    )
    lecturer_gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    TEACHER_TYPE_CHOICES = (
        ('L', 'Laboratory'),
        ('T', 'Theory')
    )
    lecturer_type = models.CharField(max_length=1, choices=TEACHER_TYPE_CHOICES)
    lecturer_past_courses = models.ManyToManyField('Course', related_name='past_lecturers', blank=True)
    lecturer_rating = models.FloatField(default=0.0)
    lecturer_department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.lecturer_name
    
    def get_all_assigned_courses(self):
        courses = Course.objects.filter(Q(course_lecturer=self) | Q(course_lab_lecturer=self))
        return courses


class Event(models.Model):
    event_name = models.CharField(max_length=100)
    event_description = models.TextField()

    def __str__(self):
        return self.event_name
    
    
class ExamSchedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    exam_date = models.DateField()
    start_time = models.TimeField()
    exam_type = models.CharField(max_length=20, default='Final')

    class Meta:
        unique_together = ('course', 'exam_date', 'start_time')


class SemesterSchedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=1, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()

    class Meta:
        unique_together = ('course', 'lecturer', 'day_of_week', 'start_time')
