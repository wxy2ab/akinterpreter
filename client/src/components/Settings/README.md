# Settings Page

**English** | [简体中文](./README.zh-CN.md)

The settings page is the configuration center for the web trading system.

## Modules

### Login Settings

- Investor account
- Password
- Saved login information for future automatic login

### CTP Settings

- Trading server address in `IP:port` format
- Market data server address in `IP:port` format
- Broker ID
- App ID
- Authentication code
- Optional default SimNow contract
- Connection testing and input validation

### System Settings

- Theme, refresh, and language preferences
- Trading confirmation, sound notifications, and risk level
- Log level and file logging
- Import, export, and reset actions

### Security Settings

- Automatic logout timeout
- Remember-login preference
- Password change and two-factor authentication placeholders

## Implementation

- `SettingsPage.tsx`: main settings UI
- `settingsService.ts`: API service
- `settings.ts`: TypeScript types

## Backend APIs

- `/api/config/config`
- `/api/config/login-info`
- `/api/config/ctp-config`
- `/api/system/test-ctp`
- `/api/system/status`
- `/api/system/stop-ctp`

## Storage

- Server configuration: `gui/setting.ini`
- Application settings: browser `localStorage`
- SimNow settings: root-level `setting.ini`

## First-Time Setup

1. Enter the investor account and password under Login Settings.
2. Fill in the required CTP connection parameters.
3. Test the connection.
4. Save the configuration before opening trading features.

