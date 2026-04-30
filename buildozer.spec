[app]
# App info
title = CALC//SYS
package.name = calcsys
package.domain = org.calcsys
version = 1.0

# Source
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.include_patterns = data.json

# Requirements
requirements = python3,kivy==2.3.0

# Android
android.permissions = INTERNET
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a, armeabi-v7a

# Orientation
orientation = portrait
fullscreen = 0

# Icons
#icon.filename = %(source.dir)s/assets/icon.png

# Boot screen
#presplash.filename = %(source.dir)s/assets/presplash.png
presplash.color = #080808

# iOS (ignore)
[buildozer]
log_level = 2
warn_on_root = 1
