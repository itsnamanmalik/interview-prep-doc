---
icon: material/email-fast-outline
---

# Background Tasks & Email

Django hands you `django.core.mail` and, by convention, Celery. FastAPI gives you `BackgroundTasks` and nothing else, so knowing when that is not enough is the interview question.

### `BackgroundTasks`

Work that runs **after** the response has been sent, in the same process:

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()
sent: list[str] = []

def send_welcome(email: str) -> None:
    sent.append(email)            # stand-in for an SMTP call

@app.post("/signup")
async def signup(email: str, tasks: BackgroundTasks):
    tasks.add_task(send_welcome, email)
    return {"status": "created"}  # returns immediately
```

Both `def` and `async def` tasks work: sync ones go to the thread pool, async ones onto the event loop.

### What `BackgroundTasks` does not give you

The whole point of the question:

- **No durability.** The task lives in process memory. A crash, an OOM kill, or a rolling deploy between response and execution loses it silently.

- **No retries.** An exception is logged and the task is gone. The client already got a 200.

- **No visibility.** Nothing to inspect, no status, no dead-letter queue.

- **It competes with your web workers.** A slow task occupies the same process that serves requests — and an `async` task that blocks stalls the event loop *after* the response, which is hard to spot.

- **No scheduling.** No "in one hour", no cron.

So: fine for a cache invalidation or a best-effort audit line. Not fine for a payment receipt.

### When to use a real queue

Reach for Celery, ARQ (async-native, Redis) or Dramatiq when the work is important, slow, retryable or scheduled:

```python
# tasks.py
from celery import Celery

celery_app = Celery("worker", broker="redis://localhost:6379/0")

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_receipt(self, order_id: int) -> None:
    try:
        ...                       # render and send
    except Exception as exc:
        raise self.retry(exc=exc)
```

```python
# main.py
from fastapi import FastAPI
from tasks import send_receipt

app = FastAPI()

@app.post("/orders/{order_id}/receipt")
async def queue_receipt(order_id: int):
    send_receipt.delay(order_id)          # returns as soon as it is enqueued
    return {"queued": True}
```

| | `BackgroundTasks` | Celery / ARQ / Dramatiq |
| --- | --- | --- |
| Infrastructure | None | Broker (Redis / RabbitMQ) + workers |
| Survives a crash | No | Yes |
| Retries | No | Yes, with backoff |
| Scheduling | No | Yes (beat / cron) |
| Runs where | Web process | Separate workers |
| Good for | Cheap, best-effort | Anything that matters |

### Enqueue only after the transaction commits

A subtle bug worth raising unprompted: if you enqueue inside a transaction that later rolls back, the worker picks up a job for a row that does not exist. Enqueue after commit, or use a transactional outbox — write the job to a table in the same transaction and have a relay publish it.

### Sending email

There is no built-in mail layer. The realistic options:

**1. `fastapi-mail`** — async, Jinja2 templates, attachments:

```python
# pip install fastapi-mail
from fastapi import BackgroundTasks, FastAPI
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr, SecretStr

conf = ConnectionConfig(
    MAIL_USERNAME="apikey",
    MAIL_PASSWORD=SecretStr("..."),
    MAIL_FROM="no-reply@example.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.example.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    TEMPLATE_FOLDER="./templates",
)

app = FastAPI()

@app.post("/notify")
async def notify(to: EmailStr, tasks: BackgroundTasks):
    message = MessageSchema(
        subject="Welcome",
        recipients=[to],
        template_body={"name": "Alice"},
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    tasks.add_task(fm.send_message, message, template_name="welcome.html")
    return {"queued": True}
```

**2. `aiosmtplib`** — raw async SMTP, no dependency beyond the stdlib `email` package:

```python
import aiosmtplib
from email.message import EmailMessage

async def send(to: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = "no-reply@example.com"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    await aiosmtplib.send(message, hostname="smtp.example.com", port=587, start_tls=True)
```

**3. A transactional provider** (SES, SendGrid, Postmark, Resend) over HTTPS with `httpx`. Usually the right production answer: they own deliverability, DKIM/SPF alignment, bounce handling, suppression lists and templates — none of which you want to build.

**4. `smtplib` in a thread.** Fine for a legacy integration, as long as it is wrapped in `run_in_threadpool` so it does not block the loop.

### Email in production, briefly

- **Never send inline.** SMTP handshakes take hundreds of milliseconds and fail often; queue it.

- **Retry with backoff, and be idempotent.** Retries mean a message can be sent twice — key off an idempotency token if duplicates matter.

- **Handle bounces and complaints.** A provider webhook plus a suppression list, or your sender reputation degrades.

- **Templates belong in version control**, rendered with Jinja2, with a plain-text alternative alongside the HTML.

- **In tests, do not send.** Override the mail dependency, or point at a local catcher such as MailHog. Django's `locmem` backend has no FastAPI equivalent, so this is on you.

### Comparison with Django

| | Django | FastAPI |
| --- | --- | --- |
| Mail API | `send_mail`, `EmailMessage` built in | None; `fastapi-mail`, `aiosmtplib` or a provider SDK |
| Backends | SMTP, console, `locmem`, file | Whatever you configure |
| Templates | Django templates | Jinja2, by hand |
| Testing | `locmem` + `mail.outbox` | Dependency override or a local SMTP catcher |
| Async | `sync_to_async` wrapper needed | Native with `aiosmtplib` / `fastapi-mail` |
