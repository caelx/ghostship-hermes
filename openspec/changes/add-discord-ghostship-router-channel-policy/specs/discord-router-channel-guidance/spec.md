## ADDED Requirements

### Requirement: Configured router channel sends advisory guidance for non-router sessions
The managed Hermes runtime SHALL treat `GHOSTSHIP_ROUTER_CHANNEL` as a Discord channel that receives advisory guidance when the active session is not using the named `ghostship-router` custom provider with a router-exposed model id.

#### Scenario: Warning appears when a normal message starts under a non-router session
- **WHEN** a Discord message begins agent execution in the channel identified by `GHOSTSHIP_ROUTER_CHANNEL`
- **AND** the active session model is not `ghostship-router` with a currently exposed router model id
- **THEN** the runtime sends an advisory warning message in that channel
- **AND** the warning does not require modifying gateway dispatch behavior or blocking the request

#### Scenario: Warning appears after reset in the configured router channel
- **WHEN** a user runs `/reset` in the channel identified by `GHOSTSHIP_ROUTER_CHANNEL`
- **AND** the reset leaves the session on the managed default model instead of a `ghostship-router` session model
- **THEN** the runtime sends the same advisory warning message in that channel
- **AND** the warning tells the user to switch back with `/model`

### Requirement: Router channel warning is bold and copy-paste oriented
The advisory warning for `GHOSTSHIP_ROUTER_CHANNEL` SHALL render a visually prominent bold heading and SHALL include one full `/model custom:ghostship-router:<model>` command for every currently exposed router model id.

#### Scenario: Warning renders live router-backed switch commands
- **WHEN** the runtime formats the router-channel warning
- **THEN** it queries or uses a recent cached view of the router's current `/v1/models` inventory
- **AND** it renders one full `/model custom:ghostship-router:<model>` command per exposed router model id
- **AND** the warning does not collapse the guidance to only a partial subset of the available router model ids

#### Scenario: Warning includes bold visual emphasis
- **WHEN** the runtime sends the router-channel warning in Discord
- **THEN** the message includes a bold warning heading
- **AND** the switch commands are formatted so they can be copied directly from the Discord message
