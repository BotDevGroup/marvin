from apscheduler.schedulers.background import BackgroundScheduler


DEFAULT_CONFIG = {
    'apscheduler.jobstores.default': {
            'type': 'mongodb'
    },
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
        'max_workers': 5
    },
    'apscheduler.job_defaults.coalesce': True,
    'apscheduler.job_defaults.max_instances': '3',
    'apscheduler.job_defaults.replace_existing': True,
    'apscheduler.timezone': 'America/Santo_Domingo'
}


def configure_scheduler(config, adapter):
    scheduler_config = {}
    scheduler_config.update(DEFAULT_CONFIG)
    scheduler_config.update(config.get('scheduler', {}))

    adapter.scheduler = BackgroundScheduler(scheduler_config)
    return adapter.scheduler
