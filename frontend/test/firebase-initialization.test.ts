import { beforeEach, describe, expect, it, vi } from "vitest";

vi.unmock("@/lib/firebase");

const mocks = vi.hoisted(() => ({
  app: { options: { projectId: "test-project" } },
  auth: { name: "auth" },
  db: { name: "db" },
  getApps: vi.fn(),
  getAuth: vi.fn(),
  getFirestore: vi.fn(),
  initializeApp: vi.fn(),
  initializeAuth: vi.fn(),
  initializeFirestore: vi.fn(),
  localPersistence: { type: "LOCAL" },
  sessionPersistence: { type: "SESSION" },
  popupResolver: { name: "popup-resolver" },
  localCache: { name: "local-cache" },
}));

vi.mock("firebase/app", () => ({
  getApps: mocks.getApps,
  initializeApp: mocks.initializeApp,
}));

vi.mock("firebase/auth", () => ({
  browserLocalPersistence: mocks.localPersistence,
  browserPopupRedirectResolver: mocks.popupResolver,
  browserSessionPersistence: mocks.sessionPersistence,
  getAuth: mocks.getAuth,
  initializeAuth: mocks.initializeAuth,
}));

vi.mock("firebase/firestore", () => ({
  getFirestore: mocks.getFirestore,
  initializeFirestore: mocks.initializeFirestore,
  persistentLocalCache: vi.fn(() => mocks.localCache),
  persistentMultipleTabManager: vi.fn(() => ({ name: "tab-manager" })),
}));

vi.mock("@/lib/env.config", () => ({
  envConfig: {
    firebase: {
      apiKey: "public-test-key",
      appId: "test-app",
      authDomain: "test-project.firebaseapp.com",
      messagingSenderId: "123",
      projectId: "test-project",
      storageBucket: "test-project.firebasestorage.app",
    },
  },
}));

describe("Firebase client initialization", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
    mocks.getApps.mockReturnValue([]);
    mocks.initializeApp.mockReturnValue(mocks.app);
    mocks.initializeAuth.mockReturnValue(mocks.auth);
    mocks.initializeFirestore.mockReturnValue(mocks.db);
  });

  it("initializes Auth independently with local and session persistence", async () => {
    const { getFirebaseAuth } = await import("@/lib/firebase");

    expect(getFirebaseAuth()).toBe(mocks.auth);
    expect(mocks.initializeAuth).toHaveBeenCalledWith(mocks.app, {
      persistence: [mocks.localPersistence, mocks.sessionPersistence],
      popupRedirectResolver: mocks.popupResolver,
    });
    expect(mocks.initializeFirestore).not.toHaveBeenCalled();
  });

  it("does not initialize Auth when only Firestore is requested", async () => {
    const { getFirebaseDb } = await import("@/lib/firebase");

    expect(getFirebaseDb()).toBe(mocks.db);
    expect(mocks.initializeFirestore).toHaveBeenCalledOnce();
    expect(mocks.initializeAuth).not.toHaveBeenCalled();
  });
});
