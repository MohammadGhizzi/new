from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from .models import Course, Lecturer, ExamSchedule, Event, Department, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
import datetime
import math
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q,F
from django.core.mail import send_mail
from django.conf import settings


        
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('landing')
        else:
            error_message = 'Invalid username or password. Please try again.'
            return render(request, 'login.html', {'error_message': error_message})
    else:
        return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def landing(request):
    if request.user.is_superuser:
        events = Event.objects.all()
        return render(request, 'landing.html', {'user': request.user, 'events': events})
    
    return redirect('lecturer_view')

def calendar(request):
    return render(request, 'calendar.html')



########## COURSES ##########
from django.db.models import F

@login_required(login_url='login')
def courses(request):
    # Fetch all courses from the database
    courses = Course.objects.all()
    lecturers = Lecturer.objects.all()
    departments = Department.objects.all()
    
    # Get the 'order' parameter from the URL query parameters
    order = request.GET.get('order')
    
    if order:
        # If the 'order' parameter is provided, apply sorting to the queryset
        if order.startswith('-'):
            # If the order starts with '-', it means descending order
            courses = courses.order_by(F(order[1:]).desc())
        else:
            # Otherwise, it's ascending order
            courses = courses.order_by(F(order))
    
    # Pass the courses to the template
    context = {'courses': courses, 'lecturers': lecturers, 'departments': departments}
    return render(request, 'courses.html', context)



@login_required(login_url='login')
def add_course(request):
    try:
        if request.method == 'POST':
            course_department = request.POST.get('course_department')
            course_code = request.POST.get('course_code')
            course_name = request.POST.get('course_name')
            credit_hours = request.POST.get('credit_hours')
            course_lecturer = request.POST.get('course_lecturer')
            course_level = request.POST.get('course_level')
            course_lab_lecturer = request.POST.get('course_lab_lecturer')
            course_past_lecturers = request.POST.getlist('course_past_lecturers')
            course_building = request.POST.get('course_building')
            #course_section = request.POST.get('course_section')
            course = Course.objects.create(
                course_department=Department.objects.get(id=int(course_department)) if course_department else None,
                course_code=course_code, 
                course_name=course_name, 
                credit_hours=credit_hours, 
                course_lecturer=Lecturer.objects.get(id=int(course_lecturer)) if course_lecturer else None,
                course_level=course_level, 
                course_lab_lecturer=Lecturer.objects.get(id=int(course_lab_lecturer)) if course_lab_lecturer else None,
                course_building=course_building,
                #course_section=course_section
            )
            for lecturer_id in course_past_lecturers:
                course.course_prerequisites.add(Course.objects.get(id=int(lecturer_id)))
            
            course.save()
            return redirect('courses')
    except:
        return HttpResponse('Error adding course')

@login_required(login_url='login')
def edit_course(request, course_id):
    course = Course.objects.get(id=course_id)
    if request.method == 'POST':
        course_department = request.POST.get('course_department')
        course_code = request.POST.get('course_code')
        course_name = request.POST.get('course_name')
        credit_hours = request.POST.get('credit_hours')
        course_lecturer = request.POST.get('course_lecturer')
        course_level = request.POST.get('course_level')
        course_lab_lecturer = request.POST.get('course_lab_lecturer')
        course_past_lecturers = request.POST.getlist('course_past_lecturers')
        course_building = request.POST.get('course_building')
        course_section = request.POST.get('course_section')
        course.course_department = Department.objects.get(id=int(course_department)) if course_department else None
        course.course_code = course_code
        course.course_name = course_name
        course.credit_hours = credit_hours
        course.course_lecturer = Lecturer.objects.get(id=int(course_lecturer)) if course_lecturer else None
        course.course_level = course_level
        course.course_lab_lecturer = Lecturer.objects.get(id=int(course_lab_lecturer)) if course_lab_lecturer else None
        course.course_building = course_building
        course.course_section = course_section
        course.save()
        course.course_past_lecturers.clear()
        for lecturer_id in course_past_lecturers:
            course.course_prerequisites.add(Course.objects.get(id=int(lecturer_id)))
        return redirect('courses')
    lecturers = Lecturer.objects.all()
    departments = Department.objects.all()
    return render(request, 'edit_course.html', {'course': course, 'lecturers': lecturers, 'departments': departments})


