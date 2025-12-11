## Functional Requirements
1. Send notification (support both sending single (`POST /api/v1/notifications`)
2. batch (`POST /api/v1/notifications/batch`))
3. Query notifications filter by user, status, time_range (`GET /api/v1/notifications`)



## Non-functional requirements
1. Extensibility: Easy to add new notify channel: Zalo, Telegram, etc
2. Scalability: can scale out based on number of retention messages
3. Reliability: can retry sending notification if failed
