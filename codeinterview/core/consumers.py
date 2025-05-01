from channels.generic.websocket import WebsocketConsumer
import json
from asgiref.sync import async_to_sync
from .models import Session, ActionLog

class SessionConsumer(WebsocketConsumer):
    def connect(self):
        self.code = self.scope['url_route']['kwargs']['code']
        self.group_name = f"session_{self.code}"

        try:
            self.session = Session.objects.get(code=self.code)
        except Session.DoesNotExist:
            self.close()
            return

        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get('event')
        content = data.get('content', '')
        user = self.scope['user']

        ActionLog.objects.create(
            session=self.session,
            user=user,
            event_type=event_type,
            content=content
        )
