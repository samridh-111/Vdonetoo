from celery import Celery
from celery.signals import beat_init, worker_process_init

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ivr_automation",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.tasks.pipeline_tasks",
        "app.workers.tasks.script_tasks",
        "app.workers.tasks.audio_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.pipeline_tasks.*": {"queue": "orchestration"},
        "app.workers.tasks.script_tasks.*": {"queue": "pipeline"},
        "app.workers.tasks.audio_tasks.*": {"queue": "elevenlabs_queue"},
    },
    beat_schedule={
        "refill-elevenlabs-token-bucket": {
            "task": "app.workers.tasks.pipeline_tasks.refill_rate_limit_tokens",
            "schedule": 1.0,
        },
    },
)


@worker_process_init.connect
def _reset_process_local_singletons(**_kwargs: object) -> None:
    """Celery's prefork pool forks worker processes after the parent process
    has already imported this module. Any lru_cache-backed engine/connection
    created in the parent (or an earlier fork) must not be reused across the
    fork boundary. Clearing the caches here forces each worker process to
    build its own engine/session-factory/Redis client on first use."""
    from app.core import db, redis_client
    from app.providers.translation import factory as translation_factory
    from app.workers import factories

    db.get_engine.cache_clear()
    db.get_session_factory.cache_clear()
    redis_client.get_redis.cache_clear()
    redis_client.get_sync_redis.cache_clear()
    factories.get_storage_provider.cache_clear()
    factories.get_voice_provider.cache_clear()
    translation_factory.get_translation_provider.cache_clear()


@beat_init.connect
def _reset_beat_singletons(**_kwargs: object) -> None:
    from app.core import redis_client

    redis_client.get_sync_redis.cache_clear()
