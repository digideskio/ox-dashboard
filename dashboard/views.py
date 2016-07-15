from django.contrib import auth, messages
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import *

import utils
from .forms import *


class LoginView(View):
    """ Logs in and redirects to the homepage """

    def post(self, request, *args, **kwargs):
        user = auth.authenticate(
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user is not None:
            if user.is_active:
                auth.login(request, user)
        return HttpResponseRedirect(reverse('dashboard:home'))

    def get(self, request, *args, **kwargs):
        # we should never get to this code path
        return HttpResponseRedirect(reverse('dashboard:home'))


class LogoutView(View):
    """ Logout and redirect to homepage """

    def get(self, request, *args, **kwargs):
        auth.logout(request)
        return HttpResponseRedirect(reverse('dashboard:home'))


def home(request):
    """ Renders home page """
    context = {
    }
    return render(request, 'home.html', context)


def brother_view(request):
    """ Renders the brother page of current user showing all standard brother information """
    if not request.user.is_authenticated():  # brother auth check
        messages.error(request, "Brother not logged in before viewing brother portal")
        return HttpResponseRedirect(reverse('dashboard:home'))
    print Brother.objects.all()
    brother = Brother.objects.filter(user=request.user)[0]
    chapter_events = ChapterEvent.objects.filter(semester__season=utils.get_season(),
                                                 semester__year=utils.get_year()).order_by("date")
    excuses_pending = Excuse.objects.filter(brother=brother, event__semester__season=utils.get_season(),
                                            event__semester__year=utils.get_year(), status='0').order_by("event__date")
    excuses_approved = Excuse.objects.filter(brother=brother, event__semester__season=utils.get_season(),
                                             event__semester__year=utils.get_year(), status='1').order_by("event__date")
    excuses_denied = Excuse.objects.filter(brother=brother, event__semester__season=utils.get_season(),
                                           event__semester__year=utils.get_year(), status='2').order_by("event__date")
    excuses_not_mandatory = Excuse.objects.filter(brother=brother, event__semester__season=utils.get_season(),
                                                  event__semester__year=utils.get_year(), status='3').order_by(
        "event__date")
    # TODO: write util function to covert standing/operational committee # to standard #
    # committee_meetings = CommitteeMeetingEvent.objects.filter()
    current_season = utils.get_season()
    if current_season is '0':
        recruitment_events = RecruitmentEvent.objects.filter(semester__season='0', semester__year=utils.get_year()) \
            .order_by("date")
        recruitment_events_next = RecruitmentEvent.objects.filter(semester__season='2', semester__year=utils.get_year()) \
            .order_by("date")
    else:
        recruitment_events = RecruitmentEvent.objects.filter(semester__season='2', semester__year=utils.get_year()) \
            .order_by("date")
        recruitment_events_next = RecruitmentEvent.objects.filter(semester__season='0', semester__year=utils.get_year()) \
            .order_by("date")
    pnms = PotentialNewMember.objects.filter(Q(primary_contact=brother) |
                                             Q(secondary_contact=brother) |
                                             Q(tertiary_contact=brother)).order_by("last_name")
    service_events = ServiceEvent.objects.filter(semester__season=utils.get_season(),
                                                 semester__year=utils.get_year()).order_by("date")
    # Service submissions
    approved_hours = 0  # TODO count approved hours
    submissions_pending = ServiceSubmission.objects.filter(brother=brother, semester__season=utils.get_season(),
                                                           semester__year=utils.get_year(), status='0').order_by("date")
    submissions_submitted = ServiceSubmission.objects.filter(brother=brother, semester__season=utils.get_season(),
                                                             semester__year=utils.get_year(), status='1').order_by(
        "date")
    submissions_approved = ServiceSubmission.objects.filter(brother=brother, semester__season=utils.get_season(),
                                                            semester__year=utils.get_year(), status='2').order_by(
        "date")
    submissions_denied = ServiceSubmission.objects.filter(brother=brother, semester__season=utils.get_season(),
                                                          semester__year=utils.get_year(), status='3').order_by(
        "date")

    hours_pending = 0
    for submission in submissions_pending:
        hours_pending += submission.hours
    for submission in submissions_submitted:
        hours_pending += submission.hours

    hours_approved = 0
    for submission in submissions_approved:
        hours_approved += submission.hours

    philanthropy_events = PhilanthropyEvent.objects.filter(semester__season=utils.get_season(),
                                                           semester__year=utils.get_year()) \
        .order_by("start_time").order_by("date")

    context = {
        'brother': brother,
        'chapter_events': chapter_events,
        'excuses_pending': excuses_pending,
        'excuses_approved': excuses_approved,
        'excuses_denied': excuses_denied,
        'excuses_not_mandatory': excuses_not_mandatory,
        # 'committee_meetings': committee_meetings,
        'recruitment_events': recruitment_events,
        'recruitment_events_next': recruitment_events_next,
        'pnms': pnms,
        'service_events': service_events,
        'approved_hours': approved_hours,
        'submissions_pending': submissions_pending,
        'submissions_submitted': submissions_submitted,
        'submissions_approved': submissions_approved,
        'submissions_denied': submissions_denied,
        'philanthropy_events': philanthropy_events,
        'hours_approved': hours_approved,
        'hours_pending': hours_pending,
    }
    return render(request, "brother.html", context)


def brother_chapter_event(request, event_id):
    """ Renders the brother page for chapter event with a excuse form """
    if not request.user.is_authenticated():  # brother auth check
        messages.error(request, "Brother not logged in before viewing brother chapter events")
        return HttpResponseRedirect(reverse('dashboard:home'))

    event = ChapterEvent.objects.get(pk=event_id)
    form = ExcuseForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            instance = form.save(commit=False)
            if instance.description == "I will not be attending because":
                context = {
                    'type': 'brother-view',
                    'form': form,
                    'event': event,
                    'error_message': "Please write a description",
                }
                return render(request, "chapter-event.html", context)
            brother = Brother.objects.filter(user=request.user)[0]
            instance.brother = brother
            instance.event = event
            instance.save()
            return HttpResponseRedirect(reverse('dashboard:brother'))

    context = {
        'type': 'brother-view',
        'form': form,
        'event': event,
    }
    return render(request, "chapter-event.html", context)


def brother_service_event(request, event_id):
    """ Renders the brother page for service event with a excuse form """
    if not request.user.is_authenticated():  # brother auth check
        messages.error(request, "Brother not logged in before viewing brother chapter events")
        return HttpResponseRedirect(reverse('dashboard:home'))

    brother = Brother.objects.filter(user=request.user)[0]
    event = ServiceEvent.objects.get(pk=event_id)
    brothers_rsvp = event.rsvp_brothers.all()
    rsvp_brother = event.rsvp_brothers.filter(id=brother.id)

    if request.method == 'POST':
        if rsvp_brother.exists():
            event.rsvp_brothers.remove(brother)
        else:
            event.rsvp_brothers.add(brother)
        event.save()
        return HttpResponseRedirect(reverse('dashboard:brother'))

    context = {
        'type': 'brother-view',
        'brothers_rsvp': brothers_rsvp,
        'rsvpd': rsvp_brother.exists(),
        'event': event,
    }

    return render(request, "service-event.html", context)


def brother_philanthropy_event(request, event_id):
    """ Renders the brother page for service event with a excuse form """
    if not request.user.is_authenticated():  # brother auth check
        messages.error(request, "Brother not logged in before viewing brother chapter events")
        return HttpResponseRedirect(reverse('dashboard:home'))

    brother = Brother.objects.filter(user=request.user)[0]
    event = PhilanthropyEvent.objects.get(pk=event_id)
    brothers_rsvp = event.rsvp_brothers.all()
    rsvp_brother = event.rsvp_brothers.filter(id=brother.id)

    if request.method == 'POST':
        if rsvp_brother.exists():
            event.rsvp_brothers.remove(brother)
        else:
            event.rsvp_brothers.add(brother)
        event.save()
        return HttpResponseRedirect(reverse('dashboard:brother'))

    context = {
        'type': 'brother-view',
        'brothers_rsvp': brothers_rsvp,
        'rsvpd': rsvp_brother.exists(),
        'event': event,
    }

    return render(request, "philanthropy-event.html", context)


def brother_recruitment_event(request, event_id):
    """ Renders the brother page for recruitment event with a excuse form """
    if not request.user.is_authenticated():  # brother auth check
        messages.error(request, "Brother not logged in before viewing brother chapter events")
        return HttpResponseRedirect(reverse('dashboard:home'))

    event = RecruitmentEvent.objects.get(pk=event_id)
    attendees_pnms = event.attendees_pnms.all()

    context = {
        'type': 'brother-view',
        'attendees_pnms': attendees_pnms,
        'event': event,
    }
    return render(request, "recruitment-event.html", context)


def brother_excuse(request, excuse_id):
    """ Renders the brother page for one of their excuses """
    excuse = Excuse.objects.get(pk=excuse_id)
    if not request.user == excuse.brother.user:  # brother auth check
        messages.error(request, "Please log into the brother that submitted that excuse")
        return HttpResponseRedirect(reverse('dashboard:home'))

    context = {
        'excuse': excuse,
        'type': 'review',
    }
    return render(request, "excuse.html", context)


class ExcuseDelete(DeleteView):
    # TODO: verify brother with excuse
    model = Excuse
    success_url = reverse_lazy('dashboard:brother')


class ExcuseEdit(UpdateView):
    model = Excuse
    success_url = reverse_lazy('dashboard:brother')
    fields = ['description']


class BrotherEdit(UpdateView):
    model = Brother
    success_url = reverse_lazy('dashboard:brother')
    fields = ['first_name', 'last_name', 'roster_number', 'semester_joined', 'school_status', 'brother_status',
              'major', 'minor', 't_shirt_size', 'case_ID', 'birthday', 'hometown', 'phone_number',
              'emergency_contact_phone_number', 'emergency_contact', 'room_number',
              'address']


def brother_pnm(request, pnm_id):
    """ Renders the pnm page for brothers """
    # TODO:
    if not request.user.is_authenticated:  # brother auth check
        messages.error(request, "Please log in to view pnms")
        return HttpResponseRedirect(reverse('dashboard:home'))

    pnm = PotentialNewMember.objects.get(pk=pnm_id)
    events = RecruitmentEvent.objects.filter(semester__season=utils.get_season(),
                                             semester__year=utils.get_year()).order_by("date").all()

    print events
    attended_events = []
    for event in events:
        if event.attendees_pnms.filter(id=pnm_id).exists():
            attended_events.append(event)

    context = {
        'type': 'brother-view',
        'pnm': pnm,
        'events': attended_events,
    }
    return render(request, 'potential_new_member.html', context)


def brother_service_submission(request, submission_id):
    """ Renders the Brother page for viewing a service submission"""
    if not request.user.is_authenticated():  # brother auth check
        messages.error(request, "Brother not logged in before adding service hours")
        return HttpResponseRedirect(reverse('dashboard:home'))

    submission = ServiceSubmission.objects.get(pk=submission_id)

    context = {
        'type': 'review',
        'submission': submission,
    }

    return render(request, 'service-submission.html', context)


def brother_service_submission_add(request):
    """ Renders the Brother page for adding a service submission"""
    if not request.user.is_authenticated():  # brother auth check
        messages.error(request, "Brother not logged in before adding service hours")
        return HttpResponseRedirect(reverse('dashboard:home'))

    form = ServiceSubmissionForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            instance = form.save(commit=False)

            try:
                semester = Semester.objects.filter(season=utils.get_season_from(instance.date.month),
                                                   year=instance.date.year)[0]
            except IndexError:
                semester = Semester(season=utils.get_season_from(instance.date.month),
                                    year=instance.date.year)
                semester.save()

            brother = Brother.objects.filter(user=request.user)[0]
            instance.brother = brother
            instance.semester = semester
            instance.save()
            return HttpResponseRedirect(reverse('dashboard:brother'))

    context = {
        'title': 'Submit Service Hours',
        'form': form,
    }
    return render(request, 'model-add.html', context)


class ServiceSubmissionDelete(DeleteView):
    # TODO: verify brother with submission
    model = ServiceSubmission
    success_url = reverse_lazy('dashboard:brother')


class ServiceSubmissionEdit(UpdateView):
    model = ServiceSubmission
    success_url = reverse_lazy('dashboard:brother')
    fields = ['name', 'date', 'description', 'hours', 'status']


def president(request):
    """ Renders the President page and all relevant information """
    # TODO: verify that user is President
    return render(request, 'president.html', {})


def vice_president(request):
    """ Renders the Vice President page and all relevant information, primarily committee related """
    # TODO: verify that user is Vice President
    return render(request, 'vice-president.html', {})


def treasurer(request):
    """ Renders all the transactional information on the site for the treasurer """
    # TODO: verify that user is Treasurer
    return render(request, 'treasurer.html', {})


def secretary(request):
    """ Renders the secretary page giving access to excuses and ChapterEvents """
    # TODO: verify that user is Secretary
    excuses = Excuse.objects.filter(event__semester__season=utils.get_season(),
                                    event__semester__year=utils.get_year(),
                                    status='0').order_by("event__date")
    events = ChapterEvent.objects.filter(semester__season=utils.get_season(),
                                         semester__year=utils.get_year()).order_by("date")
    context = {
        'excuses': excuses,
        'events': events,
    }
    return render(request, 'secretary.html', context)


def secretary_attendance(request):
    """ Renders the secretary view for chapter attendance """
    brothers = Brother.objects.exclude(brother_status='2').order_by("last_name")
    events = ChapterEvent.objects.filter(semester__season=utils.get_season(), semester__year=utils.get_year())
    excuses = Excuse.objects.filter(event__semester__season=utils.get_season(),
                                    event__semester__year=utils.get_year(), status='1')
    events_excused_list = []
    events_unexcused_list = []

    for brother in brothers:
        events_excused = 0
        events_unexcused = 0
        for event in events:
            if not event.attendees.filter(id=brother.id).exists():
                if excuses.filter(brother=brother, event=event).exists():
                    events_excused += 1
                else:
                    events_unexcused += 1
        events_excused_list.append(events_excused)
        events_unexcused_list.append(events_unexcused)

    brother_attendance = zip(brothers, events_excused_list, events_unexcused_list)

    context = {
        'brother_attendance': brother_attendance,
    }

    return render(request, 'chapter-event-attendance.html', context)


def secretary_event(request, event_id):
    """ Renders the attendance sheet for any event """
    # TODO: verify that user is Secretary (add a file with secretary verify function)
    event = ChapterEvent.objects.get(pk=event_id)
    brothers = Brother.objects.exclude(brother_status='2')
    form_list = []
    for brother in brothers:
        if event.attendees.filter(roster_number=brother.roster_number):
            new_form = BrotherAttendanceForm(request.POST or None, initial={'present': True},
                                             prefix=brother.roster_number,
                                             brother="- %s %s" % (brother.first_name, brother.last_name))
            form_list.append(new_form)
        else:
            new_form = BrotherAttendanceForm(request.POST or None, initial={'present': False},
                                             prefix=brother.roster_number,
                                             brother="- %s %s" % (brother.first_name, brother.last_name))
            form_list.append(new_form)

    if request.method == 'POST':
        if utils.forms_is_valid(form_list):
            for counter, form in enumerate(form_list):
                instance = form.cleaned_data
                if instance['present'] is True:
                    event.attendees.add(brothers[counter])
                    event.save()
                if instance['present'] is False:
                    event.attendees.remove(brothers[counter])
                    event.save()
            return HttpResponseRedirect(reverse('dashboard:secretary'))

    context = {
        'type': 'attendance',
        'brother_form_list': form_list,
        'event': event,
    }
    return render(request, "chapter-event.html", context)


def secretary_excuse(request, excuse_id):
    """ Renders Excuse response form """
    # TODO: verify that user is Secretary (add a file with secretary verify function)
    excuse = get_object_or_404(Excuse, pk=excuse_id)
    form = ExcuseResponseForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            instance = form.save(commit=False)
            if instance.status == '2' and instance.response_message == '':
                context = {
                    'type': 'response',
                    'excuse': excuse,
                    'form': form,
                    'error_message': "Response message required for denial"
                }
                return render(request, "excuse.html", context)
            if instance.status == '3' and excuse.event.mandatory:
                context = {
                    'type': 'response',
                    'excuse': excuse,
                    'form': form,
                    'error_message': "Event is mandatory cannot mark excuse not mandatory"
                }
                return render(request, "excuse.html", context)
            else:
                excuse.status = instance.status
                excuse.response_message = instance.response_message
                excuse.save()
                return HttpResponseRedirect(reverse('dashboard:secretary'))

    context = {
        'type': 'response',
        'excuse': excuse,
        'form': form,
    }
    return render(request, "excuse.html", context)


def secretary_all_excuses(request):
    """ Renders all excuses sorted by date then semester """
    # TODO: verify that user is Secretary (add a file with secretary verify function)
    excuses = Excuse.objects.order_by('brother__last_name').order_by('event__date')
    context = {
        'excuses': excuses,
    }
    # TODO: create secretary-excuses-all.html
    return render(request, "home.html", context)


def secretary_event_view(request, event_id):
    """ Renders the Secretary way of viewing old events """
    # TODO: verify that user is Secretary (add a file with secretary verify function)
    event = ChapterEvent.objects.get(pk=event_id)
    attendees = event.attendees.all().order_by("last_name")

    context = {
        'type': 'ec-view',
        'attendees': attendees,
        'event': event,
    }
    return render(request, "chapter-event.html", context)


def secretary_brother_list(request):
    """ Renders the Secretary way of viewing brothers """
    # TODO: verify that user is Secretary (add a file with secretary verify function)
    brothers = Brother.objects.exclude(brother_status='2')
    context = {
        'position': 'Secretary',
        'brothers': brothers
    }
    return render(request, "brother-list.html", context)


def secretary_brother_view(request, brother_id):
    """ Renders the Secretary way of viewing a brother """
    # TODO: verify that user is Secretary (add a file with secretary verify function)
    brother = Brother.objects.get(pk=brother_id)
    context = {
        'brother': brother
    }
    return render(request, "brother-view.html", context)


def secretary_brother_add(request):
    """ Renders the Secretary way of viewing a brother """
    form = BrotherForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            instance = form.cleaned_data
            if instance['password'] == instance['password2']:
                user = User.objects.create_user(instance['case_ID'], instance['case_ID'] + "@case.edu",
                                                instance['password'])
                user.last_name = instance['last_name']
                user.save()

                brother = form.save(commit=False)
                brother.user = user
                brother.save()

                return HttpResponseRedirect(reverse('dashboard:secretary_brother_list'))
            else:
                context = {
                    'error_message': "Please make sure your passwords match",
                    'title': 'Add New Brother',
                    'form': form,
                }
                return render(request, 'model-add.html', context)

    context = {
        'title': 'Add New Brother',
        'form': form,
    }
    return render(request, 'model-add.html', context)


class SecretaryBrotherEdit(UpdateView):
    model = Brother
    success_url = reverse_lazy('dashboard:secretary_brother_list')
    fields = ['first_name', 'last_name', 'roster_number', 'semester_joined', 'school_status', 'brother_status',
              'major', 'minor', 't_shirt_size', 'case_ID', 'birthday', 'hometown', 'phone_number',
              'emergency_contact_phone_number', 'emergency_contact', 'room_number',
              'address']


def secretary_event_add(request):
    """ Renders the Secretary way of adding ChapterEvents """
    # TODO: verify that user is Secretary (add a file with secretary verify function)
    form = ChapterEventForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            # TODO: add google calendar event adding
            instance = form.save(commit=False)
            try:
                semester = Semester.objects.filter(season=utils.get_season_from(instance.date.month),
                                                   year=instance.date.year)[0]
            except IndexError:
                semester = Semester(season=utils.get_season_from(instance.date.month),
                                    year=instance.date.year)
                semester.save()
            if instance.end_time is not None and instance.end_time < instance.start_time:
                context = {
                    'position': 'Secretary',
                    'form': form,
                    'error_message': "Start time after end time!",
                }
                return render(request, "event-add.html", context)
            instance.semester = semester
            instance.save()
            return HttpResponseRedirect(reverse('dashboard:secretary'))

    context = {
        'position': 'Secretary',
        'form': form,
    }
    return render(request, "event-add.html", context)


class ChapterEventEdit(UpdateView):
    model = ChapterEvent
    success_url = reverse_lazy('dashboard:secretary')
    fields = ['name', 'mandatory', 'date', 'start_time', 'end_time', 'minutes', 'notes']


class ChapterEventDelete(DeleteView):
    # TODO: verify secretary
    model = ChapterEvent
    success_url = reverse_lazy('dashboard:secretary')


def secretary_all_events(request):
    """ Renders a secretary view with all the ChapterEvent models ordered by date grouped by semester """
    # TODO: verify that user is Secretary (add a file with secretary verify function)
    events_by_semester = []
    semesters = Semester.objects.order_by("season").order_by("year").all()
    for semester in semesters:
        events = ChapterEvent.objects.filter(semester=semester).order_by("date")
        if len(events) == 0:
            events_by_semester.append([])
        else:
            events_by_semester.append(events)
    zip_list = zip(events_by_semester, semesters)
    context = {
        'list': zip_list,
        'position': "Secretary"
    }
    return render(request, "chapter-event-all.html", context)


def marshall(request):
    """ Renders the Marshall page listing all the candidates and relevant information to them """
    # TODO: verify that user is Marshall
    candidates = Brother.objects.filter(brother_status='0')
    context = {
        'candidates': candidates,
    }
    return render(request, 'marshall.html.html', context)


def scholarship_c(request):
    """ Renders the Scholarship page listing all brother gpas and study table attendance """
    # TODO: verify that user is Scholarship chair (add a file with scholarship verify function)
    reports = ScholarshipReport.objects.filter(semester__season=utils.get_season(),
                                               semester__year=utils.get_year()) \
        .order_by("past_semester_gpa")
    context = {
        'reports': reports,
    }
    return render(request, "scholarship-chair.html", context)


def recruitment_c(request):
    """ Renders Scholarship chair page with events for the current and following semester """
    # TODO: verify that user is Recruitment Chair
    current_season = utils.get_season()
    if current_season is '0':
        semester_events = RecruitmentEvent.objects.filter(semester__season='0', semester__year=utils.get_year())
        semester_events_next = RecruitmentEvent.objects.filter(semester__season='2', semester__year=utils.get_year())
    else:
        semester_events = RecruitmentEvent.objects.filter(semester__season='2', semester__year=utils.get_year())
        semester_events_next = RecruitmentEvent.objects.filter(semester__season='0', semester__year=utils.get_year())

    potential_new_members = PotentialNewMember.objects.all()

    context = {
        'events': semester_events,
        'events_future': semester_events_next,
        'potential_new_members': potential_new_members,
    }
    return render(request, 'recruitment-chair.html', context)


def recruitment_c_pnm(request, pnm_id):
    """ Renders PNM view for recruitment chair """
    # TODO: verify that user is Recruitment chair
    pnm = PotentialNewMember.objects.get(pk=pnm_id)

    context = {
        'type': 'recruitment-chair-view',
        'pnm': pnm,
    }
    return render(request, 'potential_new_member.html', context)


def recruitment_c_pnm_add(request):
    """ Renders the recruitment chair way of adding PNMs """
    # TODO: verify that user is Recruitment Chair
    form = PotentialNewMemberForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('dashboard:recruitment_c'))

    context = {
        'title': 'Add Potential New Member',
        'form': form,
    }
    return render(request, 'model-add.html', context)


