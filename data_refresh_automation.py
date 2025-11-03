"""
Data Refresh Automation
Automated system for keeping data fresh and up-to-date
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import threading
import time
import schedule


class DataRefreshScheduler:
    """
    Automated data refresh scheduler

    Features:
    - Scheduled refresh jobs (daily, weekly, etc.)
    - Data staleness detection
    - Refresh on-demand
    - Health monitoring
    """

    def __init__(self):
        """Initialize refresh scheduler"""
        # Refresh jobs: name -> job_config
        self.jobs = {}

        # Last refresh times: data_source -> timestamp
        self.last_refresh = {}

        # Refresh status: data_source -> status_info
        self.refresh_status = {}

        # Scheduler thread
        self.running = False
        self.scheduler_thread = None

    def register_job(
        self,
        name: str,
        refresh_func: Callable,
        schedule_type: str = 'daily',
        schedule_time: str = '03:00',
        max_age_hours: int = 24,
        enabled: bool = True
    ):
        """
        Register a data refresh job

        Args:
            name: Job name
            refresh_func: Function to call for refresh (no args)
            schedule_type: 'daily', 'weekly', 'hourly'
            schedule_time: Time to run (HH:MM for daily/weekly)
            max_age_hours: Maximum data age before considered stale
            enabled: Whether job is enabled
        """
        self.jobs[name] = {
            'name': name,
            'refresh_func': refresh_func,
            'schedule_type': schedule_type,
            'schedule_time': schedule_time,
            'max_age_hours': max_age_hours,
            'enabled': enabled
        }

        self.refresh_status[name] = {
            'last_run': None,
            'last_success': None,
            'last_error': None,
            'status': 'pending',
            'run_count': 0
        }

        print(f"✓ Registered refresh job: {name} ({schedule_type} at {schedule_time})")

    def start(self):
        """Start the scheduler"""
        if self.running:
            print("⚠️ Scheduler already running")
            return

        self.running = True

        # Schedule all jobs
        for name, job in self.jobs.items():
            if not job['enabled']:
                continue

            schedule_type = job['schedule_type']
            schedule_time = job['schedule_time']

            if schedule_type == 'daily':
                schedule.every().day.at(schedule_time).do(
                    self._run_job, name
                )
            elif schedule_type == 'weekly':
                schedule.every().monday.at(schedule_time).do(
                    self._run_job, name
                )
            elif schedule_type == 'hourly':
                schedule.every().hour.do(
                    self._run_job, name
                )

        # Start scheduler thread
        def scheduler_loop():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()

        print("✓ Data refresh scheduler started")

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        schedule.clear()
        print("✓ Data refresh scheduler stopped")

    def _run_job(self, name: str):
        """Run a refresh job"""
        job = self.jobs.get(name)
        if not job:
            print(f"⚠️ Job not found: {name}")
            return

        status = self.refresh_status[name]
        status['last_run'] = datetime.now()
        status['status'] = 'running'
        status['run_count'] += 1

        print(f"🔄 Running refresh job: {name}")

        try:
            # Run refresh function
            start_time = time.time()
            job['refresh_func']()
            duration = time.time() - start_time

            # Update status
            status['last_success'] = datetime.now()
            status['status'] = 'success'
            status['last_error'] = None
            self.last_refresh[name] = datetime.now()

            print(f"✅ Refresh job completed: {name} ({duration:.1f}s)")

        except Exception as e:
            # Update status
            status['status'] = 'error'
            status['last_error'] = str(e)

            print(f"❌ Refresh job failed: {name} - {e}")

    def refresh_now(self, name: str) -> bool:
        """
        Trigger immediate refresh

        Args:
            name: Job name

        Returns:
            True if successful
        """
        job = self.jobs.get(name)
        if not job:
            print(f"⚠️ Job not found: {name}")
            return False

        print(f"🔄 Triggering immediate refresh: {name}")

        try:
            job['refresh_func']()
            self.last_refresh[name] = datetime.now()
            self.refresh_status[name]['last_success'] = datetime.now()
            self.refresh_status[name]['status'] = 'success'
            print(f"✅ Immediate refresh completed: {name}")
            return True

        except Exception as e:
            self.refresh_status[name]['status'] = 'error'
            self.refresh_status[name]['last_error'] = str(e)
            print(f"❌ Immediate refresh failed: {name} - {e}")
            return False

    def is_stale(self, name: str) -> bool:
        """
        Check if data source is stale

        Args:
            name: Job name

        Returns:
            True if data is stale
        """
        job = self.jobs.get(name)
        if not job:
            return True  # Unknown source is considered stale

        if name not in self.last_refresh:
            return True  # Never refreshed

        last_refresh_time = self.last_refresh[name]
        max_age = timedelta(hours=job['max_age_hours'])
        age = datetime.now() - last_refresh_time

        return age > max_age

    def get_status(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get refresh status

        Args:
            name: Job name (None for all jobs)

        Returns:
            Status dict
        """
        if name:
            # Single job status
            if name not in self.jobs:
                return {'error': 'Job not found'}

            job = self.jobs[name]
            status = self.refresh_status[name]
            last_refresh_time = self.last_refresh.get(name)

            return {
                'name': name,
                'enabled': job['enabled'],
                'schedule': f"{job['schedule_type']} at {job['schedule_time']}",
                'last_run': status['last_run'].isoformat() if status['last_run'] else None,
                'last_success': status['last_success'].isoformat() if status['last_success'] else None,
                'status': status['status'],
                'error': status['last_error'],
                'run_count': status['run_count'],
                'is_stale': self.is_stale(name),
                'age_hours': (datetime.now() - last_refresh_time).total_seconds() / 3600 if last_refresh_time else None
            }
        else:
            # All jobs status
            return {
                'running': self.running,
                'total_jobs': len(self.jobs),
                'enabled_jobs': sum(1 for j in self.jobs.values() if j['enabled']),
                'jobs': {
                    name: self.get_status(name)
                    for name in self.jobs.keys()
                }
            }

    def get_stale_sources(self) -> List[str]:
        """Get list of stale data sources"""
        return [
            name for name in self.jobs.keys()
            if self.is_stale(name)
        ]


