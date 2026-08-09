from dagster import DefaultScheduleStatus

from orchestration.dagster_assets import daily_schedule


def test_daily_training_schedule_is_enabled_by_default():
    assert daily_schedule.default_status is DefaultScheduleStatus.RUNNING