class PnmDelete(DeleteView):
    model = PotentialNewMember
    success_url = reverse_lazy('dashboard:recruitment_c')


class PnmEdit(UpdateView):
    model = PotentialNewMember
    success_url = reverse_lazy('dashboard:recruitment_c')
    fields = ['first_name', 'last_name', 'case_ID', 'phone_number', 'primary_contact', 'secondary_contact',
              'tertiary_contact', 'notes']


def recruitment_c_event(request, event_id):
    """ Renders the recruitment chair way of view RecruitmentEvents """
    # TODO: verify that user is Recruitment Chair
    event = RecruitmentEvent.objects.get(pk=event_id)
    pnms = PotentialNewMember.objects.all()
    brothers = Brother.objects.exclude(brother_status='2')
    pnm_form_list = []
    brother_form_list = []
    for pnm in pnms:
        if event.attendees_pnms.filter(pk=pnm.id):
            new_form = PnmAttendanceForm(request.POST or None, initial={'present': True}, prefix=pnm.id,
                                         pnm="- %s %s" % (pnm.first_name, pnm.last_name))
            pnm_form_list.append(new_form)
        else:
            new_form = PnmAttendanceForm(request.POST or None, initial={'present': False}, prefix=pnm.id,
                                         pnm="- %s %s" % (pnm.first_name, pnm.last_name))
            pnm_form_list.append(new_form)

    for brother in brothers:
        if event.attendees_brothers.filter(roster_number=brother.roster_number):
            new_form = BrotherAttendanceForm(request.POST or None, initial={'present': True},
                                             prefix=brother.roster_number,
                                             brother="- %s %s" % (brother.first_name, brother.last_name))
            brother_form_list.append(new_form)
        else:
            new_form = BrotherAttendanceForm(request.POST or None, initial={'present': False},
                                             prefix=brother.roster_number,
                                             brother="- %s %s" % (brother.first_name, brother.last_name))
            brother_form_list.append(new_form)

    if request.method == 'POST':
        if utils.forms_is_valid(pnm_form_list) and utils.forms_is_valid(brother_form_list):
            for counter, form in enumerate(pnm_form_list):
                instance = form.cleaned_data
                if instance['present'] is True:
                    event.attendees_pnms.add(pnms[counter])
                    event.save()
                if instance['present'] is False:
                    event.attendees_pnms.remove(pnms[counter])
                    event.save()
            for counter, form in enumerate(brother_form_list):
                instance = form.cleaned_data
                if instance['present'] is True:
                    event.attendees_brothers.add(brothers[counter])
                    event.save()
                if instance['present'] is False:
                    event.attendees_brothers.remove(brothers[counter])
                    event.save()
            return HttpResponseRedirect(reverse('dashboard:recruitment_c'))

    context = {
        'type': 'attendance',
        'pnm_form_list': pnm_form_list,
        'brother_form_list': brother_form_list,
        'event': event,
    }
    return render(request, "recruitment-event.html", context)


