/**
 * Environment configuration loader
 * Workaround for Turbopack issue in Next.js 16 with environment variables
 *
 * This file loads environment variables at build time and makes them available
 * without relying on process.env at runtime.
 */

// Load env vars at build/import time
const getEnvConfig = () => {
  const config = {
    firebase: {
      apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
      authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
      projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
      storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
      messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
      appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
    },
  };

  // Validate that all required variables are present
  const missing: string[] = [];
  Object.entries(config.firebase).forEach(([key, value]) => {
    if (!value) {
      // Convert camelCase to UPPER_SNAKE_CASE properly
      const envVarName = `NEXT_PUBLIC_FIREBASE_${key
        .replace(/([A-Z])/g, "_$1")
        .toUpperCase()
        .replace(/^_/, "")}`;
      missing.push(envVarName);
    }
  });

  if (missing.length > 0) {
    console.error("❌ Missing environment variables:", missing.join(", "));
    console.error("💡 Make sure .env.local is properly configured");
  }

  return config;
};

export const envConfig = getEnvConfig();