@login_required(login_url='login')
def search_course(request):
    q = request.GET.get('q')
    # filter by course name or course codeorder by alphabetical order
    courses = Course.objects.filter(Q(course_name__icontains=q) | Q(course_code__icontains=q)).order_by('course_name')
    lecturers = Lecturer.objects.all()
    departments = Department.objects.all()
    return render(request, 'courses.html', {'courses': courses, 'lecturers': lecturers, 'departments': departments})
    



########## LECTURERS ##########
@login_required(login_url='login')
def lecturers(request):
    lecturers = Lecturer.objects.all().order_by('lecturer_name')
    courses = Course.objects.all()
    departments = Department.objects.all()
    
    lecturer_users = []
    for lecturer in lecturers:
        lecturer_users.append(lecturer.lecturer_user)
    # username not in
    users = User.objects.filter(~Q(username__in=lecturer_users))
    # exclude the superuser
    users = users.exclude(is_superuser=True)
    return render(request, 'lecturers.html', {'lecturers': lecturers, 'courses': courses, 'departments': departments, 'users': users})


from django.contrib.auth.models import User

@login_required(login_url='login')
def add_lecturer(request):
    if request.method == 'POST':
        lecturer_department = request.POST.get('lecturer_department')
        lecturer_name = request.POST.get('lecturer_name')
        lecturer_email = request.POST.get('lecturer_email')
        lecturer_phone = request.POST.get('lecturer_phone')
        lecturer_gender = request.POST.get('lecturer_gender')
        lecturer_past_courses = request.POST.getlist('lecturer_past_courses')
        
        # Create a new User account
        username = lecturer_email.split('@')[0]  # Use the part before '@' as the username
        password = '12345678'  # Set a default password for the account
        user = User.objects.create_user(username=username, password=password)
        
        # Create a new Lecturer instance
        lecturer = Lecturer.objects.create(
            lecturer_user=user,
            lecturer_department=Department.objects.get(id=int(lecturer_department)) if lecturer_department else None,
            lecturer_name=lecturer_name,
            lecturer_email=lecturer_email,
            lecturer_number=lecturer_phone,
            lecturer_gender=lecturer_gender,
        )
        
        for course_id in lecturer_past_courses:
            lecturer.lecturer_past_courses.add(Course.objects.get(id=int(course_id)))
        
        return redirect('lecturers')



@login_required(login_url='login')
def edit_lecturer(request, lecturer_id):
    lecturer = Lecturer.objects.get(id=lecturer_id)
    if request.method == 'POST':
        #lecturer_user = request.POST.get('lecturer_user')
        lecturer_department = request.POST.get('lecturer_department')
        lecturer_name = request.POST.get('lecturer_name')
        lecturer_email = request.POST.get('lecturer_email')
        lecturer_phone = request.POST.get('lecturer_phone')
        lecturer_gender = request.POST.get('lecturer_gender')
        #lecturer_type = request.POST.get('lecturer_type')
        lecturer_past_courses = request.POST.getlist('lecturer_past_courses')
        #lecturer.lecturer_user = User.objects.get(id=int(lecturer_user)) if lecturer_user else None
        lecturer.lecturer_department = Department.objects.get(id=int(lecturer_department)) if lecturer_department else None
        lecturer.lecturer_name = lecturer_name
        lecturer.lecturer_email = lecturer_email
        lecturer.lecturer_number = lecturer_phone
        lecturer.lecturer_gender = lecturer_gender
        #lecturer.lecturer_type = lecturer_type
        lecturer.save()
        lecturer.lecturer_past_courses.clear()
        
        for course_id in lecturer_past_courses:
            lecturer.lecturer_past_courses.add(Course.objects.get(id=int(course_id)))
        return redirect('lecturers')
    courses = Course.objects.all()
    departments = Department.objects.all()
    users = User.objects.filter(groups__name='Lecturers')
    return render(request, 'edit_lecturer.html', {'lecturer': lecturer, 'courses': courses, 'departments': departments, 'users': users})


