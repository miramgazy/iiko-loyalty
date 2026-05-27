from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet

class EncryptedCharField(models.CharField):
    description = "A char field that transparently encrypts and decrypts its database values"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fernet = None

    @property
    def fernet(self):
        if self._fernet is None:
            key = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
            if not key:
                raise ValueError("FIELD_ENCRYPTION_KEY settings is not set")
            if isinstance(key, str):
                key = key.encode('utf-8')
            self._fernet = Fernet(key)
        return self._fernet

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None or value == '':
            return value
        encrypted_bytes = self.fernet.encrypt(str(value).encode('utf-8'))
        return encrypted_bytes.decode('utf-8')

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        try:
            decrypted_bytes = self.fernet.decrypt(value.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception:
            return value

    def to_python(self, value):
        if value is None or value == '':
            return value
        if isinstance(value, str) and value.startswith('gAAAAA'):
            try:
                decrypted_bytes = self.fernet.decrypt(value.encode('utf-8'))
                return decrypted_bytes.decode('utf-8')
            except Exception:
                pass
        return super().to_python(value)
