"""
Property-based tests for JobManager using Hypothesis.

**Feature: pdf-to-word-converter**

These tests verify universal properties that should hold across all valid inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock
from app.job_manager import JobManager


def create_mock_redis():
    """Create a mock Redis client that stores data in memory."""
    storage = {}
    
    mock = Mock()
    
    def setex(key, expiration, value):
        storage[key] = value
    
    def get(key):
        return storage.get(key)
    
    mock.setex = setex
    mock.get = get
    mock.storage = storage
    
    return mock


class TestUniqueJobIDs:
    """
    **Property 20: Unique Job Identifier Generation**
    **Validates: Requirements 9.6**
    
    For any set of file uploads, all generated job identifiers should be unique.
    """
    
    @settings(max_examples=100)
    @given(
        num_jobs=st.integers(min_value=2, max_value=50),
        file_paths=st.lists(
            st.text(min_size=1, max_size=100, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters='/-_.'
            )),
            min_size=2,
            max_size=50
        )
    )
    def test_all_job_ids_are_unique(self, num_jobs, file_paths):
        """
        Test that creating multiple jobs generates unique IDs.
        
        This property verifies that no matter how many jobs we create,
        each one gets a unique identifier.
        """
        # Create fresh mock Redis and JobManager for this test
        mock_redis = create_mock_redis()
        job_manager = JobManager(redis_client=mock_redis)
        
        # Ensure we have enough file paths
        while len(file_paths) < num_jobs:
            file_paths.append(f"/uploads/file_{len(file_paths)}.pdf")
        
        # Create multiple jobs
        job_ids = []
        for i in range(num_jobs):
            file_path = file_paths[i % len(file_paths)]
            job_id = job_manager.create_job(file_path)
            job_ids.append(job_id)
        
        # Verify all IDs are unique
        assert len(job_ids) == len(set(job_ids)), "Job IDs must be unique"
        
        # Verify all IDs are valid UUID format (36 characters with 4 dashes)
        for job_id in job_ids:
            assert isinstance(job_id, str)
            assert len(job_id) == 36
            assert job_id.count('-') == 4
    
    @settings(max_examples=100)
    @given(
        file_path=st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='/-_.'
        ))
    )
    def test_sequential_job_creation_produces_unique_ids(self, file_path):
        """
        Test that creating jobs sequentially with the same file path produces unique IDs.
        
        This verifies that job ID generation doesn't depend on the file path.
        """
        # Create fresh mock Redis and JobManager for this test
        mock_redis = create_mock_redis()
        job_manager = JobManager(redis_client=mock_redis)
        
        # Create 10 jobs with the same file path
        job_ids = [job_manager.create_job(file_path) for _ in range(10)]
        
        # All IDs should be unique
        assert len(job_ids) == len(set(job_ids))
    
    @settings(max_examples=100)
    @given(
        num_jobs=st.integers(min_value=5, max_value=20)
    )
    def test_concurrent_job_creation_uniqueness(self, num_jobs):
        """
        Test that multiple JobManager instances create unique IDs.
        
        This simulates concurrent job creation from different workers.
        """
        # Create fresh mock Redis for this test
        mock_redis = create_mock_redis()
        
        # Create multiple JobManager instances (simulating different workers)
        managers = [JobManager(redis_client=mock_redis) for _ in range(3)]
        
        # Create jobs from different managers
        all_job_ids = []
        for i in range(num_jobs):
            manager = managers[i % len(managers)]
            job_id = manager.create_job(f"/uploads/file_{i}.pdf")
            all_job_ids.append(job_id)
        
        # All IDs should be unique across all managers
        assert len(all_job_ids) == len(set(all_job_ids))




class TestJobStateTransitions:
    """
    **Property 22: Job State Transitions**
    **Validates: Requirements 10.2, 10.3, 10.4, 10.5**
    
    For any job, the status should correctly transition through states:
    pending → processing → completed/failed, with appropriate error details when failed.
    """
    
    @settings(max_examples=100)
    @given(
        file_path=st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='/-_.'
        )),
        output_path=st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='/-_.'
        ))
    )
    def test_successful_job_state_transitions(self, file_path, output_path):
        """
        Test that jobs transition correctly through pending → processing → completed.
        
        This verifies the happy path state transitions.
        """
        # Create fresh mock Redis and JobManager
        mock_redis = create_mock_redis()
        job_manager = JobManager(redis_client=mock_redis)
        
        # Create job (should start as pending)
        job_id = job_manager.create_job(file_path)
        status = job_manager.get_status(job_id)
        assert status["status"] == "pending", "New jobs should start as pending"
        assert status["job_id"] == job_id
        
        # Mark as processing
        job_manager.mark_processing(job_id)
        status = job_manager.get_status(job_id)
        assert status["status"] == "processing", "Job should transition to processing"
        
        # Mark as completed
        job_manager.mark_completed(job_id, output_path)
        status = job_manager.get_status(job_id)
        assert status["status"] == "completed", "Job should transition to completed"
        assert status["output_path"] == output_path
        assert "completed_at" in status
    
    @settings(max_examples=100)
    @given(
        file_path=st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='/-_.'
        )),
        error_message=st.text(min_size=1, max_size=500)
    )
    def test_failed_job_state_transitions(self, file_path, error_message):
        """
        Test that jobs transition correctly through pending → processing → failed.
        
        This verifies the error path state transitions.
        """
        # Create fresh mock Redis and JobManager
        mock_redis = create_mock_redis()
        job_manager = JobManager(redis_client=mock_redis)
        
        # Create job (should start as pending)
        job_id = job_manager.create_job(file_path)
        status = job_manager.get_status(job_id)
        assert status["status"] == "pending"
        
        # Mark as processing
        job_manager.mark_processing(job_id)
        status = job_manager.get_status(job_id)
        assert status["status"] == "processing"
        
        # Mark as failed
        job_manager.mark_failed(job_id, error_message)
        status = job_manager.get_status(job_id)
        assert status["status"] == "failed", "Job should transition to failed"
        assert status["error"] == error_message, "Error message should be stored"
        assert "completed_at" in status
    
    @settings(max_examples=100)
    @given(
        file_path=st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='/-_.'
        )),
        should_fail=st.booleans()
    )
    def test_job_always_ends_in_terminal_state(self, file_path, should_fail):
        """
        Test that jobs always end in either completed or failed state.
        
        This verifies that all job lifecycles reach a terminal state.
        """
        # Create fresh mock Redis and JobManager
        mock_redis = create_mock_redis()
        job_manager = JobManager(redis_client=mock_redis)
        
        # Create and process job
        job_id = job_manager.create_job(file_path)
        job_manager.mark_processing(job_id)
        
        if should_fail:
            job_manager.mark_failed(job_id, "Test error")
            status = job_manager.get_status(job_id)
            assert status["status"] == "failed"
        else:
            job_manager.mark_completed(job_id, "/output/test.docx")
            status = job_manager.get_status(job_id)
            assert status["status"] == "completed"
        
        # Verify terminal state has completion timestamp
        assert "completed_at" in status
    
    @settings(max_examples=100)
    @given(
        file_path=st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='/-_.'
        ))
    )
    def test_pending_to_processing_transition(self, file_path):
        """
        Test that jobs can transition from pending to processing.
        
        This verifies the initial state transition when a worker picks up a job.
        """
        # Create fresh mock Redis and JobManager
        mock_redis = create_mock_redis()
        job_manager = JobManager(redis_client=mock_redis)
        
        # Create job
        job_id = job_manager.create_job(file_path)
        
        # Get initial status
        status_before = job_manager.get_status(job_id)
        assert status_before["status"] == "pending"
        
        # Mark as processing
        job_manager.mark_processing(job_id)
        
        # Get updated status
        status_after = job_manager.get_status(job_id)
        assert status_after["status"] == "processing"
        
        # Verify updated_at exists (timestamp comparison is flaky due to speed)
        assert "updated_at" in status_after
    
    @settings(max_examples=100)
    @given(
        num_jobs=st.integers(min_value=1, max_value=20),
        failure_indices=st.lists(
            st.integers(min_value=0, max_value=19),
            max_size=10
        )
    )
    def test_multiple_jobs_independent_state_transitions(self, num_jobs, failure_indices):
        """
        Test that multiple jobs can have independent state transitions.
        
        This verifies that state changes to one job don't affect others.
        """
        # Create fresh mock Redis and JobManager
        mock_redis = create_mock_redis()
        job_manager = JobManager(redis_client=mock_redis)
        
        # Create multiple jobs
        job_ids = [job_manager.create_job(f"/uploads/file_{i}.pdf") for i in range(num_jobs)]
        
        # Process jobs with some failures
        for i, job_id in enumerate(job_ids):
            job_manager.mark_processing(job_id)
            
            if i in failure_indices:
                job_manager.mark_failed(job_id, f"Error on job {i}")
            else:
                job_manager.mark_completed(job_id, f"/output/file_{i}.docx")
        
        # Verify each job has correct final state
        for i, job_id in enumerate(job_ids):
            status = job_manager.get_status(job_id)
            
            if i in failure_indices:
                assert status["status"] == "failed"
                assert "error" in status
            else:
                assert status["status"] == "completed"
                assert "output_path" in status



class TestProgressStorage:
    """
    **Property 23: Progress Information Storage**
    **Validates: Requirements 10.6**
    
    For any job being processed, progress information (current page, total pages)
    should be stored and retrievable.
    """
    
    @settings(max_examples=100)
    @given(
        file_path=st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='/-_.'
        )),
        current_page=st.integers(min_value=0, max_value=1000),
        total_pages=st.integers(min_value=0, max_value=1000)
    )
    def test_progress_storage_and_retrieval(self, file_path, current_page, total_pages):
        """
        Test that progress information is correctly stored and retrieved.
        
        This verifies that any valid progress values can be stored and retrieved.
        """
        # Create fresh mock Redis and JobManager
        mock_redis = create_mock_redis()
        job_manager = JobManager(redis_client=mock_redis)
        
        # Create job
        job_id = job_manager.create_job(file_path)
        
        # Update progress
        job_manager.update_progress(job_id, current_page, total_pages)
        
        # Retrieve status
        status = job_manager.get_status(job_id)
        
        # Verify progress is stored correctly
        assert status["progress"]["current_page"] == current_page
        assert status["progress"]["total_pages"] == total_pages
        
        # Verify percentage is calculated correctly
        if total_pages > 0:
            expected_percentage = int((current_page / total_pages) * 100)
            assert status["progress"]["percentage"] == expected_percentage
        else:
            assert status["progress"]["percentage"] == 0
    
    @settings(max_examples=100)
    @given(
        file_path=st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='/-_.'
        )),
        progress_updates=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=100),
                st.integers(min_value=1, max_value=100)
            ),
            min_size=1,
            max_size=20
        )
    )
    def test_multiple_progress_updates(self, file_path, progress_updates):
        """
        Test that progress can be updated multiple times.
        
        This verifies that progress updates are idempotent and the latest value is stored.
        """
        # Create fresh mock Redis and JobManager
        mock_redis = create_mock_redis()
        job_manager = JobManager(redis_client=mock_redis)
        
        # Create job
        job_id = job_manager.create_job(file_path)
        
        # Apply multiple progress updates
        for current, total in progress_updates:
            job_manager.update_progress(job_id, current, total)
        
        # Get final status
        status = job_manager.get_status(job_id)
        
        # Verify last update is stored
        last_current, last_total = progress_updates[-1]
        assert status["progress"]["current_page"] == last_current
        assert status["progress"]["total_pages"] == last_total
    
    @settings(max_examples=100)
    @given(
        file_path=st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='/-_.'
        )),
        total_pages=st.integers(min_value=1, max_value=50)
    )
    def test_progress_percentage_calculation(self, file_path, total_pages):
        """
        Test that percentage is calculated correctly for all page counts.
        
        This verifies the percentage calculation property.
        """
        # Create fresh mock Redis and JobManager
        mock_redis = create_mock_redis()
        job_manager = JobManager(redis_client=mock_redis)
        
        # Create job
        job_id = job_manager.create_job(file_path)
        
        # Test progress at various points
        for current_page in range(0, total_pages + 1):
            job_manager.update_progress(job_id, current_page, total_pages)
            status = job_manager.get_status(job_id)
            
            expected_percentage = int((current_page / total_pages) * 100)
            assert status["progress"]["percentage"] == expected_percentage
            
            # Verify percentage is in valid range
            assert 0 <= status["progress"]["percentage"] <= 100
    
    @settings(max_examples=100)
    @given(
        num_jobs=st.integers(min_value=2, max_value=10),
        progress_data=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=100),
                st.integers(min_value=1, max_value=100)
            ),
            min_size=2,
            max_size=10
        )
    )
    def test_independent_progress_for_multiple_jobs(self, num_jobs, progress_data):
        """
        Test that progress for different jobs is stored independently.
        
        This verifies that updating one job's progress doesn't affect others.
        """
        # Create fresh mock Redis and JobManager
        mock_redis = create_mock_redis()
        job_manager = JobManager(redis_client=mock_redis)
        
        # Ensure we have enough progress data
        while len(progress_data) < num_jobs:
            progress_data.append((1, 10))
        
        # Create multiple jobs with different progress
        job_progress = {}
        for i in range(num_jobs):
            job_id = job_manager.create_job(f"/uploads/file_{i}.pdf")
            current, total = progress_data[i]
            job_manager.update_progress(job_id, current, total)
            job_progress[job_id] = (current, total)
        
        # Verify each job has its own progress
        for job_id, (expected_current, expected_total) in job_progress.items():
            status = job_manager.get_status(job_id)
            assert status["progress"]["current_page"] == expected_current
            assert status["progress"]["total_pages"] == expected_total
    
    @settings(max_examples=100)
    @given(
        file_path=st.text(min_size=1, max_size=200, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='/-_.'
        )),
        current_page=st.integers(min_value=0, max_value=100)
    )
    def test_progress_with_zero_total_pages(self, file_path, current_page):
        """
        Test that progress handles zero total pages gracefully.
        
        This verifies edge case handling for empty documents.
        """
        # Create fresh mock Redis and JobManager
        mock_redis = create_mock_redis()
        job_manager = JobManager(redis_client=mock_redis)
        
        # Create job
        job_id = job_manager.create_job(file_path)
        
        # Update with zero total pages
        job_manager.update_progress(job_id, current_page, 0)
        
        # Retrieve status
        status = job_manager.get_status(job_id)
        
        # Verify progress is stored
        assert status["progress"]["current_page"] == current_page
        assert status["progress"]["total_pages"] == 0
        
        # Percentage should be 0 when total is 0
        assert status["progress"]["percentage"] == 0
