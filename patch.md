___扩展程序启动___
 [chromium本地存储路径]/src/out/Release/Chromium.app/Contents/MacOS/Chromium --no-sandbox

使用--no-sandbox参数使日志能被记录到本地文件

___开启扩展测试单元___
---------------
/chrome/browser/extensions/extension_service.cc

在void ExtensionService::EnableExtension中，将来extension_id.c_str()记录在日志文件


