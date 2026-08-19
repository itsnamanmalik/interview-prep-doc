---
icon: material/content-copy
---

# Read Replica DB

Implementing a read replica for PostgreSQL involves setting up a replica server that copies data from a primary database server. In a Django application, you can then configure your database settings to use the read replica for read operations, improving performance and reducing the load on the primary database.

### Step 1: Set Up PostgreSQL Read Replica

1. **Primary Database Configuration**:

    - Make sure the primary PostgreSQL server is configured to allow replication. Edit the `postgresql.conf` file on the primary server:

```
wal_level = replica
max_wal_senders = 5
hot_standby = on
```

    - In the `pg_hba.conf` file, add an entry to allow the replica server to connect:

```
host replication all <replica_server_ip> md5
```

1. **Create a Replication User**:

    - On the primary server, create a user specifically for replication:

```sql
CREATE USER replication_user WITH REPLICATION ENCRYPTED PASSWORD 'yourpassword';
```

1. **Base Backup**:

    - Take a base backup from the primary server and transfer it to the replica server:

```bash
pg_basebackup -h <primary_server_ip> -D /var/lib/postgresql/12/main -U replication_user -Fp -Xs -P
```

1. **Configure Replica Server**:

    - On the replica server, configure it to follow the primary by editing `recovery.conf`:

```
standby_mode = 'on'
primary_conninfo = 'host=<primary_server_ip> port=5432 user=replication_user password=yourpassword'
```

    - Start the replica server.

### Step 2: Configure Django to Use Read Replica

In Django, you can configure the `DATABASES` setting to differentiate between read and write operations by setting up a database router.

1. **Update** `DATABASES` **in** `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'yourdbname',
        'USER': 'yourdbuser',
        'PASSWORD': 'yourpassword',
        'HOST': 'primary_db_host',
        'PORT': '5432',
    },
    'replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'yourdbname',
        'USER': 'yourdbuser',
        'PASSWORD': 'yourpassword',
        'HOST': 'replica_db_host',
        'PORT': '5432',
    }
}
```

1. **Create a Database Router**: Create a `routers.py` file to define the routing logic:

```python
class PrimaryReplicaRouter:
    def db_for_read(self, model, **hints):
        return 'replica'

    def db_for_write(self, model, **hints):
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == 'default'
```

1. **Add the Router to Django Settings**: In `settings.py`, add the router to the `DATABASE_ROUTERS` setting:

```python
DATABASE_ROUTERS = ['path.to.routers.PrimaryReplicaRouter']
```

### Step 3: Usage in Django

With this setup, Django will automatically use the read replica for read operations and the primary database for write operations. This improves performance by offloading read queries to the replica server.

### Step 4: Testing

- Ensure the replica is properly synchronized with the primary server.

- Test your application to make sure it correctly uses the replica for reads and the primary for writes.

This setup should be robust for most Django applications needing to scale read operations across multiple servers.
