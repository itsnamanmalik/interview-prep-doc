---
icon: material/lan-connect
---

# Websockets / Channels (Django)

WebSockets and Django Channels are powerful tools for adding real-time communication capabilities to Django applications. Here's an overview of how they work and how you can use them in your projects:

### What Are WebSockets?

WebSockets are a protocol that provides full-duplex communication channels over a single, long-lived connection between a client (usually a web browser) and a server. Unlike HTTP, which is a request-response protocol, WebSockets allow for persistent connections, enabling real-time, two-way interaction between the client and the server.

### Django Channels

Django Channels extends Django to handle WebSockets, HTTP2, and other protocols beyond HTTP. It integrates directly with Django, allowing developers to utilize Django's capabilities while adding support for handling asynchronous protocols like WebSockets.

### **Key Concepts in Django Channels**

1. **Consumers**: Consumers are Django’s equivalent of views in the Channels framework. They handle the WebSocket connections and messages. There are two main types of consumers:

    - **Synchronous Consumers**: Suitable for simple, blocking operations.

    - **Asynchronous Consumers**: Use Python’s `async` and `await` syntax to handle asynchronous operations, making them ideal for WebSocket connections.

1. **Routing**: Django Channels uses routing to connect incoming WebSocket connections to their respective consumers, similar to how URL routing works in Django.

1. **Channels**: Channels are the basic unit of communication in Django Channels. They are a place where messages can be sent and received, allowing consumers to communicate asynchronously.

1. **Channel Layers**: Channel layers provide a way to handle distributed messaging. They allow multiple Django processes to talk to each other, useful for scaling an application horizontally. The most common backend for channel layers is Redis.

### Setting Up Django Channels

1. **Install Django Channels**:  
Start by installing Django Channels via pip:

```bash
pip install channels
```

1. **Update Django Settings**:  
Update your `settings.py` to include `channels` and configure the `ASGI_APPLICATION` setting:

```python
INSTALLED_APPS = [
    # Other installed apps
    'channels',
]

ASGI_APPLICATION = 'your_project_name.asgi.application'

# Redis channel layer (optional but recommended for production)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
=
```

1. **Create ASGI Configuration**:  
You need to create an ASGI configuration file (usually `asgi.py`) in your project root:

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import your_app_name.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project_name.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            your_app_name.routing.websocket_urlpatterns
        )
    ),
})
```

1. **Define Routing**:  
Create a `routing.py` file in your Django app to define WebSocket routing:

```python
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/some_path/', consumers.MyConsumer.as_asgi()),
]
```

1. **Create Consumers**:  
Create consumers in `consumers.py` to handle WebSocket connections:

```python
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "some_group"

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
```

1. **Run Your Django Application**:  
With Channels configured, you can run your application using Daphne (the ASGI server) instead of the default WSGI server:

```bash
daphne -p 8000 your_project_name.asgi:application
```

### Use Cases for Django Channels

- **Chat Applications**: Real-time chat systems where messages are instantly pushed to all connected clients.

- **Live Notifications**: Push notifications to users without needing to refresh the page.

- **Collaborative Tools**: Applications like collaborative document editing or whiteboards.

- **Real-time Dashboards**: Display live updates or changes to dashboards or data visualizations.

Django Channels is a powerful extension to Django, enabling you to build a wide range of real-time applications by leveraging WebSockets and other asynchronous protocols.
