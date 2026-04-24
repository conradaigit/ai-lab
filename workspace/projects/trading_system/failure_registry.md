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

## FR-0002
### Title
Polygon/Massive probe ambiguity from transient 429 rate limits

### What failed
Initial multi-endpoint history-depth probing produced 429 responses for some windows, which temporarily obscured entitlement-vs-access interpretation.

### Detection
Endpoints that previously returned 200/403 intermittently returned 429 with a per-minute limit message.

### Current mitigation
Re-run only ambiguous windows with paced requests and classify results only after retry stabilization.

### Status
Mitigated
