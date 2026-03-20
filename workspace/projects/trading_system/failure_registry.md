# trading_system failure registry

## FR-0001
### Title
Unreliable paste behavior in the old terminal flow

### What failed
Large multiline pastes in the earlier terminal workflow caused corrupted commands and partial file writes.

### Detection
Unexpected shell control characters, malformed commands, and incomplete heredoc/file writes.

### Current mitigation
Use Windows Terminal for Ubuntu/WSL and prefer one-file-at-a-time writes.

### Status
Mitigated
