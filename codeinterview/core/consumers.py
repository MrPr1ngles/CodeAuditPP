import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .models import Session, ActionLog

class SessionConsumer(WebsocketConsumer):
    def connect(self):
        self.code = self.scope['url_route']['kwargs']['code']
        self.user = self.scope['user']
        self.group_name = f"session_{self.code}"

        try:
            self.session = Session.objects.get(code=self.code)
        except Session.DoesNotExist:
            return self.close()

        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

        # отправка текущего кода
        self.send(text_data=json.dumps({
            'event': 'init',
            'content': self.session.code_content or '',
        }))

        # лог и рассылка join
        ActionLog.objects.create(session=self.session, user=self.user, event_type='join', content='')
        join_payload = {
            'event': 'join',
            'user': self.user.username,
            'role': self.user.role,
            'color': '#007AFF',
            'timestamp': timezone.now().isoformat(),
        }
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {'type': 'broadcast_event', 'message': join_payload}
        )

    def disconnect(self, close_code):
        # удаление из группы
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

        # лог и рассылка leave
        ActionLog.objects.create(session=self.session, user=self.user, event_type='leave', content='')
        leave_payload = {
            'event': 'leave',
            'user': self.user.username,
            'role': self.user.role,
            'color': '#007AFF',
            'timestamp': timezone.now().isoformat(),
        }
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {'type': 'broadcast_event', 'message': leave_payload}
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        event = data.get('event')
        timestamp = timezone.now().isoformat()

        payload = {
            'event': event,
            'user': data.get('user'),
            'role': data.get('role'),
            'color': data.get('color'),
            'cursor': data.get('cursor'),
            'timestamp': timestamp,
        }

        if event == 'change':
            # сохраняем и рассылаем новый код
            content = data.get('content', '')
            self.session.code_content = content
            self.session.save()
            payload['content'] = content

        elif event in ('copy', 'paste', 'blur'):
            # логируем и рассылаем только событие кандидата
            if self.user.role == 'candidate':
                if event in ('copy', 'paste'):
                    ActionLog.objects.create(
                        session=self.session,
                        user=self.user,
                        event_type=event,
                        content=json.dumps(data.get('range', {}))
                    )
                    payload['range'] = data.get('range', {})
                else:
                    ActionLog.objects.create(
                        session=self.session,
                        user=self.user,
                        event_type='blur',
                        content=''
                    )
            else:
                return  # экзаменаторские copy/paste/blur игнорируем

        # курсор передаём всем, без логирования
        # события join/leave не обрабатываются здесь

        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {'type': 'broadcast_event', 'message': payload}
        )

    def broadcast_event(self, event):
        self.send(text_data=json.dumps(event['message']))
