"""
Property-based tests for FileManager component using Hypothesis.

**Feature: pdf-to-word-converter**

These tests verify universal properties that should hold across all valid inputs.
"""

import os
import shutil
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck

from app.file_manager import FileManager


@pytest.fixture
def temp_upload_folder():
    """Create a temporary upload folder for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def file_manager(temp_upload_folder):
    """Create a FileManager instance with temporary folder."""
    return FileManager(upload_folder=temp_upload_folder)


class TestFileCleanupProperties:
    """
    Property-based tests for file cleanup functionality.
    
    **Property 28: File Cleanup After Expiration**
    **Validates: Requirements 12.4**
    """
    
    @given(
        num_old_files=st.integers(min_value=0, max_value=10),
        num_new_files=st.integers(min_value=0, max_value=10),
        age_threshold_hours=st.integers(min_value=1, max_value=48),
        old_file_age_hours=st.integers(min_value=25, max_value=100)
    )
    @settings(
        max_examples=100,
        deadline=None
    )
    def test_cleanup_deletes_only_old_files(
        self,
        num_old_files,
        num_new_files,
        age_threshold_hours,
        old_file_age_hours
    ):
        """
        **Property 28: File Cleanup After Expiration**
        **Validates: Requirements 12.4**
        
        For any set of files with various ages, cleanup should delete only
        files older than the threshold while preserving newer files.
        """
        # Ensure old files are actually older than threshold
        assume(old_file_age_hours > age_threshold_hours)
        
        # Create fresh temp directory for this test run
        temp_upload_folder = tempfile.mkdtemp()
        try:
            fm = FileManager(upload_folder=temp_upload_folder)
        
            # Create old job directories
            old_job_ids = []
            for i in range(num_old_files):
                job_id = f"old-job-{i}"
                old_job_ids.append(job_id)
                job_dir = Path(temp_upload_folder) / job_id
                job_dir.mkdir(parents=True)
                (job_dir / "input.pdf").write_text(f"Old file {i}")
                
                # Set modification time to old_file_age_hours ago
                old_time = time.time() - (old_file_age_hours * 3600)
                os.utime(job_dir, (old_time, old_time))
            
            # Create new job directories
            new_job_ids = []
            for i in range(num_new_files):
                job_id = f"new-job-{i}"
                new_job_ids.append(job_id)
                job_dir = Path(temp_upload_folder) / job_id
                job_dir.mkdir(parents=True)
                (job_dir / "input.pdf").write_text(f"New file {i}")
                # Leave with current timestamp (new)
            
            # Run cleanup
            deleted_count = fm.cleanup_old_files(max_age_hours=age_threshold_hours)
            
            # Verify: deleted count should equal number of old files
            assert deleted_count == num_old_files, \
                f"Expected {num_old_files} deletions, got {deleted_count}"
            
            # Verify: old directories should be deleted
            for job_id in old_job_ids:
                job_dir = Path(temp_upload_folder) / job_id
                assert not job_dir.exists(), \
                    f"Old directory {job_id} should be deleted"
            
            # Verify: new directories should still exist
            for job_id in new_job_ids:
                job_dir = Path(temp_upload_folder) / job_id
                assert job_dir.exists(), \
                    f"New directory {job_id} should still exist"
        finally:
            # Cleanup temp directory
            if os.path.exists(temp_upload_folder):
                shutil.rmtree(temp_upload_folder)
    
    @given(
        num_files=st.integers(min_value=0, max_value=20),
        age_threshold_hours=st.integers(min_value=1, max_value=72)
    )
    @settings(
        max_examples=100,
        deadline=None
    )
    def test_cleanup_with_all_new_files_deletes_nothing(
        self,
        num_files,
        age_threshold_hours
    ):
        """
        **Property 28: File Cleanup After Expiration**
        **Validates: Requirements 12.4**
        
        For any set of files that are all newer than the threshold,
        cleanup should delete nothing.
        """
        # Create fresh temp directory for this test run
        temp_upload_folder = tempfile.mkdtemp()
        try:
            fm = FileManager(upload_folder=temp_upload_folder)
        
            # Create new job directories (all recent)
            for i in range(num_files):
                job_id = f"new-job-{i}"
                job_dir = Path(temp_upload_folder) / job_id
                job_dir.mkdir(parents=True)
                (job_dir / "input.pdf").write_text(f"New file {i}")
        
            # Run cleanup
            deleted_count = fm.cleanup_old_files(max_age_hours=age_threshold_hours)
        
            # Verify: nothing should be deleted
            assert deleted_count == 0, \
                f"Expected 0 deletions for all new files, got {deleted_count}"
        
            # Verify: all directories still exist
            for i in range(num_files):
                job_id = f"new-job-{i}"
                job_dir = Path(temp_upload_folder) / job_id
                assert job_dir.exists(), \
                    f"New directory {job_id} should still exist"
        finally:
            # Cleanup temp directory
            if os.path.exists(temp_upload_folder):
                shutil.rmtree(temp_upload_folder)
    
    @given(
        num_files=st.integers(min_value=0, max_value=20),
        age_threshold_hours=st.integers(min_value=1, max_value=72),
        old_file_age_hours=st.integers(min_value=73, max_value=200)
    )
    @settings(
        max_examples=100,
        deadline=None
    )
    def test_cleanup_with_all_old_files_deletes_everything(
        self,
        num_files,
        age_threshold_hours,
        old_file_age_hours
    ):
        """
        **Property 28: File Cleanup After Expiration**
        **Validates: Requirements 12.4**
        
        For any set of files that are all older than the threshold,
        cleanup should delete all of them.
        """
        # Ensure old files are actually older than threshold
        assume(old_file_age_hours > age_threshold_hours)
        
        # Create fresh temp directory for this test run
        temp_upload_folder = tempfile.mkdtemp()
        try:
            fm = FileManager(upload_folder=temp_upload_folder)
        
            # Create old job directories
            for i in range(num_files):
                job_id = f"old-job-{i}"
                job_dir = Path(temp_upload_folder) / job_id
                job_dir.mkdir(parents=True)
                (job_dir / "input.pdf").write_text(f"Old file {i}")
            
                # Set modification time to old_file_age_hours ago
                old_time = time.time() - (old_file_age_hours * 3600)
                os.utime(job_dir, (old_time, old_time))
        
            # Run cleanup
            deleted_count = fm.cleanup_old_files(max_age_hours=age_threshold_hours)
        
            # Verify: all files should be deleted
            assert deleted_count == num_files, \
                f"Expected {num_files} deletions for all old files, got {deleted_count}"
        
            # Verify: no directories should exist
            for i in range(num_files):
                job_id = f"old-job-{i}"
                job_dir = Path(temp_upload_folder) / job_id
                assert not job_dir.exists(), \
                    f"Old directory {job_id} should be deleted"
        finally:
            # Cleanup temp directory
            if os.path.exists(temp_upload_folder):
                shutil.rmtree(temp_upload_folder)
    
    @given(
        age_threshold_hours=st.integers(min_value=1, max_value=72)
    )
    @settings(
        max_examples=50,
        deadline=None
    )
    def test_cleanup_on_empty_directory_returns_zero(
        self,
        age_threshold_hours
    ):
        """
        **Property 28: File Cleanup After Expiration**
        **Validates: Requirements 12.4**
        
        For any threshold, cleanup on an empty directory should return 0.
        """
        # Create fresh temp directory for this test run
        temp_upload_folder = tempfile.mkdtemp()
        try:
            fm = FileManager(upload_folder=temp_upload_folder)
        
            # Run cleanup on empty directory
            deleted_count = fm.cleanup_old_files(max_age_hours=age_threshold_hours)
        
            # Verify: nothing to delete
            assert deleted_count == 0, \
                f"Expected 0 deletions for empty directory, got {deleted_count}"
        finally:
            # Cleanup temp directory
            if os.path.exists(temp_upload_folder):
                shutil.rmtree(temp_upload_folder)
    
    @given(
        num_files=st.integers(min_value=1, max_value=10),
        age_threshold_hours=st.integers(min_value=24, max_value=48)
    )
    @settings(
        max_examples=100,
        deadline=None
    )
    def test_cleanup_is_idempotent(
        self,
        num_files,
        age_threshold_hours
    ):
        """
        **Property 28: File Cleanup After Expiration**
        **Validates: Requirements 12.4**
        
        Running cleanup multiple times should be idempotent - the second
        run should delete nothing if no new old files were created.
        """
        # Create fresh temp directory for this test run
        temp_upload_folder = tempfile.mkdtemp()
        try:
            fm = FileManager(upload_folder=temp_upload_folder)
        
            # Create old job directories
            for i in range(num_files):
                job_id = f"old-job-{i}"
                job_dir = Path(temp_upload_folder) / job_id
                job_dir.mkdir(parents=True)
                (job_dir / "input.pdf").write_text(f"Old file {i}")
            
                # Set modification time to be older than threshold
                old_time = time.time() - ((age_threshold_hours + 10) * 3600)
                os.utime(job_dir, (old_time, old_time))
        
            # First cleanup
            first_deleted = fm.cleanup_old_files(max_age_hours=age_threshold_hours)
        
            # Second cleanup (should delete nothing)
            second_deleted = fm.cleanup_old_files(max_age_hours=age_threshold_hours)
        
            # Verify: first cleanup deleted files, second deleted nothing
            assert first_deleted == num_files, \
                f"First cleanup should delete {num_files} files"
            assert second_deleted == 0, \
                f"Second cleanup should delete 0 files (idempotent)"
        finally:
            # Cleanup temp directory
            if os.path.exists(temp_upload_folder):
                shutil.rmtree(temp_upload_folder)
    
    @given(
        num_files=st.integers(min_value=1, max_value=10),
        file_age_hours=st.integers(min_value=2, max_value=100),
        threshold_hours=st.integers(min_value=1, max_value=99)
    )
    @settings(
        max_examples=100,
        deadline=None
    )
    def test_cleanup_threshold_boundary_behavior(
        self,
        num_files,
        file_age_hours,
        threshold_hours
    ):
        """
        **Property 28: File Cleanup After Expiration**
        **Validates: Requirements 12.4**
        
        Files should be deleted if and only if their age exceeds the threshold.
        This tests the boundary condition.
        """
        # Ensure there's a clear gap to avoid timing issues
        assume(abs(file_age_hours - threshold_hours) > 1)
        
        # Create fresh temp directory for this test run
        temp_upload_folder = tempfile.mkdtemp()
        try:
            fm = FileManager(upload_folder=temp_upload_folder)
        
            # Create job directories with specific age
            for i in range(num_files):
                job_id = f"job-{i}"
                job_dir = Path(temp_upload_folder) / job_id
                job_dir.mkdir(parents=True)
                (job_dir / "input.pdf").write_text(f"File {i}")
            
                # Set modification time to file_age_hours ago
                file_time = time.time() - (file_age_hours * 3600)
                os.utime(job_dir, (file_time, file_time))
        
            # Run cleanup
            deleted_count = fm.cleanup_old_files(max_age_hours=threshold_hours)
        
            # Verify: deleted count matches expectation based on age comparison
            if file_age_hours > threshold_hours:
                # Files are older than threshold, should be deleted
                assert deleted_count == num_files, \
                    f"Files aged {file_age_hours}h should be deleted with threshold {threshold_hours}h"
            else:
                # Files are newer than threshold, should not be deleted
                assert deleted_count == 0, \
                    f"Files aged {file_age_hours}h should not be deleted with threshold {threshold_hours}h"
        finally:
            # Cleanup temp directory
            if os.path.exists(temp_upload_folder):
                shutil.rmtree(temp_upload_folder)
