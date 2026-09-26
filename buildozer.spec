[app]

# (str) Title of your application
title = Embodied Cybernetics Agency

# (str) Package name (no spaces, used internally by Android)
package.name = embodiedcyberneticagency

# (str) Package domain (reverse-DNS style, unique to you)
package.domain = org.kryptickode007

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (leave empty to include all the files)
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,csv,ttf

# (str) Application versioning
version = 0.1

# (list) Application requirements
requirements = python3,kivy

# (str) Supported orientation (landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible
android.api = 33

# (int) Minimum API your APK / AAB will support
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1