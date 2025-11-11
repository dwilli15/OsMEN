# API Integration Setup Guide

Complete guide for setting up real API integrations in OsMEN v1.6.0.

## Table of Contents
1. [Android Health Connect](#android-health-connect)
2. [Google Fit API](#google-fit-api)
3. [Firebase Cloud Messaging (Push Notifications)](#firebase-cloud-messaging)
4. [Testing Integrations](#testing-integrations)

---

## Android Health Connect

### Overview
Android Health Connect provides access to health and fitness data on Android devices.

### Prerequisites
- Android device (Android 14+ recommended)
- Android Health Connect app installed
- Python development environment

### Setup Steps

#### 1. Install Android Health Connect App
```bash
# Install from Google Play Store or
adb install health-connect.apk
```

#### 2. Configure Android Manifest
Add permissions to your Android app's `AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.health.READ_SLEEP" />
<uses-permission android:name="android.permission.health.READ_STEPS" />
<uses-permission android:name="android.permission.health.READ_DISTANCE" />
<uses-permission android:name="android.permission.health.READ_HEART_RATE" />
```

#### 3. Install Python SDK
```bash
# Note: This is a hypothetical package - actual implementation may vary
pip install android-health-connect
```

#### 4. Initialize in Code
```python
from health_integration.health_data import HealthDataIntegrator

integrator = HealthDataIntegrator()

# Connect with your app's package name
success = integrator.connect_android_health(package_name="com.yourapp.osmen")

if success:
    # Fetch sleep data
    sleep_data = integrator.fetch_sleep_data(days=7)
    print(f"Found {len(sleep_data)} sleep records")
```

### Data Available
- Sleep duration and quality
- Sleep stages (light, deep, REM, awake)
- Steps and activity
- Heart rate
- Distance traveled

### Fallback
If Android Health Connect is not available, the system automatically falls back to manual data entry.

---

## Google Fit API

### Overview
Google Fit provides access to fitness and wellness data across Android, iOS, and web.

### Prerequisites
- Google Cloud Platform account
- OAuth 2.0 credentials
- Google Fit API enabled

### Setup Steps

#### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Navigate to "APIs & Services" > "Library"
4. Search for "Fitness API" and enable it

#### 2. Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Choose application type:
   - **Desktop app** for local testing
   - **Android** for mobile app
   - **Web application** for web app
4. Download the credentials JSON file
5. Save as `google_fit_credentials.json` in your project root

#### 3. Configure Scopes
Required OAuth scopes:
- `https://www.googleapis.com/auth/fitness.sleep.read`
- `https://www.googleapis.com/auth/fitness.activity.read`

#### 4. Install Dependencies
```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

#### 5. Initialize in Code
```python
from health_integration.health_data import HealthDataIntegrator

integrator = HealthDataIntegrator()

# Connect (will open browser for OAuth on first run)
success = integrator.connect_google_fit(
    credentials_path="google_fit_credentials.json",
    token_path="google_fit_token.json"
)

if success:
    # Fetch sleep data
    sleep_data = integrator.fetch_sleep_data(days=7)
    
    # Fetch activity data
    activity_data = integrator.fetch_activity_data(days=7)
```

### Environment Variables
```bash
export GOOGLE_FIT_CREDENTIALS=/path/to/google_fit_credentials.json
export GOOGLE_FIT_TOKEN=/path/to/google_fit_token.json
```

### Data Available
- Sleep sessions and quality
- Steps, distance, calories
- Heart rate
- Weight and nutrition
- Activity types (running, cycling, etc.)

### Token Management
- First run: Opens browser for OAuth authorization
- Token saved to `google_fit_token.json`
- Automatic refresh when expired
- Valid for 1 hour, refresh token valid indefinitely

---

## Firebase Cloud Messaging

### Overview
Firebase Cloud Messaging (FCM) enables push notifications to Android, iOS, and web clients.

### Prerequisites
- Firebase project
- Firebase Admin SDK credentials
- Device FCM tokens

### Setup Steps

#### 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click "Add project"
3. Follow the setup wizard
4. Enable Cloud Messaging

#### 2. Download Service Account Credentials
1. Go to Project Settings > Service Accounts
2. Click "Generate new private key"
3. Save as `firebase_credentials.json`
4. **IMPORTANT**: Keep this file secure, don't commit to git

#### 3. Install Firebase Admin SDK
```bash
pip install firebase-admin
```

#### 4. Configure Environment
```bash
export FIREBASE_CREDENTIALS=/path/to/firebase_credentials.json
export FCM_DEVICE_TOKENS=/path/to/.copilot/fcm_device_tokens.json
```

#### 5. Register Device Tokens
```python
from reminders.multi_channel_notifier import MultiChannelNotifier

notifier = MultiChannelNotifier()

# Add device token (obtained from mobile app)
notifier.add_device_token("your-fcm-device-token-here")
```

#### 6. Send Push Notifications
```python
reminder = {
    "id": "task-123",
    "task_title": "Complete assignment",
    "due_date": "2025-11-15",
    "escalation_level": "urgent"
}

# Send to all registered devices
success = notifier._send_push_notification(reminder)
```

### Getting Device Tokens

#### Android (Kotlin)
```kotlin
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val token = task.result
        // Send token to your backend
        Log.d("FCM", "Token: $token")
    }
}
```

#### iOS (Swift)
```swift
import FirebaseMessaging

Messaging.messaging().token { token, error in
    if let error = error {
        print("Error fetching FCM token: \(error)")
    } else if let token = token {
        print("FCM token: \(token)")
        // Send token to your backend
    }
}
```

#### Web (JavaScript)
```javascript
import { getMessaging, getToken } from "firebase/messaging";

const messaging = getMessaging();
getToken(messaging, { vapidKey: 'YOUR_VAPID_KEY' })
  .then((currentToken) => {
    if (currentToken) {
      console.log('FCM token:', currentToken);
      // Send token to your backend
    }
  });
```

### Notification Payload Structure
```json
{
  "title": "🔔 Task Reminder",
  "body": "Complete assignment - Due: 2025-11-15",
  "data": {
    "task_id": "task-123",
    "task_title": "Complete assignment",
    "escalation_level": "urgent",
    "click_action": "OPEN_TASK"
  },
  "android": {
    "priority": "high",
    "notification": {
      "sound": "default",
      "color": "#FF6B35"
    }
  },
  "apns": {
    "payload": {
      "aps": {
        "sound": "default",
        "badge": 1
      }
    }
  }
}
```

### Token Management
- Tokens stored in `.copilot/fcm_device_tokens.json`
- Invalid tokens automatically removed
- Support for multiple devices per user
- Automatic retry on failure

---

## Testing Integrations

### Health Data Integration Test

```python
from health_integration.health_data import HealthDataIntegrator

# Initialize
integrator = HealthDataIntegrator()

# Test manual entry (always works)
integrator.record_manual_sleep(7.5, "good")
integrator.record_manual_energy(8, "morning")

# Test Android Health Connect (if available)
if integrator.connect_android_health():
    sleep = integrator.fetch_sleep_data(days=3)
    print(f"Sleep records: {len(sleep)}")

# Test Google Fit (if configured)
if integrator.connect_google_fit():
    sleep = integrator.fetch_sleep_data(days=3)
    activity = integrator.fetch_activity_data(days=3)
    print(f"Sleep: {len(sleep)}, Activity: {len(activity)}")
```

### Push Notification Test

```python
from reminders.multi_channel_notifier import MultiChannelNotifier

# Initialize
notifier = MultiChannelNotifier()

# Add test device token
notifier.add_device_token("test-fcm-token-12345")

# Send test notification
test_reminder = {
    "id": "test-1",
    "task_title": "Test Notification",
    "escalation_level": "moderate"
}

result = notifier.send_notification(test_reminder, channels=['notification'])
print(f"Push notification sent: {result.get('notification', False)}")
```

### Integration Status Check

```python
from health_integration.health_data import HealthDataIntegrator
from reminders.multi_channel_notifier import MultiChannelNotifier

integrator = HealthDataIntegrator()
notifier = MultiChannelNotifier()

print("Health Integration Status:")
print(f"  Android Health: {integrator.sources['android_health']}")
print(f"  Google Fit: {integrator.sources['google_fit']}")
print(f"  Manual Entry: {integrator.sources['manual_entry']}")

print("\nNotification Status:")
print(f"  Firebase: {notifier.firebase_initialized}")
print(f"  Devices: {len(notifier.device_tokens)}")
print(f"  Email: {'configured' if notifier.smtp_config['username'] else 'not configured'}")
```

---

## Troubleshooting

### Android Health Connect
- **Error: "SDK not available"**
  - Solution: Install `android-health-connect` package
  - Fallback: Use manual data entry

- **Error: "Permission denied"**
  - Solution: Grant permissions in Android settings
  - Check AndroidManifest.xml has correct permissions

### Google Fit
- **Error: "Credentials file not found"**
  - Solution: Download OAuth credentials from Google Cloud Console
  - Place in project root or set `GOOGLE_FIT_CREDENTIALS` env var

- **Error: "Invalid grant"**
  - Solution: Delete `google_fit_token.json` and re-authenticate
  - Check OAuth scopes are correct

### Firebase Cloud Messaging
- **Error: "Firebase credentials not found"**
  - Solution: Download service account key from Firebase Console
  - Set `FIREBASE_CREDENTIALS` environment variable

- **Error: "No device tokens"**
  - Solution: Register at least one device token using `add_device_token()`
  - Get tokens from mobile app using Firebase SDK

- **Error: "Registration token not registered"**
  - Solution: Token expired or app uninstalled
  - System automatically removes invalid tokens

---

## Security Best Practices

### Credentials Management
1. **Never commit credentials to git**
   ```bash
   # Add to .gitignore
   firebase_credentials.json
   google_fit_credentials.json
   google_fit_token.json
   .copilot/fcm_device_tokens.json
   .copilot/health_data.json
   ```

2. **Use environment variables**
   ```bash
   # .env file (also in .gitignore)
   FIREBASE_CREDENTIALS=/secure/path/firebase_credentials.json
   GOOGLE_FIT_CREDENTIALS=/secure/path/google_fit_credentials.json
   SMTP_USERNAME=your-email@example.com
   SMTP_PASSWORD=your-app-password
   ```

3. **Encrypt sensitive data**
   - Use encrypted storage for tokens
   - Rotate credentials regularly
   - Implement key management system

### API Security
- Use HTTPS for all API calls
- Implement rate limiting
- Validate all inputs
- Log security events
- Monitor for suspicious activity

### User Privacy
- Request minimum necessary permissions
- Explain data usage to users
- Implement data retention policies
- Allow users to delete their data
- Comply with GDPR/CCPA regulations

---

## Support

For issues or questions:
1. Check this documentation
2. Review error messages carefully
3. Test with manual fallback mode
4. Check API console logs
5. Open an issue on GitHub

---

**Last Updated**: 2025-11-10
**Version**: v1.6.0
