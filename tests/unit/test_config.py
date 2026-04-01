from app.config import settings


def test_settings_import():
    assert settings is not None


def test_log_level():
    assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]


def test_chunk_size():
    assert settings.CHUNK_SIZE > 0


def test_vector_size():
    assert settings.VECTOR_SIZE == 1024


def test_chunk_overlap():
    assert settings.CHUNK_OVERLAP < settings.CHUNK_SIZE