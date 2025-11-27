// Firebase configuration and initialization
import { initializeApp, getApps, FirebaseApp } from "firebase/app";
import { getAuth, Auth } from "firebase/auth";
import {
  getFirestore,
  Firestore,
  initializeFirestore,
  persistentLocalCache,
  persistentMultipleTabManager,
} from "firebase/firestore";
import { envConfig } from "./env.config";

// Firebase configuration from centralized env config
// This approach works around Turbopack issues with process.env
const firebaseConfig = envConfig.firebase;

// Validate configuration
if (
  !firebaseConfig.apiKey ||
  !firebaseConfig.authDomain ||
  !firebaseConfig.projectId
) {
  throw new Error(
    "Firebase configuration is missing. Please ensure all required environment variables are set in .env.local"
  );
}

// Initialize Firebase (singleton pattern)
const app: FirebaseApp = !getApps().length
  ? initializeApp(firebaseConfig)
  : getApps()[0];

const auth: Auth = getAuth(app);

const db: Firestore = !getApps().length
  ? initializeFirestore(app, {
      localCache: persistentLocalCache({
        tabManager: persistentMultipleTabManager(),
      }),
    })
  : getFirestore(app);

if (!getApps().length) {
  console.log("🔥 Initializing Firebase...");
  console.log("  Project ID:", firebaseConfig.projectId);
  console.log("✅ Firebase initialized");
  console.log("  Firestore database:", db.app.options.projectId);
}

export { app, auth, db };