# Common refresh functions for Netflix Mandate Wizard

def refresh_executive_data():
    """Refresh executive profiles from Neo4j"""
    print("  Refreshing executive data...")
    # Would reload from Neo4j
    time.sleep(1)  # Simulate work
    print("  ✓ Executive data refreshed")


def refresh_greenlight_data():
    """Refresh recent greenlights"""
    print("  Refreshing greenlight data...")
    # Would query recent greenlights
    time.sleep(1)  # Simulate work
    print("  ✓ Greenlight data refreshed")


def refresh_mandate_data():
    """Refresh executive mandate data"""
    print("  Refreshing mandate data...")
    # Would fetch latest mandates
    time.sleep(1)  # Simulate work
    print("  ✓ Mandate data refreshed")


def rebuild_vector_index():
    """Rebuild Pinecone vector index"""
    print("  Rebuilding vector index...")
    # Would re-embed and upload to Pinecone
    time.sleep(2)  # Simulate work
    print("  ✓ Vector index rebuilt")


# Global instance
_refresh_scheduler = None


def get_refresh_scheduler() -> DataRefreshScheduler:
    """Get or create global refresh scheduler"""
    global _refresh_scheduler
    if _refresh_scheduler is None:
        _refresh_scheduler = DataRefreshScheduler()

        # Register default jobs
        _refresh_scheduler.register_job(
            name='executive_profiles',
            refresh_func=refresh_executive_data,
            schedule_type='daily',
            schedule_time='03:00',
            max_age_hours=24
        )

        _refresh_scheduler.register_job(
            name='recent_greenlights',
            refresh_func=refresh_greenlight_data,
            schedule_type='daily',
            schedule_time='04:00',
            max_age_hours=12
        )

        _refresh_scheduler.register_job(
            name='executive_mandates',
            refresh_func=refresh_mandate_data,
            schedule_type='weekly',
            schedule_time='02:00',
            max_age_hours=168  # 1 week
        )

        _refresh_scheduler.register_job(
            name='vector_index',
            refresh_func=rebuild_vector_index,
            schedule_type='weekly',
            schedule_time='01:00',
            max_age_hours=168,
            enabled=False  # Disabled by default (expensive operation)
        )

    return _refresh_scheduler


# Example usage
if __name__ == '__main__':
    import json

    scheduler = get_refresh_scheduler()

    print("\nData Refresh Scheduler Example\n" + "="*70)

    # Start scheduler
    scheduler.start()

    # Check status
    print("\nInitial status:")
    status = scheduler.get_status()
    print(json.dumps(status, indent=2, default=str))

    # Trigger immediate refresh
    print("\nTriggering immediate refresh...")
    scheduler.refresh_now('executive_profiles')

    # Check stale sources
    print("\nStale sources:")
    stale = scheduler.get_stale_sources()
    print(f"  {stale}")

    # Stop scheduler
    time.sleep(2)
    scheduler.stop()
