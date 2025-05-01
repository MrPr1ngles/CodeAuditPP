from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm, JoinSessionForm
from .models import Session, ActionLog

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

@login_required
def index(request):
    if request.user.role == 'examiner':
        return redirect('sessions_list')
    return redirect('join_session')

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
    return render(request, 'core/sessions_list.html', {'sessions': sessions})

@login_required
def session_detail_view(request, code):
    try:
        session = Session.objects.get(code=code)
    except Session.DoesNotExist:
        return redirect('index')
    if request.user != session.examiner:
        return redirect('index')
    logs = ActionLog.objects.filter(session=session).order_by('timestamp')
    return render(request, 'core/session_detail.html', {
        'session': session,
        'logs': logs
    })

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
                return redirect('code_editor', code=code)
            except Session.DoesNotExist:
                form.add_error('code', 'Сессия с таким кодом не найдена.')
    else:
        form = JoinSessionForm()
    return render(request, 'core/join_session.html', {'form': form})

@login_required
def code_editor_view(request, code):
    try:
        session = Session.objects.get(code=code)
    except Session.DoesNotExist:
        return redirect('index')
    return render(request, 'core/code_editor.html', {'session': session})
