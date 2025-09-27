import firebase_admin
from firebase_admin import credentials, messaging

print("🔍 Step 1: Loading service account JSON...")
cred = credentials.Certificate("serviceAccountKey.json")
print("✅ Service account JSON loaded.")

print("🔍 Step 2: Initializing Firebase Admin SDK...")
firebase_admin.initialize_app(cred)
print("✅ Firebase Admin SDK initialized.")

# Replace this with a real FCM device token you registered
registration_token = "c3x3HTFMQnKBCdFcDJlE22:APA91bGfBOmZzuXG6rQNOZ87ykUkWMmYssn8WHSAft2QxVFTw0G-8op1IqsASK_WCni0lrjHDKYBH3-6Argwh9I0FiaSGPQTdzjln1k3d7-fjAZF0ZQbYAg"
print(f"🔍 Step 3: Using device token -> {registration_token}")

print("🔍 Step 4: Building FCM message...")
message = messaging.Message(
    notification=messaging.Notification(
        title="🚨 Test Alert",
        body="Hello from Firebase Cloud Messaging!"
    ),
    token=registration_token,
)
print("✅ Message object created.")

print("🔍 Step 5: Sending message via FCM...")
try:
    response = messaging.send(message)
    print("✅ Successfully sent message:", response)
except Exception as e:
    print("❌ Error sending message:", e)