@login_required(login_url='login')
def lecturer_view(request):
    try:
        lecturer = Lecturer.objects.get(lecturer_user=request.user)
        # filter by course lecturer or course lab lecturer
        courses = Course.objects.filter(Q(course_lecturer=lecturer) | Q(course_lab_lecturer=lecturer)).order_by('course_name')
        similar_lecturers = Lecturer.objects.filter(lecturer_past_courses__in=courses).exclude(id=lecturer.id).distinct()
        return render(request, 'lecturer_view.html', {'lecturer': lecturer, 'courses': courses, 'similar_lecturers': similar_lecturers})
    except:
        return render(request, 'not_a_lecturer.html')


@login_required(login_url='login')
def search_lecturer(request):
    q = request.GET.get('q')
    # filter by lecturer name or lecturer email or lecturer number
    lecturers = Lecturer.objects.filter(lecturer_name__icontains=q).order_by('lecturer_name')
    courses = Course.objects.all()
    departments = Department.objects.all()
    # users whose are in lecturers group
    users = User.objects.filter(groups__name='Lecturers')
    return render(request, 'lecturers.html', {'lecturers': lecturers, 'courses': courses, 'departments': departments, 'users': users})


########## Add Lexturer to Course ##########
@login_required(login_url='login')
def add_lecturer_to_course(request, course_id):
    if request.method == 'POST':
        lecturer_id = request.POST.get('lecturer')
        lecturer_type = request.POST.get('lecturer_type')
        section = request.POST.get('section')
        day = request.POST.get('day')
        time = request.POST.get('time')
        course = Course.objects.get(id=course_id)
        lecturer = Lecturer.objects.get(id=lecturer_id)
        # if lecturers all courses has this time, then return error
        if lecturer.lecturer_past_courses.filter(course_time=time).exists() and lecturer.lecturer_past_courses.filter(course_time=time).first() != course:
            messages.error(request, 'This lecturer has a course at this time')
            return redirect('esnad')
        course.course_section = section
        course.course_day = day
        course.course_time = time
        if lecturer_type == 'L':
            course.course_lab_lecturer = lecturer
            course.course_lecturer = None
            course_type = 'Laboratory'
        else:
            course.course_lecturer = lecturer
            course.course_lab_lecturer = None
            course_type = 'Theory'
        course.course_past_lecturers.add(lecturer)
        course.save()
        lecturer.lecturer_past_courses.add(course)

        past_lec = Lecturer.objects.filter(lecturer_past_courses__in=[course]).exclude(id=lecturer.id).distinct()
        teachers = []
        for lec in past_lec:
            teachers.append(f'{lec.lecturer_name} (email: {lec.lecturer_email}, phone: {lec.lecturer_number}), ')

        if len(teachers) == 0:
            teachers.append('No teachers')

        subject = 'You have been aseigned a course'
        body = f'Hello {lecturer.lecturer_name},\n\nYou have been aseigned the course {course.course_name} for this semester.\n\n \
        Course: {course.course_name}\n \
        Course Code: {course.course_code}\n \
        Course type: {course_type}\n \
        Section: {section}\n \
        Time: {time}\n \
        Teachers: {f" ".join(teachers)}\n \
        '
        # send_mail(
        #     subject, 
        #     body, 
        #     settings.EMAIL_HOST_USER,
        #     [lecturer.lecturer_email],
        #     fail_silently=False
        # )
        messages.success(request, f'{lecturer.lecturer_name} has been added to {course.course_name}')


        return redirect('esnad')



########## EXAM ##########
@login_required(login_url='login')
def exam_dates(request):
    courses = Course.objects.all()
    exam_dates = ExamSchedule.objects.all()
    exam_dates_json = []
    for exam_date in exam_dates:
        exam_dates_json.append({
            'title': exam_date.exam_type + ' \n' + exam_date.course.course_name,
            'start': exam_date.exam_date.strftime('%Y-%m-%d') + 'T' + exam_date.start_time.strftime('%H:%M:%S'),
            'url': '/confirm-delete-exam/' + str(exam_date.id)
        })
    return render(request, 'exam_dates.html', {'courses': courses, 'exam_dates': exam_dates_json})

