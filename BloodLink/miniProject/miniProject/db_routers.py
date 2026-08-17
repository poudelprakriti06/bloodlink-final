

class LegacyRouter:
    def db_for_read(self, model, **hints):
        # If the model is unmanaged (legacy), read from 'legacy' DB
        if hasattr(model, '_meta') and not model._meta.managed:
            return 'legacy'
        return None  # Default uses 'default'

    def db_for_write(self, model, **hints):
        # Block writes to unmanaged models to protect legacy DB
        if hasattr(model, '_meta') and not model._meta.managed:
            return None
        return 'default'  # All other writes go to your new DB

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Only run migrations for 'bloodbank' and 'myapp' on the 'default' DB
        if app_label in ['bloodbank', 'myapp']:
            return db == 'default'
        return None