def recruitment_c_event_add(request):
    """ Renders the recruitment chair way of adding RecruitmentEvents """
    # TODO: verify that user is Recruitment Chair
    form = RecruitmentEventForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            # TODO: add google calendar event adding
            instance = form.save(commit=False)
            try:
                semester = Semester.objects.filter(season=utils.get_season_from(instance.date.month),
                                                   year=instance.date.year)[0]
            except IndexError:
                semester = Semester(season=utils.get_season_from(instance.date.month),
                                    year=instance.date.year)
                semester.save()
            if instance.end_time is not None and instance.end_time < instance.start_time:
                context = {
                    'position': 'Recruitment Chair',
                    'form': form,
                    'error_message': "Start time after end time!",
                }
                return render(request, "event-add.html", context)
            instance.semester = semester
            instance.save()
            return HttpResponseRedirect(reverse('dashboard:recruitment_c'))

    context = {
        'position': 'Recruitment Chair',
        'form': form,
    }
    return render(request, "event-add.html", context)


class RecruitmentEventDelete(DeleteView):
    # TODO: verify recruitment chair
    model = RecruitmentEvent
    success_url = reverse_lazy('dashboard:recruitment_c')


class RecruitmentEventEdit(UpdateView):
    model = RecruitmentEvent
    success_url = reverse_lazy('dashboard:recruitment_c')
    fields = ['name', 'rush', 'date', 'start_time', 'end_time', 'notes']