@login_required(login_url='login')
def add_exam(request):
    if request.method == 'POST':
        courses = request.POST.getlist('courses')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        courses = Course.objects.filter(id__in=courses)
        exam_dates = []
        exam_hours = []
        # add the days to exam_dates list between start_date and end_date
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        delta = end_date - start_date
        for i in range(delta.days + 1):
            # check if the day is a weekend (friday or saturday)
            if (start_date + datetime.timedelta(days=i)).weekday() not in [4, 5]:
                exam_dates.append(start_date + datetime.timedelta(days=i))

        # add the hours to exam_hours list between start_time and end_time
        start_time = datetime.datetime.strptime(start_time, '%H:%M')
        end_time = datetime.datetime.strptime(end_time, '%H:%M')
        delta = end_time - start_time
        for i in range(delta.seconds // 3600 + 1):
            exam_hours.append(start_time + datetime.timedelta(hours=i))

        courses_len = len(courses)
        exam_dates_len = len(exam_dates)

        exams_gradually = exam_dates_len / courses_len
        
        # Assign exams to courses
        first_exam_date_and_time = exam_dates[0].strftime('%Y-%m-%d') + 'T' + exam_hours[0].strftime('%H:%M:%S')
        exam_assigned_at_with_time = [first_exam_date_and_time]

        exam_assigned_at = [exam_dates[0]]
        add_index = 1 if exams_gradually < 1 else int(exams_gradually)
        add_index_fraction = exams_gradually - add_index
        add_index_fraction_backup = add_index_fraction
        fraction_added = False

        for course in courses[1:]:
            # calculate the next add_index
            add_index_fraction = add_index_fraction + add_index_fraction_backup
            if not fraction_added:
                if add_index_fraction >= 1:
                    add_index = add_index + 1
                    add_index_fraction = add_index_fraction - 1
                    fraction_added = True
            else:
                add_index -= 1
                fraction_added = False


            # check if course is last course in the list
            if course == courses[courses_len - 1]:
                last_index = exam_dates_len - 1
                next_exam_date = exam_dates[last_index]
                exam_assigned_at.append(next_exam_date)
            else:
                last_exam_date = exam_assigned_at[-1]
                last_exam_date_index = exam_dates.index(last_exam_date)
                next_exam_date_index = last_exam_date_index + add_index if last_exam_date_index + add_index < exam_dates_len else 0
                next_exam_date = exam_dates[next_exam_date_index]
                exam_assigned_at.append(next_exam_date)

            next_exam_time = exam_hours[0]
            next_exam_date_and_time = next_exam_date.strftime('%Y-%m-%d') + 'T' + next_exam_time.strftime('%H:%M:%S')
            
            while next_exam_date_and_time in exam_assigned_at_with_time:
                # add 4 hours to next_exam_date_and_time
                next_exam_time = next_exam_time + datetime.timedelta(hours=4)
                next_exam_date_and_time = next_exam_date.strftime('%Y-%m-%d') + 'T' + next_exam_time.strftime('%H:%M:%S')
            exam_assigned_at_with_time.append(next_exam_date_and_time)

            # Assign exams to courses

        #print(exam_assigned_at)
        print(exam_assigned_at_with_time)

        # Assign exams to courses
        for date_time in exam_assigned_at_with_time:
            course = courses[exam_assigned_at_with_time.index(date_time)]
            if not ExamSchedule.objects.filter(course=course, exam_type='Final').exists():
                exam_schedule = ExamSchedule.objects.create(
                    course=course,
                    exam_date=date_time.split('T')[0],
                    start_time=date_time.split('T')[1],
                )
                exam_schedule.save()
            else:
                messages.error(request, 'Exam already exists for ' + course.course_name + ' course')
            
            
        return redirect('exam_dates')


@login_required(login_url='login')
def add_exam_single(request):
    if request.method == 'POST':
        course = request.POST.get('course')
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time')

        course = Course.objects.get(id=course)
        if not ExamSchedule.objects.filter(course=course, exam_type='Final').exists():
            exam_schedule = ExamSchedule.objects.create(
                course=course,
                exam_date=start_date,
                start_time=start_time,
            )
            exam_schedule.save()
        else:
            messages.error(request, 'Exam already exists for ' + course.course_name + ' course')
        return redirect('exam_dates')


@login_required(login_url='login')
def add_quiz_exam(request):
    if request.method == 'POST':
        course = request.POST.get('course')
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time')

        course = Course.objects.get(id=course)
        if ExamSchedule.objects.filter(course=course, exam_type='Quiz').exists():
            messages.error(request, 'Quiz exam already exists for ' + course.course_name + ' course')
            return redirect('exam_dates')
        exam_schedule = ExamSchedule.objects.create(
            course=course,
            exam_date=start_date,
            start_time=start_time,
            exam_type='Quiz'
        )
        exam_schedule.save()
        return redirect('exam_dates')


@login_required(login_url='login')
def add_midterm_exam(request):
    if request.method == 'POST':
        courses = request.POST.getlist('courses')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        courses = Course.objects.filter(id__in=courses)
        exam_dates = []
        exam_hours = []
        # add the days to exam_dates list between start_date and end_date
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        delta = end_date - start_date
        for i in range(delta.days + 1):
            # check if the day is a weekend (friday or saturday)
            if (start_date + datetime.timedelta(days=i)).weekday() not in [4, 5]:
                exam_dates.append(start_date + datetime.timedelta(days=i))

        # add the hours to exam_hours list between start_time and end_time
        start_time = datetime.datetime.strptime(start_time, '%H:%M')
        end_time = datetime.datetime.strptime(end_time, '%H:%M')
        delta = end_time - start_time
        for i in range(delta.seconds // 3600 + 1):
            exam_hours.append(start_time + datetime.timedelta(hours=i))

        courses_len = len(courses)
        exam_dates_len = len(exam_dates)

        exams_gradually = exam_dates_len / courses_len
        
        # Assign exams to courses
        first_exam_date_and_time = exam_dates[0].strftime('%Y-%m-%d') + 'T' + exam_hours[0].strftime('%H:%M:%S')
        exam_assigned_at_with_time = [first_exam_date_and_time]

        exam_assigned_at = [exam_dates[0]]
        add_index = 1 if exams_gradually < 1 else int(exams_gradually)
        add_index_fraction = exams_gradually - add_index
        add_index_fraction_backup = add_index_fraction
        fraction_added = False

        for course in courses[1:]:
            # calculate the next add_index
            add_index_fraction = add_index_fraction + add_index_fraction_backup
            if not fraction_added:
                if add_index_fraction >= 1:
                    add_index = add_index + 1
                    add_index_fraction = add_index_fraction - 1
                    fraction_added = True
            else:
                add_index -= 1
                fraction_added = False


            # check if course is last course in the list
            if course == courses[courses_len - 1]:
                last_index = exam_dates_len - 1
                next_exam_date = exam_dates[last_index]
                exam_assigned_at.append(next_exam_date)
            else:
                last_exam_date = exam_assigned_at[-1]
                last_exam_date_index = exam_dates.index(last_exam_date)
                next_exam_date_index = last_exam_date_index + add_index if last_exam_date_index + add_index < exam_dates_len else 0
                next_exam_date = exam_dates[next_exam_date_index]
                exam_assigned_at.append(next_exam_date)

            next_exam_time = exam_hours[0]
            next_exam_date_and_time = next_exam_date.strftime('%Y-%m-%d') + 'T' + next_exam_time.strftime('%H:%M:%S')
            
            while next_exam_date_and_time in exam_assigned_at_with_time:
                # add 4 hours to next_exam_date_and_time
                next_exam_time = next_exam_time + datetime.timedelta(hours=4)
                next_exam_date_and_time = next_exam_date.strftime('%Y-%m-%d') + 'T' + next_exam_time.strftime('%H:%M:%S')
            exam_assigned_at_with_time.append(next_exam_date_and_time)

            # Assign exams to courses

        #print(exam_assigned_at)
        print(exam_assigned_at_with_time)

        # Assign exams to courses
        for date_time in exam_assigned_at_with_time:
            course = courses[exam_assigned_at_with_time.index(date_time)]
            if not ExamSchedule.objects.filter(course=course, exam_type='Midterm').exists():
                exam_schedule = ExamSchedule.objects.create(
                    course=course,
                    exam_date=date_time.split('T')[0],
                    start_time=date_time.split('T')[1],
                    exam_type='Midterm'
                )
                exam_schedule.save()
            else:
                messages.error(request, 'You can not add midterm exams. There are midterm exams already added.')
            
            
        return redirect('exam_dates')





@login_required(login_url='login')
def delete_exam(request, exam_id):
    exam_schedule = ExamSchedule.objects.get(id=exam_id)
    exam_schedule.delete()
    return redirect('exam_dates')


@login_required(login_url='login')
def confirm_delete_exam(request, exam_id):
    exam = ExamSchedule.objects.get(id=exam_id)
    user = request.user
    if exam.exam_type == 'Final' and request.user.groups.filter(name='Coordinators').exists():
        messages.error(request, 'You can not change this exam date.')
        return redirect('exam_dates')
    courses = Course.objects.all()
    return render(request, 'confirm_delete_exam.html', {'exam_id': exam_id, 'exam': exam, 'courses': courses})


@login_required(login_url='login')
def edit_exam(request, exam_id):
    if request.method == 'POST':
        course = request.POST.get('course')
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time')

        exam_schedule = ExamSchedule.objects.get(id=exam_id)
        exam_schedule.course = Course.objects.get(id=course)
        exam_schedule.exam_date = start_date
        exam_schedule.start_time = start_time
        exam_schedule.save()
        return redirect('exam_dates')



########## Profile ##########
@login_required(login_url='login')
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email_address = request.POST.get('email')
        password = request.POST.get('password')
        
        user.first_name = first_name
        user.last_name = last_name
        user.email = email_address
        if password != '':
            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters')
                return redirect('edit_profile')
            user.set_password(password)
        user.save()
        return redirect('edit_profile')
    return render(request, 'edit_profile.html', {'user': user})





@csrf_exempt
def add_event(request):
    if request.method == 'POST':
        title = request.POST.get('event_title')
        start_date = request.POST.get('event_start')
        # Convert start_date to datetime object if necessary
        event = Event.objects.create(title=title, start=start_date)
        return JsonResponse({'event_id': event.id})

@csrf_exempt
def update_event(request):
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        title = request.POST.get('event_title')
        event = Event.objects.get(id=event_id)
        event.title = title
        event.save()
        return JsonResponse({})

@csrf_exempt
def delete_event(request):
    if request.method == 'POST':
        event_id = request.POST.get('event_id')
        event = Event.objects.get(id=event_id)
        event.delete()
        return JsonResponse({})
    


def assign_lecturer(request):
    if request.method == 'POST':
        lecturer_id = request.POST.get('lecturer_id')
        course_code = request.POST.get('course_code')
        
        lecturer = Lecturer.objects.get(id=lecturer_id)
        course = Course.objects.get(course_code=course_code)  # Get course by its code

        # Check for time conflicts
        if not Lecturer.objects.filter(courses__time=course.time).exists():
            # No conflicts, assign lecturer to course
            lecturer.courses.add(course)
            lecturer.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Time conflict'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required(login_url='login')
def esnad(request):
    lecturers = Lecturer.objects.all()
    courses = Course.objects.all()
    return render(request, 'esnad.html', {'lecturers': lecturers, 'courses': courses})



@login_required(login_url='login')
def assigned_courses(request):
    # get the courses that course_lecturer or course_lab_lecturer not null
    courses = Course.objects.filter(Q(course_lecturer__isnull=False) | Q(course_lab_lecturer__isnull=False))
    all_lecturers = []
    for course in courses:
        if course.course_lecturer:
            if course.course_lecturer not in all_lecturers:
                all_lecturers.append(course.course_lecturer)
        if course.course_lab_lecturer:
            if course.course_lab_lecturer not in all_lecturers:
                all_lecturers.append(course.course_lab_lecturer)

    return render(request, 'assigned_courses.html', {'courses': courses, 'lecturers': all_lecturers})



def automate_esnad(request):
    # remove all lecturers from course
    courses = Course.objects.all()
    if len(courses) > 45:
        messages.error(request, 'There are more than 45 courses, please delete some courses')
        return redirect('esnad')
    for course in courses:
        course.course_lecturer = None
        course.course_lab_lecturer = None
        course.course_section = ''
        course.course_time = None
        course.save()


    b_sections = [271, 272, 273]
    g_sections = [171, 172, 173]
    teaching_hours = []
    # teaching hours will be sunday to thursday from 8 to 3 except 12 to 1:30
    # example item: {'day': 'Sunday', 'time': '8:00 - 10:00'}
    for hour in range(8, 15, 2):
        for day in range(1, 6):
            if hour == 12:
                continue
            teaching_hours.append({'day': day, 'time': f'{hour}:00 - {hour+2}:00'})

    #print(teaching_hours)
    teaching_hours_with_b_sections = []
    for section in b_sections:
        for hour in teaching_hours:
            teaching_hours_with_b_sections.append({'day': hour['day'], 'time': hour['time'], 'section': section})

    teaching_hours_with_g_sections = []
    for section in g_sections:
        for hour in teaching_hours:
            teaching_hours_with_g_sections.append({'day': hour['day'], 'time': hour['time'], 'section': section})

    # print(teaching_hours_with_b_sections)
    # print(teaching_hours_with_g_sections)


    def get_available_lecturers(course, booked_lecturers):
        #lecturer.lecturer_past_courses.all()
        # get the lecturers that teach this course before
        previous_lecturers = Lecturer.objects.filter(lecturer_past_courses__course_code=course.course_code)
        for lecturer in previous_lecturers:
            if lecturer not in booked_lecturers:
                return lecturer
            
        lecturers = Lecturer.objects.all()
        for lecturer in lecturers:
            gender = lecturer.lecturer_gender
            if gender == 'F' and course.course_building == 'B':
                continue
            if lecturer not in booked_lecturers:
                return lecturer
            
        return None


    booked_lecturers = []
    for course in courses:
        lecturer = get_available_lecturers(course, booked_lecturers)
        while lecturer is None:
            booked_lecturers = []
            lecturer = get_available_lecturers(course, booked_lecturers)
        booked_lecturers.append(lecturer)

        course_building = course.course_building
        if course_building == 'B':
            section = teaching_hours_with_b_sections[0]
            teaching_hours_with_b_sections.remove(section)
            course.course_section = section['section']
            start_time = section['time'].split(' - ')[0]
            start_time = datetime.datetime.strptime(start_time, '%H:%M')
            course.course_time = start_time
            course.course_day = section['day']
            course.course_lecturer = lecturer
            course.save()
        elif course_building == 'A':
            section = teaching_hours_with_g_sections[0]
            teaching_hours_with_g_sections.remove(section)
            course.course_section = section['section']
            start_time = section['time'].split(' - ')[0]
            start_time = datetime.datetime.strptime(start_time, '%H:%M')
            course.course_time = start_time
            course.course_day = section['day']
            course.course_lecturer = lecturer
            course.save()
            





    return redirect('esnad')


def duplicate_courses(request):
    courses = Course.objects.all()
    for course in courses:
        building = course.course_building
        if building == 'B':
            if not Course.objects.filter(course_code=course.course_code, course_name=course.course_name, course_building='A').exists():
                c = Course.objects.create(
                    course_code=course.course_code, 
                    course_name=course.course_name, 
                    course_building='A',
                    credit_hours=course.credit_hours,
                    course_level=course.course_level,
                    course_department=course.course_department,
                )
                course_prerequisites = course.course_prerequisites.all()
                for prerequisite in course_prerequisites:
                    c.course_prerequisites.add(prerequisite)
                c.save()
        elif building == 'A':
            if not Course.objects.filter(course_code=course.course_code, course_name=course.course_name, course_building='B').exists():
                c = Course.objects.create(
                    course_code=course.course_code, 
                    course_name=course.course_name, 
                    course_building='B',
                    credit_hours=course.credit_hours,
                    course_level=course.course_level,
                    course_department=course.course_department,
                )
                course_prerequisites = course.course_prerequisites.all()
                for prerequisite in course_prerequisites:
                    c.course_prerequisites.add(prerequisite)
                c.save()
    return redirect('courses')