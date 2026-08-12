// Firebase configuration and initialization
// Uses lazy initialization so this module never throws at import/build time.
// Firebase is only initialised (and validated) the first time a getter is called,
// which always happens inside a browser context (useEffect / event handlers).

import { initializeApp, getApps, type FirebaseApp } from "firebase/app";
import { getAuth, type Auth } from "firebase/auth";
import {
  getFirestore,
  type Firestore,
  initializeFirestore,
  persistentLocalCache,
  persistentMultipleTabManager,
} from "firebase/firestore";
import { envConfig } from "./env.config";

// ─── Internal singletons ──────────────────────────────────────────────────────

let _app: FirebaseApp | undefined;
let _auth: Auth | undefined;
let _db: Firestore | undefined;

// ─── Lazy initialiser ─────────────────────────────────────────────────────────

function initFirebase(): { app: FirebaseApp; auth: Auth; db: Firestore } {
  // Return already-initialised singletons on subsequent calls.
  if (_app && _auth && _db) {
    return { app: _app, auth: _auth, db: _db };
  }

  const firebaseConfig = envConfig.firebase;

  // Validate at call-time (runtime, inside the browser) – not at module
  // evaluation time, so Next.js static generation never hits this throw.
  if (!firebaseConfig.apiKey || !firebaseConfig.authDomain || !firebaseConfig.projectId) {
    throw new Error(
      "Firebase configuration is missing. Please ensure all required " +
        "environment variables are set in .env.local"
    );
  }

  const alreadyInitialised = getApps().length > 0;

  _app = alreadyInitialised ? getApps()[0] : initializeApp(firebaseConfig);

  _auth = getAuth(_app);

  // initializeFirestore (with persistence options) must only be called once,
  // before any other Firestore calls – use it only on the first initialisation.
  _db = alreadyInitialised
    ? getFirestore(_app)
    : initializeFirestore(_app, {
        localCache: persistentLocalCache({
          tabManager: persistentMultipleTabManager(),
        }),
      });

  if (!alreadyInitialised) {
    console.log("🔥 Firebase initialised");
    console.log("  Project ID:", firebaseConfig.projectId);
    console.log("  Firestore database:", _db.app.options.projectId);
  }

  return { app: _app, auth: _auth, db: _db };
}

// ─── Public getters ───────────────────────────────────────────────────────────

/** Returns the Firebase app instance (initialises on first call). */
export function getFirebaseApp(): FirebaseApp {
  return initFirebase().app;
}

/** Returns the Firebase Auth instance (initialises on first call). */
export function getFirebaseAuth(): Auth {
  return initFirebase().auth;
}

/** Returns the Firestore instance (initialises on first call). */
export function getFirebaseDb(): Firestore {
  return initFirebase().db;
}