def service_c(request):
    """ Renders the service chair page with service submissions """
    # TODO: verify that user is Service Chair
    events = ServiceEvent.objects.filter(semester__season=utils.get_season(),
                                         semester__year=utils.get_year())
    submissions_pending = ServiceSubmission.objects.filter(semester__season=utils.get_season(),
                                                           semester__year=utils.get_year(), status='0').order_by("date")

    submissions_submitted = ServiceSubmission.objects.filter(semester__season=utils.get_season(),
                                                             semester__year=utils.get_year(), status='1').order_by(
        "date")

    hours_pending = 0
    for submission in submissions_pending:
        hours_pending += submission.hours
    for submission in submissions_submitted:
        hours_pending += submission.hours

    hours_approved = 0
    submissions_approved = ServiceSubmission.objects.filter(semester__season=utils.get_season(),
                                                            semester__year=utils.get_year(), status='2')
    for submission in submissions_approved:
        hours_approved += submission.hours

    context = {
        'events': events,
        'hours_approved': hours_approved,
        'hours_pending': hours_pending,
        'submissions_pending': submissions_pending,
        'submissions_submitted': submissions_submitted,
    }
    return render(request, 'service-chair.html', context)


def service_c_event(request, event_id):
    """ Renders the service chair way of adding ServiceEvent """
    # TODO: verify that user is Service Chair
    event = ServiceEvent.objects.get(pk=event_id)
    brothers = Brother.objects.exclude(brother_status='2')
    brothers_rsvp = event.rsvp_brothers.all()
    form_list = []

    for brother in brothers:
        if event.attendees.filter(roster_number=brother.roster_number):
            new_form = BrotherAttendanceForm(request.POST or None, initial={'present': True},
                                             prefix=brother.roster_number,
                                             brother="- %s %s" % (brother.first_name, brother.last_name))
            form_list.append(new_form)
        else:
            new_form = BrotherAttendanceForm(request.POST or None, initial={'present': False},
                                             prefix=brother.roster_number,
                                             brother="- %s %s" % (brother.first_name, brother.last_name))
            form_list.append(new_form)

    if request.method == 'POST':
        if utils.forms_is_valid(form_list):
            for counter, form in enumerate(form_list):
                instance = form.cleaned_data
                if instance['present'] is True:
                    event.attendees.add(brothers[counter])
                    event.save()
                if instance['present'] is False:
                    event.attendees.remove(brothers[counter])
                    event.save()
            return HttpResponseRedirect(reverse('dashboard:service_c'))

    context = {
        'type': 'attendance',
        'brother_form_list': form_list,
        'brothers_rsvp': brothers_rsvp,
        'event': event,
    }

    return render(request, 'service-event.html', context)


