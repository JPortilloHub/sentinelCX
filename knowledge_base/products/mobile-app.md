# Mobile App Guide

## Supported Platforms
- **iOS**: Version 18.0 and above. Available on App Store.
- **Android**: Version 13 and above. Available on Google Play.

## Features
- View and respond to conversations
- Push notifications for new messages and assignments
- Quick reply templates
- Offline mode for viewing cached conversations

## Push Notifications
Push notifications require:
1. Notification permissions enabled in device settings
2. Notification preferences enabled in-app (Settings → Notifications)
3. A valid push token registered with our servers

### Troubleshooting Notifications
If notifications aren't working:
1. Check device notification settings
2. Check in-app notification preferences
3. Try logging out and back in to refresh the push token
4. Ensure you're on the latest app version
5. For iOS: Check that Background App Refresh is enabled

## Known Issues (Current Version)
- iOS 18.2: Push notification token refresh issue after system update. Fix in progress, expected in next release.
- Android: Battery optimization may delay notifications. Add app to battery optimization exceptions.

## Data Import Tool
The mobile app supports importing data via:
- **CSV files**: Comma-separated values with headers
- **JSON files**: Array of objects matching our schema
- **Excel files (.xlsx)**: First sheet only, with headers in row 1
