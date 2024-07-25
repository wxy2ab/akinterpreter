import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
from typing import Callable, List, Any
import asyncio
import time
from ..utils.single_ton import Singleton

# 配置日志记录
from ..utils.log import logger

class SchedulerManager(metaclass=Singleton):
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("Scheduler started.")

    def add_job(self, func: Callable[..., Any], trigger: str, **trigger_args) -> Job:
        """
        添加一个新的 job
        :param func: 要执行的函数，可以是同步或异步函数
        :param trigger: 触发器类型 ('date', 'interval', 'cron')
        :param trigger_args: 触发器参数
        :return: 返回添加的 job
        """
        job = self.scheduler.add_job(func, trigger, **trigger_args)
        logger.info(f"Job {job.id} added.")
        return job

    def remove_job(self, job_id: str) -> None:
        """
        删除一个 job
        :param job_id: job 的 ID
        """
        self.scheduler.remove_job(job_id)
        logger.info(f"Job {job_id} removed.")

    def get_jobs(self) -> List[Job]:
        """
        获取所有的 job
        :return: 返回所有 job 的列表
        """
        jobs = self.scheduler.get_jobs()
        logger.info(f"Retrieved {len(jobs)} jobs.")
        return jobs

    def stop(self) -> None:
        """
        停止调度器
        """
        self.scheduler.shutdown()
        logger.info("Scheduler stopped.")