class ServiceEventDelete(DeleteView):
    model = ServiceEvent
    success_url = reverse_lazy('dashboard:service_c')


class ServiceEventEdit(UpdateView):
    model = ServiceEvent
    success_url = reverse_lazy('dashboard:service_c')
    fields = ['name', 'date', 'start_time', 'end_time', 'notes']


class ServiceSubmissionChairEdit(UpdateView):
    model = ServiceSubmission
    success_url = reverse_lazy('dashboard:service_c')
    fields = ['status']
    template_name = 'dashboard/servicesubmission_chair_form.html'


def service_c_event_add(request):
    """ Renders the service chair way of adding ServiceEvent """
    # TODO: verify that user is Service Chair
    form = ServiceEventForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            # TODO: add google calendar event adding
            instance = form.save(commit=False)
            try:
                semester = Semester.objects.filter(season=utils.get_season_from(instance.date.month),
                                                   year=instance.date.year)[0]
            except IndexError:
                semester = Semester(season=utils.get_season_from(instance.date.month),
                                    year=instance.date.year)
                semester.save()
            if instance.end_time is not None and instance.end_time < instance.start_time:
                context = {
                    'position': 'Service Chair',
                    'form': form,
                    'error_message': "Start time after end time!",
                }
                return render(request, "event-add.html", context)
            instance.semester = semester
            instance.save()
            return HttpResponseRedirect(reverse('dashboard:service_c'))

    context = {
        'position': 'Service Chair',
        'form': form,
    }

    return render(request, 'event-add.html', context)


