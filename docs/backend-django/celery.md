---
icon: material/cog-clockwise
---

# Celery

**Celery** is an asynchronous task queue/job queue based on distributed message passing. It is focused on real-time operation but supports scheduling as well. Celery is commonly used with Django to handle background tasks, periodic tasks, and long-running operations outside of the request/response cycle.

### What is Celery?

Celery is an open-source task queue system written in Python that allows you to execute tasks asynchronously and concurrently. It is designed to distribute tasks to multiple workers, making it ideal for handling tasks that are time-consuming, need to run periodically, or need to run independently from the main web process.

### Why Use Celery in Django?

1. **Asynchronous Task Execution**: Celery allows Django applications to run tasks asynchronously in the background, freeing up the main process to handle web requests without waiting for the task to complete. This is crucial for improving user experience and application responsiveness.

1. **Handling Long-Running Tasks**: For tasks that are resource-intensive and time-consuming (like image processing, sending emails, or data analysis), Celery can offload these to worker processes, ensuring the web application remains responsive.

1. **Periodic Task Scheduling**: Celery can be used to schedule tasks at regular intervals, similar to cron jobs, but with more flexibility and in a Pythonic way. This is useful for routine maintenance tasks, like clearing cache or sending out newsletters.

1. **Scalability**: Celery is highly scalable, meaning you can distribute tasks across multiple workers and machines, balancing the load and improving performance as your application grows.

1. **Error Handling and Retries**: Celery provides robust error handling, allowing tasks to be retried automatically if they fail. It also supports setting timeouts and limits on task execution, helping manage resources effectively.

### Where is Celery Used in Django Applications?

Celery is typically used in scenarios where background processing is needed, such as:

- **Sending Emails**: Sending bulk emails or notifications in the background without blocking the web request.

- **Image and File Processing**: Resizing images, converting file formats, or processing uploads asynchronously.

- **Data Import/Export**: Running data import/export jobs in the background, especially if they involve large datasets.

- **Web Scraping**: Running web scraping jobs as background tasks to avoid blocking other operations.

- **Scheduled Tasks**: Running periodic tasks like clearing expired sessions, updating caches, or syncing with third-party services.

### When to Use Celery in Django?

Use Celery in Django when you have:

1. **Background Tasks**: Any operation that needs to run in the background, like sending emails, generating reports, or processing files, should use Celery to avoid blocking the main web server thread.

1. **Long-Running Tasks**: Tasks that take a significant amount of time to complete, such as complex computations, database operations, or data analysis, should be offloaded to Celery.

1. **Periodic Tasks**: When you need to schedule tasks to run at regular intervals (e.g., daily, hourly, weekly), Celery's built-in support for periodic tasks (using `celery.beat`) is ideal.

1. **Asynchronous Operations**: When you want to perform operations asynchronously (like processing user requests without making them wait for the operation to complete), Celery provides a clean and effective solution.

### How to Use Celery in Django?

Here’s a brief overview of setting up and using Celery in a Django project:

1. **Install Celery**: Install Celery using pip.

```bash
pip install celery
```

1. **Configure Django for Celery**: In your Django settings, configure Celery with a broker (like RabbitMQ or Redis) and, optionally, a result backend.

```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

1. **Create a Celery App**: Create a new file named `celery.py` in your Django project directory (same level as `settings.py`) to configure the Celery application.

```python
# myproject/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

1. **Define Tasks**: Create tasks in your Django apps by defining functions and decorating them with `@shared_task`.

```python
# myapp/tasks.py
from celery import shared_task

@shared_task
def send_email_task(user_id):
    # Logic for sending an email to the user
    pass
```

1. **Run Celery Worker**: Start the Celery worker to listen for and execute tasks.

```bash
celery -A myproject worker -l info
```

1. **Execute Tasks**: Call tasks from your Django views or models. These tasks will be executed asynchronously by Celery workers.

```python
# In your views or models
from myapp.tasks import send_email_task

send_email_task.delay(user_id)
```

### Conclusion

Celery is a powerful tool for Django developers to handle background tasks, long-running processes, and scheduled jobs efficiently. By using Celery, you can significantly improve the performance and responsiveness of your Django applications, especially when dealing with tasks that require significant processing or need to run periodically.
