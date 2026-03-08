from ai_data_qa.scheduler import SchedulerJob, SchedulerJobUpdate, SchedulerStore


def test_scheduler_store_crud(tmp_path):
    store = SchedulerStore(str(tmp_path / "jobs.json"))

    created = store.create_job(SchedulerJob(dataset="analytics", interval_seconds=300))
    assert created.dataset == "analytics"

    jobs = store.list_jobs()
    assert len(jobs) == 1

    updated = store.update_job(
        created.id,
        SchedulerJobUpdate(dataset="analytics_v2", interval_seconds=600),
    )
    assert updated.dataset == "analytics_v2"
    assert updated.interval_seconds == 600

    marked = store.mark_run(created.id)
    assert marked.last_run_at is not None

    store.delete_job(created.id)
    assert store.list_jobs() == []