def philanthropy_c(request):
    """ Renders the philanthropy chair's RSVP page for different events """
    # TODO: verify that user is Philanthropy Chair
    events = PhilanthropyEvent.objects.filter(semester__season=utils.get_season(),
                                              semester__year=utils.get_year())
    context = {
        'events': events,
    }
    return render(request, 'philanthropy-chair.html', context)


def philanthropy_c_event(request, event_id):
    """"""
    event = PhilanthropyEvent.objects.get(pk=event_id)
    brothers_rsvp = event.rsvp_brothers.all()

    context = {
        'type': 'ec-view',
        'brothers_rsvp': brothers_rsvp,
        'event': event,
    }

    return render(request, 'philanthropy-event.html', context)


def philanthropy_c_event_add(request):
    """ Renders the philanthropy chair way of adding PhilanthropyEvent """
    # TODO: verify that user is Philanthropy Chair
    form = PhilanthropyEventForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            # TODO: add google calendar event adding
            instance = form.save(commit=False)
            try:
                semester = Semester.objects.filter(season=utils.get_season_from(instance.date.month),
                                                   year=instance.date.year)[0]
            except IndexError:
                semester = Semester(season=utils.get_season_from(instance.date.month),
                                    year=instance.date.year)
                semester.save()
            if instance.end_time is not None and instance.end_time < instance.start_time:
                context = {
                    'position': 'Philanthropy Chair',
                    'form': form,
                    'error_message': "Start time after end time!",
                }
                return render(request, "event-add.html", context)
            instance.semester = semester
            instance.save()
            return HttpResponseRedirect(reverse('dashboard:service_c'))

    context = {
        'position': 'Philanthropy Chair',
        'form': form,
    }
    return render(request, 'event-add.html', context)


class PhilanthropyEventDelete(DeleteView):
    model = PhilanthropyEvent
    success_url = reverse_lazy('dashboard:philanthropy_c')


class PhilanthropyEventEdit(UpdateView):
    model = PhilanthropyEvent
    success_url = reverse_lazy('dashboard:philanthropy_c')
    fields = ['name', 'date', 'start_time', 'end_time', 'notes']


def detail_m(request):
    """ Renders the detail manager page"""
    # TODO: verify that user is Detail Manager
    return render(request, 'detail-manager.html', {})
