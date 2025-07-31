# TODO - pyLoad Jellyfin Mover

## Tasks to Implement

### High Priority
- [ ] **Persistent file move progress tracking** - Track file move operations across browser sessions/reloads
  - Add server-side status storage (in-memory dict or database)
  - Track states: pending, in-progress, completed, failed
  - **Show progress as percentage** (0-100%) with progress bar UI
  - Update frontend to check/display persistent status on page load
  - Handle status cleanup for completed/failed operations

- [ ] **Multi-select file operations** - Select multiple files for batch operations
  - Add checkboxes to file table for multi-selection
  - Bulk set media type (movie/tvshow) for selected files
  - Bulk set TV show name for selected files
  - Batch move operation for all selected files
  - Select all/none functionality
  - Show selection count and bulk action controls 

### Medium Priority
- [ ] 

### Low Priority
- [ ] 

## Completed Tasks
- [x] Created initial CLAUDE.md documentation
- [x] Set up TODO.md for task tracking
- [x] **Persistent file move progress tracking** - Track file move operations across browser sessions/reloads
  - [x] Added server-side status storage (in-memory dict with threading.Lock)
  - [x] Created `/status` and `/status/<filename>` API endpoints
  - [x] Implemented progress tracking with percentage (0-100%) and progress bars
  - [x] Updated frontend to poll for status updates every 2 seconds
  - [x] Added threaded file operations for non-blocking moves
  - [x] Status persists across browser refreshes
  - [x] Automatic cleanup of old operations after 1 hour

---

## Notes
- Tasks will be added and prioritized as we discuss improvements
- Mark completed tasks with [x] and move to "Completed Tasks" section
- Include implementation details or requirements in task descriptions