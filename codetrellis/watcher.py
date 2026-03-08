"""
CodeTrellis File Watcher - Watches for file changes and auto-syncs matrix
===================================================================

Similar to Angular's hot reload, this watches the project for changes
and automatically updates the matrix files.
"""

import os
import sys
import time
import json
import hashlib
import threading
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    print("[CodeTrellis] Warning: watchdog not installed. Run: pip install watchdog")


class MatrixSyncHandler(FileSystemEventHandler):
    """
    Handles file system events and triggers matrix updates.
    """

    # File extensions to watch
    WATCH_EXTENSIONS = {
        ".ts", ".py", ".proto", ".json", ".yaml", ".yml",
        ".html", ".scss", ".css"
    }

    # Directories to ignore
    IGNORE_DIRS = {
        "node_modules", "dist", "build", ".git", ".angular",
        ".codetrellis", "__pycache__", ".pytest_cache", "venv", ".venv",
        "coverage", ".nyc_output"
    }

    def __init__(self, project_root: Path, ct_dir: Path, on_change=None):
        self.project_root = project_root
        self.ct_dir = ct_dir
        self.hashes_file = ct_dir / "hashes.json"
        self.hashes = self._load_hashes()
        self.on_change = on_change
        self.pending_updates: Set[Path] = set()
        self._lock = threading.Lock()  # guards pending_updates & last_update
        self.last_update = time.time()
        self.debounce_seconds = 2.0  # Wait 2s to batch rapid-fire changes

    def _load_hashes(self) -> Dict[str, str]:
        """Load file hashes from disk"""
        if self.hashes_file.exists():
            try:
                return json.loads(self.hashes_file.read_text())
            except Exception:
                pass
        return {}

    def _save_hashes(self):
        """Save file hashes to disk"""
        self.hashes_file.parent.mkdir(parents=True, exist_ok=True)
        self.hashes_file.write_text(json.dumps(self.hashes, indent=2))

    def _hash_file(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content"""
        try:
            content = file_path.read_bytes()
            return hashlib.md5(content).hexdigest()[:8]
        except Exception:
            return ""

    def _should_watch(self, path: str) -> bool:
        """Check if file should be watched"""
        path_obj = Path(path)

        # Check extension
        if path_obj.suffix not in self.WATCH_EXTENSIONS:
            return False

        # Check for ignored directories
        for part in path_obj.parts:
            if part in self.IGNORE_DIRS:
                return False

        # Ignore test files
        name = path_obj.name
        if ".spec." in name or ".test." in name:
            return False

        return True

    def on_modified(self, event):
        """Handle file modification"""
        if event.is_directory:
            return

        if not self._should_watch(event.src_path):
            return

        file_path = Path(event.src_path)
        relative_path = str(file_path.relative_to(self.project_root))

        # Calculate new hash
        new_hash = self._hash_file(file_path)
        old_hash = self.hashes.get(relative_path)

        # Skip if hash unchanged
        if new_hash == old_hash:
            return

        print(f"[CodeTrellis] Changed: {relative_path}")

        # Update hash
        self.hashes[relative_path] = new_hash
        self._save_hashes()

        # Add to pending updates (thread-safe)
        with self._lock:
            self.pending_updates.add(file_path)
            self.last_update = time.time()

    def on_created(self, event):
        """Handle file creation"""
        if event.is_directory:
            return

        if not self._should_watch(event.src_path):
            return

        file_path = Path(event.src_path)
        relative_path = str(file_path.relative_to(self.project_root))

        print(f"[CodeTrellis] Created: {relative_path}")

        # Hash new file
        self.hashes[relative_path] = self._hash_file(file_path)
        self._save_hashes()

        # Add to pending updates (thread-safe)
        with self._lock:
            self.pending_updates.add(file_path)
            self.last_update = time.time()

    def on_deleted(self, event):
        """Handle file deletion"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        relative_path = str(file_path.relative_to(self.project_root))

        if relative_path in self.hashes:
            print(f"[CodeTrellis] Deleted: {relative_path}")
            del self.hashes[relative_path]
            self._save_hashes()

            # Trigger full resync (thread-safe)
            with self._lock:
                self.pending_updates.add(Path("__full_resync__"))
                self.last_update = time.time()

    def process_pending(self):
        """Process pending updates after debounce period.

        Thread-safe: atomically snapshots and clears pending_updates
        under a lock, then processes outside the lock so new events
        can continue to accumulate for the next batch.
        """
        # Fast path — no lock needed when empty
        if not self.pending_updates:
            return

        # Atomic snapshot-and-clear under lock
        with self._lock:
            if not self.pending_updates:
                return

            # Wait for debounce
            if time.time() - self.last_update < self.debounce_seconds:
                return

            batch = self.pending_updates.copy()
            self.pending_updates.clear()

        # Process outside the lock (allows new events to accumulate)
        print(f"[CodeTrellis] Processing {len(batch)} changes...")

        if self.on_change:
            if Path("__full_resync__") in batch:
                self.on_change(None)  # Full resync
            else:
                # Pass the full batch as a list — single rebuild
                changed_files: List[Path] = sorted(batch)
                self.on_change(changed_files)


class FileWatcher:
    """
    Watches project directory for changes and updates matrix.

    Usage:
        watcher = FileWatcher("/path/to/project")
        watcher.start()

        # ... watcher runs in background ...

        watcher.stop()
    """

    def __init__(self, project_root: str, on_change=None):
        self.project_root = Path(project_root).resolve()
        self.ct_dir = self.project_root / ".codetrellis"
        self.on_change = on_change
        self.observer = None
        self.handler = None
        self.running = False

    def start(self):
        """Start watching for changes"""
        if not HAS_WATCHDOG:
            print("[CodeTrellis] Error: watchdog not installed")
            print("[CodeTrellis] Install with: pip install watchdog")
            return False

        print(f"[CodeTrellis] Starting file watcher for: {self.project_root}")

        self.handler = MatrixSyncHandler(
            self.project_root,
            self.ct_dir,
            self.on_change
        )

        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            str(self.project_root),
            recursive=True
        )

        self.observer.start()
        self.running = True

        print("[CodeTrellis] Watching for changes... (Ctrl+C to stop)")

        return True

    def run_forever(self):
        """Run watcher forever, processing pending updates"""
        if not self.running:
            if not self.start():
                return

        try:
            while True:
                time.sleep(0.1)
                if self.handler:
                    self.handler.process_pending()
        except KeyboardInterrupt:
            print("\n[CodeTrellis] Stopping watcher...")
            self.stop()

    def stop(self):
        """Stop watching"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        self.running = False
        print("[CodeTrellis] Watcher stopped")

    def get_changed_files(self) -> Set[str]:
        """Get list of files changed since last sync"""
        if self.handler:
            return {str(p) for p in self.handler.pending_updates}
        return set()


def watch_project(project_root: str, on_change=None):
    """Convenience function to start watching"""
    watcher = FileWatcher(project_root, on_change)
    watcher.run_forever()


if __name__ == "__main__":
    # Test watcher
    path = sys.argv[1] if len(sys.argv) > 1 else "."

    def on_file_change(file_paths):
        if file_paths is None:
            print("[CodeTrellis] Would do full resync")
        else:
            for fp in file_paths:
                print(f"[CodeTrellis] Would update matrix for: {fp}")

    watch_project(path, on_file_change)
