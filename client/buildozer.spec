[app]
title = BetterDisplay
package.name = btds
package.domain = org.btds
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3,kivy,opencv,numpy

# Use the generated icon
icon.filename = ../assets/icon.jpg

orientation = landscape
fullscreen = 1

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
