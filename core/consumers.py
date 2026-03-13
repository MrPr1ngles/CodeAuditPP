import json
import subprocess
import tempfile
import os
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

        self.send(text_data=json.dumps({
            'event': 'init',
            'content': self.session.code_content or '',
            'task_content': self.session.task_content or ''
        }))

        ActionLog.objects.create(session=self.session, user=self.user, event_type='join', content='')
        join_payload = {
            'event': 'join',
            'user': self.user.username,
            'role': self.user.role,
            'timestamp': timezone.now().isoformat(),
        }
        async_to_sync(self.channel_layer.group_send)(self.group_name, {'type': 'broadcast_event', 'message': join_payload})

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        ActionLog.objects.create(session=self.session, user=self.user, event_type='leave', content='')
        leave_payload = {
            'event': 'leave',
            'user': self.user.username,
            'role': self.user.role,
            'timestamp': timezone.now().isoformat(),
        }
        async_to_sync(self.channel_layer.group_send)(self.group_name, {'type': 'broadcast_event', 'message': leave_payload})

    def receive(self, text_data):
        data = json.loads(text_data)
        event = data.get('event')
        timestamp = timezone.now().isoformat()

        # ЛОКАЛЬНАЯ КОМПИЛЯЦИЯ КОДА (без использования сторонних API)
        if event == 'run_code':
            code = data.get('code', '')
            lang = data.get('language', 'Python')
            output = ""
            
            try:
                if lang == 'Python':
                    # Запуск Python локально
                    res = subprocess.run(['python', '-c', code], capture_output=True, text=True, timeout=5)
                    output = res.stdout if res.returncode == 0 else res.stderr

                elif lang == 'JavaScript':
                    # Запуск Node.js
                    res = subprocess.run(['node', '-e', code], capture_output=True, text=True, timeout=5)
                    output = res.stdout if res.returncode == 0 else res.stderr

                elif lang == 'C++':
                    # Компиляция и запуск C++
                    with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False) as f:
                        f.write(code.encode('utf-8'))
                        filepath = f.name
                    
                    exe_path = filepath[:-4] # убираем .cpp
                    
                    # Компиляция
                    compile_res = subprocess.run(['g++', filepath, '-o', exe_path], capture_output=True, text=True, timeout=10)
                    if compile_res.returncode != 0:
                        output = f"Ошибка компиляции:\n{compile_res.stderr}"
                    else:
                        # Запуск
                        run_res = subprocess.run([exe_path], capture_output=True, text=True, timeout=5)
                        output = run_res.stdout if run_res.returncode == 0 else run_res.stderr
                        
                        # Удаляем скомпилированный файл
                        if os.path.exists(exe_path):
                            os.remove(exe_path)
                            
                    # Удаляем исходник
                    if os.path.exists(filepath):
                        os.remove(filepath)

                if not output.strip():
                    output = "Программа выполнилась успешно, но ничего не вывела на экран."

            except subprocess.TimeoutExpired:
                output = "Ошибка: Время выполнения программы превысило 5 секунд (возможно, у вас бесконечный цикл)."
            except FileNotFoundError as e:
                output = f"Ошибка: Не установлен компилятор для {lang}. Добавьте его в Dockerfile."
            except Exception as e:
                output = f"Внутренняя ошибка сервера: {str(e)}"
            
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {'type': 'broadcast_event', 'message': {'event': 'execution_result', 'output': output}}
            )
            return

        payload = {
            'event': event,
            'user': data.get('user'),
            'role': data.get('role'),
            'timestamp': timestamp,
        }

        # СИНХРОНИЗАЦИЯ ПОЛЯ С ЗАДАНИЕМ
        if event == 'task_update':
            task_content = data.get('task_content', '')
            self.session.task_content = task_content
            self.session.save()
            payload['task_content'] = task_content

        elif event == 'typing':
            payload['is_typing'] = data.get('is_typing', False)

        elif event == 'change':
            content = data.get('content', '')
            self.session.code_content = content
            self.session.save()
            payload['content'] = content

        elif event in ('copy', 'paste', 'paste_blocked', 'blur'):
            if self.user.role == 'candidate':
                log_event = event
                content_log = json.dumps(data.get('range', {})) if event in ('copy', 'paste') else ''
                ActionLog.objects.create(session=self.session, user=self.user, event_type=log_event, content=content_log)
                if event in ('copy', 'paste'):
                    payload['range'] = data.get('range', {})
            else:
                return  

        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {'type': 'broadcast_event', 'message': payload}
        )

    def broadcast_event(self, event):
        self.send(text_data=json.dumps(event['message']))