// Firebase configuration and initialization
// Uses lazy initialization so this module never throws at import/build time.
// Firebase is only initialised (and validated) the first time a getter is called,
// which always happens inside a browser context (useEffect / event handlers).

import { initializeApp, getApps, type FirebaseApp } from "firebase/app";
import {
  browserLocalPersistence,
  browserPopupRedirectResolver,
  browserSessionPersistence,
  getAuth,
  initializeAuth,
  type Auth,
} from "firebase/auth";
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

// ─── Lazy initialisers ────────────────────────────────────────────────────────

function initFirebaseApp(): FirebaseApp {
  if (_app) {
    return _app;
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

  const existingApp = getApps()[0];
  _app = existingApp || initializeApp(firebaseConfig);

  if (!existingApp) {
    console.log("🔥 Firebase initialised");
    console.log("  Project ID:", firebaseConfig.projectId);
  }

  return _app;
}

// ─── Public getters ───────────────────────────────────────────────────────────

/** Returns the Firebase app instance (initialises on first call). */
export function getFirebaseApp(): FirebaseApp {
  return initFirebaseApp();
}

/** Returns the Firebase Auth instance (initialises on first call). */
export function getFirebaseAuth(): Auth {
  if (_auth) {
    return _auth;
  }

  const app = initFirebaseApp();
  try {
    _auth = initializeAuth(app, {
      // Local persistence keeps sessions across browser restarts without using
      // Auth's IndexedDB persistence, which can close while mobile OAuth UI is
      // foregrounded. Session storage remains the official fallback.
      persistence: [browserLocalPersistence, browserSessionPersistence],
      popupRedirectResolver: browserPopupRedirectResolver,
    });
  } catch (error) {
    // During hot reload Firebase may retain the Auth instance while this module
    // is re-evaluated. Reuse that instance; propagate every other error.
    if (
      typeof error === "object" &&
      error !== null &&
      "code" in error &&
      error.code === "auth/already-initialized"
    ) {
      _auth = getAuth(app);
    } else {
      throw error;
    }
  }

  return _auth;
}

/** Returns the Firestore instance (initialises on first call). */
export function getFirebaseDb(): Firestore {
  if (_db) {
    return _db;
  }

  const app = initFirebaseApp();
  try {
    _db = initializeFirestore(app, {
      localCache: persistentLocalCache({
        tabManager: persistentMultipleTabManager(),
      }),
    });
  } catch (error) {
    // Reuse an existing Firestore instance after hot reload. The original
    // persistence configuration remains attached to that instance.
    if (
      typeof error === "object" &&
      error !== null &&
      "code" in error &&
      error.code === "failed-precondition"
    ) {
      _db = getFirestore(app);
    } else {
      throw error;
    }
  }

  return _db;
}
