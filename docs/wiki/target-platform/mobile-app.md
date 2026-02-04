---
sidebar_label: Mobile App
sidebar_position: 1
---

Convert a React/Vite web app created using Google AI Studio to a native iOS/Android mobile app using Capacitor, with minimal code changes.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather information

Gather the following information from the user-provided context:

- Project directory path
- Any native features needed (camera, filesystem, geolocation, etc.)

If not specified, default to:

- Current working directory for project path
- Inspecting the project source code yourself to understand what features it makes use of

Explore the codebase to understand:

- Build tool (Vite, CRA, Next.js, etc.) and output directory
- Existing features that need native equivalents (file inputs, camera, etc.)

### Step 1: Install Capacitor

```bash
npm install @capacitor/core @capacitor/cli @capacitor/ios @capacitor/android
```

### Step 2: Initialize Capacitor

```bash
npx cap init "<App Name>" "<app.bundle.id>" --web-dir <build-output-dir>
```

Use the project name for app name, create a reasonable bundle ID (e.g., `com.company.appname`), and set `--web-dir` to the build output (usually `dist` for Vite, `build` for CRA).

### Step 3: Install native plugins

Install Capacitor plugins for any native features needed:

```bash
npm install @capacitor/camera @capacitor/filesystem  # Common for image handling
```

Other common plugins: `@capacitor/geolocation`, `@capacitor/storage`, `@capacitor/push-notifications`

### Step 4: Update components to use native APIs

For each web feature that needs a native equivalent, update the component to:

1. Import from Capacitor: `import { Camera } from '@capacitor/camera'`
2. Import platform detection: `import { Capacitor } from '@capacitor/core'`
3. Use `Capacitor.isNativePlatform()` to branch between native and web implementations
4. Keep the web fallback for browser compatibility

Example pattern for camera:

```typescript
const handleCapture = () => {
  if (Capacitor.isNativePlatform()) {
    // Use Capacitor Camera API
    Camera.getPhoto({
      resultType: CameraResultType.Base64,
      source: CameraSource.Camera,
    });
  } else {
    // Fall back to file input for web
    fileInputRef.current?.click();
  }
};
```

### Step 5: Configure mobile viewport

Update `index.html` with mobile-specific meta tags:

```html
<meta
  name="viewport"
  content="width=device-width, initial-scale=1.0, viewport-fit=cover, user-scalable=no, maximum-scale=1"
/>
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta
  name="apple-mobile-web-app-status-bar-style"
  content="black-translucent"
/>
<meta name="theme-color" content="#000000" />
```

Add CSS for safe areas and overscroll prevention:

```css
.safe-area-bottom {
  padding-bottom: env(safe-area-inset-bottom);
}
.safe-area-top {
  padding-top: env(safe-area-inset-top);
}
html,
body {
  overscroll-behavior: none;
}
```

### Step 6: Update Capacitor config

Edit `capacitor.config.ts` to add platform-specific settings:

```typescript
const config: CapacitorConfig = {
  appId: "com.example.app",
  appName: "App Name",
  webDir: "dist",
  ios: {
    contentInset: "automatic",
    backgroundColor: "#000000", // Match app background
  },
  android: {
    backgroundColor: "#000000",
  },
  plugins: {
    // Plugin-specific config
  },
};
```

### Step 7: Build and add platforms

```bash
npm run build && npx cap add ios && npx cap add android
```

### Step 8: Configure platform permissions

**iOS** - Edit `ios/App/App/Info.plist` to add required permission descriptions:

- `NSCameraUsageDescription` - Camera access
- `NSPhotoLibraryUsageDescription` - Photo library read access
- `NSPhotoLibraryAddUsageDescription` - Photo library write access
- `NSLocationWhenInUseUsageDescription` - Location access

**Android** - Edit `android/app/src/main/AndroidManifest.xml` to add permissions:

- `android.permission.CAMERA`
- `android.permission.READ_EXTERNAL_STORAGE`
- `android.permission.WRITE_EXTERNAL_STORAGE`
- `android.permission.READ_MEDIA_IMAGES` (Android 13+)
- `android.permission.ACCESS_FINE_LOCATION`

### Step 9: Update .gitignore

Add Capacitor-specific ignores for build artifacts while keeping project config:

```gitignore
# Capacitor - iOS
ios/App/App/public
ios/App/App/capacitor.config.json
ios/App/Pods
ios/App/App.xcworkspace/xcuserdata
ios/App/App.xcodeproj/xcuserdata
ios/DerivedData

# Capacitor - Android
android/app/src/main/assets/public
android/app/src/main/assets/capacitor.config.json
android/.gradle
android/app/build
android/build
android/local.properties
android/.idea
android/*.iml
android/app/*.iml
```

### Step 10: Add npm scripts

Add convenience scripts to `package.json`:

```json
{
  "scripts": {
    "cap:sync": "npm run build && npx cap sync",
    "cap:ios": "npm run build && npx cap sync ios && npx cap open ios",
    "cap:android": "npm run build && npx cap sync android && npx cap open android",
    "cap:run:ios": "npm run build && npx cap sync ios && npx cap run ios",
    "cap:run:android": "npm run build && npx cap sync android && npx cap run android"
  }
}
```

If using a different build tool other than npm, update accordingly for that build tool instead.

### Step 11: Sync and verify

```bash
npx cap sync
```

Verify the setup works by asking the user to run these commands to open and test the projects in the respective IDEs:

- iOS: `npm run cap:ios` (requires Xcode on macOS)
- Android: `npm run cap:android` (requires Android Studio)

### Step 12: Update documentation

Update the project's README or docs to document:

- Mobile prerequisites (Xcode, Android Studio)
- Available npm scripts for mobile development
- How Capacitor works (web app in native shell)
- Platform-specific build/deploy instructions
- Troubleshooting common issues

## Key Principles

- **Minimal code changes**: Capacitor wraps your existing web app - you're not rewriting it
- **Platform detection**: Use `Capacitor.isNativePlatform()` to branch between native and web implementations, keeping web compatibility
- **Permissions are platform-specific**: iOS uses Info.plist descriptions, Android uses AndroidManifest.xml permissions
- **Build artifacts are regenerated**: Gitignore the `public/` directories and build outputs in native projects, but commit the project configuration files
- **Always rebuild before testing**: Changes to web code require `npm run build && npx cap sync` before they appear in native apps
