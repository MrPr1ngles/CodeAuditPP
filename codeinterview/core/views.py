import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from .forms import CustomUserCreationForm, JoinSessionForm
from .models import Session, ActionLog


def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.role == 'examiner':
        return redirect('sessions_list')
    return redirect('join_session')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    return redirect('logout_success')


def logout_success_view(request):
    return render(request, 'core/logout_success.html')


@login_required
def create_session_view(request):
    if request.user.role != 'examiner':
        return redirect('index')
    if request.method == 'POST':
        session = Session.objects.create(examiner=request.user)
        return redirect('session_detail', code=session.code)
    return render(request, 'core/create_session.html')


@login_required
def sessions_list_view(request):
    if request.user.role != 'examiner':
        return redirect('index')

    sessions = Session.objects.filter(examiner=request.user).order_by('-created_at')
    session_data = []
    for s in sessions:
        joins = set(
            ActionLog.objects.filter(session=s, event_type='join')
                     .values_list('user__username', flat=True)
        )
        leaves = set(
            ActionLog.objects.filter(session=s, event_type='leave')
                     .values_list('user__username', flat=True)
        )
        active_count = len(joins - leaves)
        session_data.append({
            'session': s,
            'active': active_count
        })

    return render(request, 'core/sessions_list.html', {
        'session_data': session_data,
    })


@require_POST
@login_required
def delete_session(request, code):
    if request.user.role != 'examiner':
        return redirect('sessions_list')
    session = get_object_or_404(Session, code=code, examiner=request.user)

    joins = set(
        ActionLog.objects.filter(session=session, event_type='join')
                 .values_list('user__username', flat=True)
    )
    leaves = set(
        ActionLog.objects.filter(session=session, event_type='leave')
                 .values_list('user__username', flat=True)
    )
    if len(joins - leaves) == 0:
        session.delete()

    return redirect('sessions_list')


@login_required
def join_session_view(request):
    if request.user.role != 'candidate':
        return redirect('index')
    if request.method == 'POST':
        form = JoinSessionForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                Session.objects.get(code=code)
                return redirect('session_detail', code=code)
            except Session.DoesNotExist:
                form.add_error('code', 'Сессия с таким кодом не найдена.')
    else:
        form = JoinSessionForm()
    return render(request, 'core/join_session.html', {'form': form})


@login_required
def session_detail_view(request, code):
    if request.user.role == 'examiner':
        return redirect('examiner_editor', code=code)
    return redirect('code_editor', code=code)


@login_required
def code_editor_view(request, code):
    if request.user.role == 'examiner':
        return redirect('examiner_editor', code=code)
    session = get_object_or_404(Session, code=code)
    return render(request, 'core/code_editor.html', {'session': session})


@login_required
def examiner_editor_view(request, code):
    if request.user.role != 'examiner':
        return redirect('index')
    session = get_object_or_404(Session, code=code, examiner=request.user)

    qs = ActionLog.objects.filter(
        session=session,
        event_type__in=['join', 'copy', 'paste', 'blur']
    ).order_by('timestamp')

    logs = []
    participants = {}
    for log in qs:
        if log.event_type == 'join':
            participants[log.user.username] = log.user.role

        if log.event_type == 'join':
            event_txt = 'присоединился'
            rng = None
        elif log.event_type == 'copy':
            event_txt = 'скопировал'
            rng = json.loads(log.content or '{}')
        elif log.event_type == 'paste':
            event_txt = 'вставил'
            rng = json.loads(log.content or '{}')
        else:  
            event_txt = 'потерял фокус'
            rng = None

        logs.append({
            'time': log.timestamp.strftime('%H:%M'),
            'user': log.user.username,
            'event': event_txt,
            'range': rng
        })

    if request.user.username not in participants:
        participants[request.user.username] = request.user.role

    participants_json = json.dumps([
        {'user': u, 'role': r}
        for u, r in participants.items()
    ])

    return render(request, 'core/examiner_editor.html', {
        'session': session,
        'initial_logs': logs,
        'participants_json': participants_json,
    })
