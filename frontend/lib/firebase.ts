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
let app: FirebaseApp;
let auth: Auth;
let db: Firestore;

if (!getApps().length) {
  console.log("🔥 Initializing Firebase...");
  console.log("  Project ID:", firebaseConfig.projectId);

  app = initializeApp(firebaseConfig);
  auth = getAuth(app);

  // Inizializza Firestore con cache locale
  db = initializeFirestore(app, {
    localCache: persistentLocalCache({
      tabManager: persistentMultipleTabManager(),
    }),
  });

  console.log("✅ Firebase initialized");
  console.log("  Firestore database:", db.app.options.projectId);
} else {
  app = getApps()[0];
  auth = getAuth(app);
  db = getFirestore(app);
}

export { app, auth, db };
