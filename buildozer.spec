[app]
title = Image Studio Local
package.name = imagestudiolocal
package.domain = com.imagestudio
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas
version = 1.0
requirements = python3,kivy,requests,pillow,pyjnius
orientation = portrait
fullscreen = 0
android.api = 35
android.minapi = 24
android.archs = arm64-v8a
android.permissions = INTERNET,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,WRITE_EXTERNAL_STORAGE
android.allow_backup = True
android.gradle_dependencies = 
android.entrypoint = org.kivy.android.PythonActivity
