# TODO - pyLoad Jellyfin Mover

## Tasks to Implement

### High Priority
- [ ] 

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

- [x] **Multi-select file operations** - Select multiple files for batch operations
  - [x] Added checkboxes to file table for multi-selection
  - [x] Implemented bulk set media type (movie/tvshow) for selected files
  - [x] Implemented bulk set TV show name for selected files
  - [x] Created `/move-batch` API endpoint for batch operations
  - [x] Added batch move functionality to frontend
  - [x] Implemented select all/none functionality
  - [x] Added selection count and bulk action controls
  - [x] Fixed auto-reload issue that disrupted UI state during operations

---

## Notes
- Tasks will be added and prioritized as we discuss improvements
- Mark completed tasks with [x] and move to "Completed Tasks" section
- Include implementation details or requirements in task descriptions