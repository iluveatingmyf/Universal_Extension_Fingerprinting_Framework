# Chromium 编译指南

在添加代码时注意替换掉原来的日志文件路径（[本地路径]/extension.log），以及配置文件config.txt的路径。

#### 源代码路径：base/metrics/field_trial.cc
+ 添加位置：函数```void FieldTrialList::CreateTrialsFromCommandLine(const CommandLine& cmd_line, int fd_key)```内部
+ 功能说明：关闭页面验证
```
    \\注释下方代码
    \\DCHECK(result);
```

#### 源代码路径：chrome/browser/extensions/crx_installer.cc
+ 添加位置：文件开头
+ 功能说明： 头文件引用
```
    #ifndef BASE_LOGGING_H_
    #include "/base/logging.h"
    #endif
    #include "chrome/browser/extensions/scripting_permissions_modifier.h"
```
+ 添加位置： ```CrxInstaller::CrxInstaller(base::WeakPtr<ExtensionService> service_weak, ...)```内部
+ 功能说明： 开启Chromium的静态安装功能，修改构造函数
+ 修改说明： 将```allow_silent_install_(false)```修改为```allow_silent_install_(true)```



+ 添加位置：```void CrxInstaller::ReportSuccessFromUIThread()```函数中```if (!update_from_settings_page_)``` 作用域结尾
+ 功能说明：给Honeysite授予与被安装扩展程序交互的权限，若honeysite的地址不是localhost:3000注意替换。

```
    ExtensionService* service = service_weak_.get();
    ScriptingPermissionsModifier modifier(profile(), extension());
    modifier.GrantHostPermission(GURL("http://localhost:3000"));
    if(!modifier.HasGrantedHostPermission(GURL("http://localhost:3000"))){
      VLOG(0) << extension()->id() << " grant permission on honeysite fail";
    }else{
      VLOG(0) << extension()->id() << " grant permission on honeysite success!";
    }

    //批量安装的扩展程序自动关闭，等待Autotester轮番开启，独立测试
    service->GrantPermissions(extension());
    service->DisableExtension(extension()->id(), disable_reason::DISABLE_USER_ACTION);
    VLOG(0) << "\n[INSTALL 3]--------------------"
          << "Extension " << extension()->id() << " installed!";

```



#### 源代码路径：chrome/browser/extensions/extension_service.h
+ 添加位置：在本文件原定义的所有class之前
+ 功能说明： 添加一个日志类，由此记录每次开启测试的扩展程序ID。另此处对临界区的操作windows和mac可能有差异，若修改参考链接https://blog.csdn.net/huang714/article/details/109524692 ，以下所有的日志类都类似。

```
#include <string.h>
#include <stdarg.h>
#include<iostream> 
#include <stddef.h>
#include <stdio.h>
#include "base/base_export.h"
#ifdef __APPLE__
        #include <sys/uio.h>
#else
        #include <io.h>
#endif

    #ifndef COMMAND_DEFINE_H
    #define COMMAND_DEFINE_H
    static const int MAX_STR_LEN = 1024;
    static const char * EXTENSIONPREFIX = "\n --------------------------\n[EXTENSION_ID]: ";
    #endif
    class BASE_EXPORT FinLogger{
    public:    
        //默认构造函数
        FinLogger();
        virtual ~FinLogger();
    public:
        void LogExtensionID(const std::string& extension_id);
    private:
        //写文件的操作
        void LogFin(const char * strInfo);
    private:
        //写日志文件流
        FILE * m_pFileStream;
        //日志的路径
        //线程同步的临界区变量
    std::string m_strLogPath;
    void* m_pCritSection;   
    };
```

#### 源代码路径：chrome/browser/extensions/extension_service.cc
+ 添加位置：文件开头
+ 功能说明： 头文件引用
```
    #include <dirent.h>
    #include <cstdio>
    #include <stdarg.h>
    #include <iostream> 
    #include <stdio.h>
    #include <string.h>
    #include <fstream>
    #include <vector>
    #ifdef __APPLE__
            #include <sys/uio.h>
    #else
            #include <io.h>
    #endif
```

+ 添加位置： 在本文件原定义的所有class之前
+ 功能说明： 实例化日志类

```
using namespace std;

FinLogger::FinLogger()
{
  //默认构造函数
  m_pFileStream = NULL;
  //输出日志文件的绝对路径
  m_strLogPath = "/Users/myf/Desktop/chro/extension.log";
  pthread_mutex_t *pMutex = new pthread_mutex_t;
  pthread_mutex_init(pMutex, NULL);
  m_pCritSection = reinterpret_cast<void*>(pMutex);
  // use InitializeCriticalSection(&m_cs) instead in Windows'
}

//析构函数
FinLogger::~FinLogger()
{
  //DeleteCriticalSection(&m_cs); in Windows
  pthread_mutex_t *pMutex = reinterpret_cast<pthread_mutex_t*>(m_pCritSection);
  pthread_mutex_destroy(pMutex);
  delete pMutex;

  if(m_pFileStream)
    fclose(m_pFileStream);
}

//写操作的函数

void FinLogger::LogFin(const char* strInfo)
{
  if(!strInfo)
    return;
  //进入临界区，EnterCriticalSection(&m_cs); in Windows
  pthread_mutex_lock(reinterpret_cast<pthread_mutex_t*>(m_pCritSection));
  //若文件流没有打开，则重新打开
  if(!m_pFileStream)
    {
      char temp[1024] = {0};
      strcat(temp, m_strLogPath);
      m_pFileStream = fopen(temp, "a+");
      if(!m_pFileStream)
      {
        return;
      }
    }
    DVLOG(0) << strInfo;
    //写日志信息到文件流
    fprintf(m_pFileStream, "%s\n", strInfo);
    fflush(m_pFileStream);
    //离开临界区, LeaveCriticalSection(&m_cs); in Windows
    pthread_mutex_unlock(reinterpret_cast<pthread_mutex_t*>(m_pCritSection));
}

void FinLogger::LogExtensionID(const std::string& extension_id){
  char pTemp[MAX_STR_LEN] = {0};
  strcat(pTemp, EXTENSIONPREFIX);
  strcat(pTemp, extension_id.c_str());
  strcat(pTemp, "\n");  
  LogFin(pTemp);
}
```


+ 添加位置： void ExtensionService::Init()函数的末尾
+ 功能说明： 在Chromium启动时清除原安装所有扩展程序，再安装config.txt指定路径中的新扩展程序开启新测试单元。注意替换config.txt的路径。

```
    VLOG(0) << "Installed Extensions: " << 
    registry_->GenerateInstalledExtensionsSet()->size();
    VLOG(0) << "Install Dir: " << install_directory_;
    
    // Read CRX path from config file
        std::string str;
        std::string crx_path;
        //需要替换config.txt的路径
        std::ifstream f("/Users/myf/Desktop/chro/src/out/Release/config.txt");
        if (!f) {
        VLOG(0) << std::endl << "Config File not found." << std::endl;
        return;
        }

        //auto* extension_service =
        //extensions::ExtensionSystem::Get(profile())->extension_service();
        // std::u16string error;

        while (getline(f, str)) {
        std::string::size_type n;
        if((n = str.find("=")) != std::string::npos) {
        if (str.substr(0, n) == "crxpath") {
            crx_path = str.substr(n + 1);
            VLOG(0) << "\n--------------------" 
                    << "CRX Folder Path: " << crx_path;
            break;  
            }
        }
        }
    
    // List dir
    std::vector<std::string> crx_files;
    
    


    DIR *dir;
    struct dirent *catlog;
    char cFileTmp[64] = {0};
    DVLOG(0)<<dir;
    dir = opendir(crx_path.c_str());
    if(dir == NULL){
        VLOG(0) << "\n--------------------" 
                << crx_path << " is empty!";
        return;
    }

    while((catlog = readdir(dir)) != NULL){
        VLOG(0) <<  catlog->d_name;
        sprintf(cFileTmp, "%s", catlog->d_name);
        crx_files.push_back(cFileTmp);
    }
    closedir(dir);
    
    


    std::unique_ptr<ExtensionSet> remove_extensions =
        registry_->GenerateInstalledExtensionsSet();

    for (auto extension_id : *remove_extensions) {
        std::u16string error;
        if(strcmp(extension_id->id().c_str(), "ebfjcddknegphmacmpahfgpbkgedfhlk") == 0){
        continue;
        }
        if (!UninstallExtension(extension_id->id(), UNINSTALL_REASON_INTERNAL_MANAGEMENT,
                                &error)) {
        SYSLOG(WARNING) << "Extension with id " << extension_id
                        << " failed to be uninstalled via policy: " << error;
        }
    }



    for (const std::string& crx : crx_files) {
    // // Read A CRX File
        if(crx.length() < 20){
        continue;
        }
        VLOG(0) << "\n[INSTALL 1]--------------------"
                << "Now Loading: " << crx;
        std::string id = crx.substr(0, 32);

        // Pass the crx path to crxfileinfo
        std::string _crx_file = crx_path.c_str() + crx;
        base::StringPiece filename(_crx_file);
        const base::FilePath file_path(filename);
        CRXFileInfo file_info(file_path, GetExternalVerifierFormat());

        // Install if not installed
        const Extension* extension = registry_->GetExtensionById(
        id, ExtensionRegistry::EVERYTHING);
        if (extension) {
            VLOG(0) << id << "already exists. Skip.\n"
            << "dis: " << registry_->disabled_extensions().Contains(id) << "\n"
            << "tem: " << registry_->terminated_extensions().Contains(id) << "\n"
            << "blk: " << registry_->blocked_extensions().Contains(id) << "\n"
            << "bll: " << registry_->blocklisted_extensions().Contains(id);
        } else {
        // Silent install
        scoped_refptr<CrxInstaller> installer(CrxInstaller::CreateSilent(this));
        installer->set_install_cause(extension_misc::INSTALL_CAUSE_EXTERNAL_FILE);
        installer->set_expected_id(id);
        installer->set_install_immediately(true);
        installer->set_grant_permissions(true);
        installer->InstallCrxFile(file_info); // Enable the extension in InstallCrxFile
    
        // Suppress the notification
        external_install_manager_->AcknowledgeExternalExtension(id);
        VLOG(0) << "\n[INSTALL 2]--------------------"
                << "Extension: " << id << " installing...";
        }

    }

```


+ 添加位置： ```void ExtensionService::EnableExtension(const std::string& extension_id)```函数开头
+ 功能说明： 将由Autotester开启的扩展程序UUID记录在日志文件中
```
    DVLOG(0)<<"----------------------";
    DVLOG(0)<< "[Start To Test]" + extension_id;
    FinLogger * finlogger = new FinLogger();
    finlogger->LogExtensionID(extension_id);
```


#### 源代码路径：chrome/browser/extensions/extension_tab_util.cc
+ 修改说明1：```bool ExtensionTabUtil::OpenOptionsPageFromAPI ```函数，直接 return false

+ 修改说明2: 为了防止测试目标扩展程序时可能出现的，将honeysite导航到其他网页情况导致测试中断的情况，在```bool ExtensionTabUtil::PrepareURLForNavigation```末尾，倒数第三行（swap函数之前）添加代码```if(url!=GURL("http://localhost:3000")){return false;}```(如果honeysite URL不一致需要替换)

+ 修改说明3: 防止测试目标扩展程序时，可能出现自动打开新tab的情况```void ExtensionTabUtil::CreateTab```直接return

### 源代码路径：chrome/browser/extensions/scripting_permissions_modifier.cc
+ 修改说明1: 将```void ScriptingPermissionsModifier::GrantHostPermission(const GURL& url)```中的第一行```DCHECK(CanAffectExtension());```注释掉；

+ 修改说明2: 将```bool ScriptingPermissionsModifier::HasGrantedHostPermission```第一行的```DCHECK(CanAffectExtension());```注释掉；


#### 源代码路径：chrome\browser\extensions\api\web_navigation\web_navigation_api_helpers.cc
+ 添加位置: 文件开头
+ 功能说明: 添加头文件
```
    #include "chrome/browser/extensions/extension_action_runner.h"
    #include "extensions/browser/extension_action_manager.h"
    #include "chrome/browser/ui/browser_finder.h"
    #include "base/run_loop.h"
    #ifndef BASE_LOGGING_H_
    #include "/base/logging.h"
    #endif
    #include "chrome/browser/extensions/tab_helper.h"
    #include "chrome/browser/extensions/api/extension_action/extension_action_api.h"
    #include <iostream>
    #include <string>
    #include <fstream>
    #include "extensions/renderer/dom_activity_logger.h"
    #include "chrome/browser/extensions/extension_service.h"
    #include "extensions/browser/extension_system.h"
    #include<sstream>
```

+ 添加位置：```void DispatchOnCompleted```函数末尾的```DispatchEvent(browser_context, std::move(event), url);```之前
+ 功能说明： 此处完成拓展的自动激活，注意替换config.txt的路径
```
    std::string str;
    std::string myid;
    std::ifstream f("/Users/myf/Desktop/chro/src/out/Release/config.txt");
    if (!f) {
        VLOG(0) << std::endl << "Config File not found." << std::endl;
        return;
    }
    while (getline(f, str)) {
        std::string::size_type n;
        if((n = str.find("=")) != std::string::npos) {
        if (str.substr(0, n) == "autotester_id") {
            myid = str.substr(n + 1);
            VLOG(0) << "\n--------------------" 
                    << "Autotester id: " << myid;
            break;  
        }
        }
    }

    ExtensionRegistry* registry_ = ExtensionRegistry::Get(browser_context);
    int flag = 1;

    for (const auto& extension : registry_->enabled_extensions()) { 
        //在浏览器初次启动时，只激活一次Autotester即可
        if (extension->id() == myid) {
            if(flag == 0){
                continue;
            }else{
                flag = flag-1;
            };
        };

        extensions::ExtensionAction* extension_action = extensions::ExtensionActionManager::Get(browser_context)->GetExtensionAction(*extension);
        
        if(!extension_action){VLOG(0)<<"no extension_action for" << extension->id();continue;}
        VLOG(0)<< "\n---------------------" << "Run: " << extension->id();
        extensions::ExtensionActionRunner* runner = extensions::ExtensionActionRunner::GetForWebContents(web_contents);
        if(!runner){VLOG(0)<<"no runner";continue;}
        runner->RunAction(extension.get(), true);
    }
```

#### 源代码路径：chrome/browser/ui/views/tabs/tab_hover_card_bubble_view.cc
+ 修改说明： 将```std::unique_ptr<views::View> CreateAlertView```函数的赋值         ```alert_state_label->SetVisible(true);```中的`true改为false，由此屏蔽测试过程中的弹窗

#### 源代码路径：extensions/browser/api/management/management_api.cc
+ 修改说明：将 ```show_confirm_dialog |= !self_uninstall;``` 改为 ```show_confirm_dialog = false;``` 即可取消卸载拓展时弹出的确认窗口

#### 源代码路径：third_party/blink/renderer/core/dom/container_node.h
+ 添加位置： 所有本文件class定义之前
+ 功能说明： 定义日志类别（之前定义的日志类无法跨文件调用，不太了解C++不确定问题出现在哪里，若有更好的方法烦请指正）。注意windows与mac对临界区处理的差异与前文提及的类似。
```
    #include "third_party/blink/renderer/core/css/parser/css_parser.h"
    #include "third_party/blink/renderer/core/css/parser/css_tokenizer.h"
    #include "third_party/blink/renderer/core/css/parser/css_selector_parser.h"
    #include "third_party/blink/renderer/core/css/css_selector_list.h"
    #include "third_party/blink/renderer/core/css/css_test_helpers.h"
    #include "third_party/blink/renderer/core/css/parser/css_parser_context.h"
    #include "third_party/blink/renderer/core/css/parser/css_tokenizer.h"
    #include "third_party/blink/renderer/core/css/style_sheet_contents.h"

    #include "third_party/blink/renderer/platform/heap/garbage_collected.h"
    #include "third_party/blink/renderer/core/css/css_selector.h"

    #include <vector>
    #include <stdarg.h>
    #include <iostream> 
    #include <stddef.h>
    #include <stdio.h>
    #include <string.h>
    #include <fstream>
    #include <iterator>
    #include <memory>
    #include <set>
    #include <utility>
    #ifdef __APPLE__
            #include <sys/uio.h>
    #else
            #include <io.h>
    #endif


    #ifndef COMMAND_DEFINE_H
    #define COMMAND_DEFINE_H
    static const int MAX_STR_LEN = 4096;
    static const char * APIPREFIX = "[API]:";
    static const char * MDOMPREFIX = "[M_DOM]:";
    static const char * ORIGINDOMPREFIX = "[O_DOM]:";
    static const char * EXTENSIONPREFIX = "\n --------------------------\n[EXTENSION_ID]: ";
    #endif
    class BASE_EXPORT FinLoggerX{
    public:    
        //默认构造函数
        FinLoggerX();
        virtual ~FinLoggerX();
    public:
        WTF::Vector<WTF::String>  GenerateLogFormat(WTF::String content, WTF::String origin);
        //直接记录DOM操作
        void Direct_Log(const char* API_name, WTF::Vector<WTF::String> obj);
        void Query_Log(const char* API_name, const char* content);
    private:
        //写文件的操作
        void LogFin(const char * strInfo);
    private:
        //写日志文件流
        FILE * m_pFileStream;
        //日志的路径
        //线程同步的临界区变量
        //pthread_mutex_t *pMutex;
    std::string m_strLogPath;
    void* m_pCritSection;
    
    };

```


#### 源代码路径：third_party/blink/renderer/core/dom/container_node.cc
+ 添加位置： 所有本文件class定义之前
+ 功能说明： 定义日志类别（之前定义的日志类无法跨文件调用，不太了解C++不确定问题出现在哪里，若有更好的方法烦请指正）。注意windows与mac对临界区处理的差异与前文提及的类似。
```
    #ifndef BASE_LOGGING_H_
    #include "/base/logging.h"
    #endif

    #include "chrome/browser/extensions/extension_service.h"
    #include <stdarg.h>
    #include <iostream> 
    #include <stddef.h>
    #include <stdio.h>
    #include <string.h>
    #include <fstream>
    #include <vector>
    #include <iterator>
    #include <memory>
    #include <set>
    #include <utility>
    #include "third_party/blink/renderer/core/dom/attr.h"
    #include "third_party/blink/public/web/web_element.h"
    #include "third_party/blink/renderer/core/css/parser/css_parser.h"
    #include "third_party/blink/renderer/core/css/parser/css_tokenizer.h"
    #include "third_party/blink/renderer/core/css/parser/css_selector_parser.h"
    #include "third_party/blink/renderer/core/css/css_selector_list.h"
    #include "third_party/blink/renderer/core/css/css_test_helpers.h"
    #include "third_party/blink/renderer/core/css/parser/css_parser_context.h"
    #include "third_party/blink/renderer/core/css/parser/css_tokenizer.h"
    #include "third_party/blink/renderer/core/css/style_sheet_contents.h"
    #include "third_party/blink/renderer/core/dom/document.h"
    #include "third_party/blink/renderer/platform/heap/garbage_collected.h"
    #include "third_party/blink/renderer/core/css/has_argument_match_context.h"
    #include "third_party/blink/renderer/core/css/css_selector.h"
    #include "third_party/blink/renderer/core/dom/element.h"
    
    using namespace std;
    FinLoggerX::FinLoggerX()
    {
    //默认构造函数
    m_pFileStream = NULL;
    //注意替换日志路径
    m_strLogPath = "/Users/myf/Desktop/chro/extension.log";
    pthread_mutex_t *pMutex = new pthread_mutex_t;
    pthread_mutex_init(pMutex, NULL);
    m_pCritSection = reinterpret_cast<void*>(pMutex);
    // use InitializeCriticalSection(&m_cs) instead in Windows'
    }

    //析构函数
    FinLoggerX::~FinLoggerX()
    {
    //DeleteCriticalSection(&m_cs); in Windows
    pthread_mutex_t *pMutex = reinterpret_cast<pthread_mutex_t*>(m_pCritSection);
    pthread_mutex_destroy(pMutex);
    delete pMutex;

    if(m_pFileStream)
        fclose(m_pFileStream);
    }

    //写操作的函数

    void FinLoggerX::LogFin(const char* strInfo)
    {
    if(!strInfo)
        return;
    //进入临界区，EnterCriticalSection(&m_cs); in Windows
    pthread_mutex_lock(reinterpret_cast<pthread_mutex_t*>(m_pCritSection));
    //若文件流没有打开，则重新打开
    if(!m_pFileStream)
        {
        char temp[1024] = {0};
        strcat(temp, m_strLogPath.c_str());
        m_pFileStream = fopen(temp, "a+");
        if(!m_pFileStream)
        {
            return;
        }
        }
        DVLOG(0) << strInfo;
        //写日志信息到文件流
        fprintf(m_pFileStream, "%s\n", strInfo);
        fflush(m_pFileStream);
        //离开临界区, LeaveCriticalSection(&m_cs); in Windows
        pthread_mutex_unlock(reinterpret_cast<pthread_mutex_t*>(m_pCritSection));
    }



    WTF::Vector<WTF::String>  FinLoggerX::GenerateLogFormat(WTF::String content, WTF::String origin){
    WTF::Vector<WTF::String> obj;
    obj.push_back(MDOMPREFIX);
    obj.push_back(content);
    obj.push_back(ORIGINDOMPREFIX);
    obj.push_back(origin);
    return obj;
    }


    void FinLoggerX::Query_Log(const char* API_name, const char* content)
    {
    if(!content)
        return;
    char pTemp[MAX_STR_LEN] = {0};
    strcpy(pTemp, APIPREFIX);
    strcpy(pTemp+strlen(pTemp), API_name);
    strcpy(pTemp + strlen(pTemp), content);
    //写日志文件
    LogFin(pTemp);
    }

    void FinLoggerX::Direct_Log(const char* API_name, WTF::Vector<WTF::String> obj )
    {

    char pTemp[MAX_STR_LEN] = {0};
    strcpy(pTemp, APIPREFIX);
    strcpy(pTemp+strlen(pTemp), API_name);
    for(int i=0; i<4;i++){
        strcpy(pTemp+strlen(pTemp), obj[i].Ascii().c_str());
    }
    //写日志文件
    LogFin(pTemp);
    }
```


+ 添加位置： ```Node* ContainerNode::InsertBefore(Node* new_child, Node* ref_child) ```函数开头
+ 功能说明： 记录InsertBefore DOM Interface的关键参数
```
  FinLoggerX * finlogger = new FinLoggerX();
  WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(DynamicTo<Element>(new_child)->outerHTML(),DynamicTo<Element>(ref_child)->outerHTML());
   String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
  if (executing_window == "localhost"){
    finlogger->Direct_Log("insertBefore\t", obj);
  }
```

+ 添加位置： ```Node* ContainerNode::ReplaceChild(Node* new_child, Node* old_child, ExceptionState& exception_state) ```函数开头
+ 功能说明： 记录ReplaceChild DOM Interface的关键参数
```
  FinLoggerX * finlogger = new FinLoggerX();
  WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(DynamicTo<Element>(old_child)->outerHTML(),DynamicTo<Element>(new_child)->outerHTML());
   String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
  if (executing_window == "localhost"){
    finlogger->Direct_Log("ReplaceChild", obj);
  }
```

+ 添加位置： ```Node* ContainerNode::RemoveChild(Node* old_child,ExceptionState& exception_state)```函数开头
+ 功能说明： 记录ReplaceChild DOM Interface的关键参数
```
  FinLoggerX * finlogger = new FinLoggerX();
  WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(DynamicTo<Element>(old_child)->outerHTML(),DynamicTo<Element>(old_child)->outerHTML());
   String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
  if (executing_window == "localhost"){
    finlogger->Direct_Log("RemoveChild", obj);
  } 
```


+ 添加位置： ```Element* ContainerNode::QuerySelector(const AtomicString& selectors, ExceptionState& exception_state) ```函数中```if (!selector_query)```作用域之后
+ 功能说明： 除记录QuerySelector DOM Interface的关键调用参数外，在页面没有符合其请求的元素时为其创建一个，由此触发扩展程序的更多DOM行为
```
  FinLoggerX * finlogger = new FinLoggerX();
  String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
  if (executing_window == "localhost"){
        finlogger->Query_Log("QuerySelector\t", selectors.Utf8().c_str()); 
  }
  //If no element found, create element accordingly
  if(!selector_query->QueryFirst(*this)){
    auto* context = MakeGarbageCollected<CSSParserContext>(
        kHTMLStandardMode, SecureContextMode::kInsecureContext);
    auto* sheet = MakeGarbageCollected<StyleSheetContents>(context);
    CSSTokenizer tokenizer(selectors);
    const auto tokens = tokenizer.TokenizeToEOF();
    CSSParserTokenRange range(tokens);
    CSSSelectorList list =
        CSSSelectorParser::ParseSelector(range, context, sheet);
    
    //遍历selectorlist里面的每一个selector
    for (const CSSSelector* s = list.First(); s; s = list.Next(*s)) {  
      const CSSSelector* s1 = nullptr;
      const CSSSelector* s2 = nullptr;
      Element* other_one = nullptr;
      Element* other_two = nullptr;
    
      int depth =0;
      String rela;
      int ele_num = 0;
      int ele = 0;
      
      for (; s; s = s->TagHistory()) {
          if (depth ==0){s1 = s;}
          if (depth ==1){s2 = s;}
          depth = depth+1;
        if (ele_num == 0 && s->Match()== CSSSelector::kTag){
          other_one = GetDocument().CreateRawElement(s->TagQName());
          ele_num = ele_num + 1;
        }
        if (ele == 1 && s->Match()== CSSSelector::kTag){
          other_two = GetDocument().CreateRawElement(s->TagQName());
          ele_num = ele_num + 1;     
        }
        ele = ele_num;
        if (depth == 1){
          switch (s->Relation()) {
              case CSSSelector::kDescendant: //
                rela = "des";
                break;
              case CSSSelector::kChild: //>
                rela = "child";
                break;
              case CSSSelector::kDirectAdjacent: //+
                rela = "dj";
                break;
              case CSSSelector::kSubSelector:
                rela = "sub";
                //NOTREACHED();
                break;
              default:
                rela = "null";
                break;
            }
        }
        if(!(s->TagHistory())){
          break;
        }
    }

    if( depth > 2 ) {break;}

    if (depth == 1){
      switch(ele) {
            case 0: {     
                bool flag= false;        
                if(s->Match() == CSSSelector::kId && rela == "sub"){
                  Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
                  div_node->setAttribute(html_names::kIdAttr, s->Value());
                  GetDocument().body()->AppendChild(div_node);  
                  flag = true; 
                }
                if(s->Match() == CSSSelector::kClass && rela == "sub"){
                   Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
                    div_node->setAttribute(html_names::kClassAttr, s->Value());
                    GetDocument().body()->AppendChild(div_node);
                    flag = true; 
                }
                if(s->IsAttributeSelector() && rela == "sub"){
                  Attr* attr = GetDocument().createAttribute(s->Attribute().LocalName(), ASSERT_NO_EXCEPTION);
                  attr->setValue("Fingerprinting Test", ASSERT_NO_EXCEPTION);
                  Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
                  attr->AttachToElement(div_node, s->Attribute().LocalName());
                  GetDocument().body()->AppendChild(div_node);
                  flag = true; 
                }
                if(!flag){break;}
                break;   
            }
            case 1: {
              if(other_one && rela == "sub"){  
                GetDocument().body()->AppendChild(other_one);
              }
              break;
            }
           
      }
    }
    
    if (depth ==2){  
      switch(ele){
        case 0:{
          Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
          switch (s1->Match()){
            case CSSSelector::kId: 
                  div_node->setAttribute(html_names::kIdAttr, s1->Value());
                  break;
            case CSSSelector::kClass:
                  div_node->setAttribute(html_names::kClassAttr, s1->Value());
                  break;
            default:
                break; 
            }      
          if(s1->IsAttributeSelector()){
                Attr* attr = GetDocument().createAttribute(s1->Attribute().LocalName(), ASSERT_NO_EXCEPTION);
                attr->setValue("Fingerprinting Test", ASSERT_NO_EXCEPTION);
                attr->AttachToElement(div_node, s1->Attribute().LocalName());
          }
          switch (s2->Match()){
            case CSSSelector::kId: 
                  div_node->setAttribute(html_names::kIdAttr, s2->Value());
                  break;
            case CSSSelector::kClass:
                  div_node->setAttribute(html_names::kClassAttr, s2->Value());
                  break;
            default:
                break; 
            }      
          if(s2->IsAttributeSelector()){
                Attr* attr = GetDocument().createAttribute(s2->Attribute().LocalName(), ASSERT_NO_EXCEPTION);
                attr->setValue("Fingerprinting Test", ASSERT_NO_EXCEPTION);
                attr->AttachToElement(div_node, s2->Attribute().LocalName());
          }
          GetDocument().body()->AppendChild(div_node);
          break;
        }
        case 1:{
          switch (s2->Match()){
            case CSSSelector::kId: 
                  other_one->setAttribute(html_names::kIdAttr, s2->Value());
                  break;
            case CSSSelector::kClass:
                  other_one->setAttribute(html_names::kClassAttr, s2->Value());
                  break;
            default:
                break; 
            }      
            if(s2->IsAttributeSelector()){
                Attr* attr = GetDocument().createAttribute(s2->Attribute().LocalName(), ASSERT_NO_EXCEPTION);
                attr->setValue("Fingerprinting Test", ASSERT_NO_EXCEPTION);
                DVLOG(0) << s2->Attribute().LocalName();
                other_one->setAttributeNode(attr, exception_state);
            }
            GetDocument().body()->AppendChild(other_one);
            break;       
        }
        case 2:{
          if(other_one && other_two){
                if (rela == "des"){
                    other_one->AppendChild(other_two);
                    GetDocument().body()->AppendChild(other_one);
                  }
                if (rela =="child"){
                    other_two->AppendChild(other_one);
                    GetDocument().body()->AppendChild(other_two);
                }
                if (rela == "dj"){
                    GetDocument().body()->AppendChild(other_one);
                    GetDocument().body()->AppendChild(other_two);
                }    

          }
          break;
        } 
    }}
    }
    
     
  }

```


+ 添加位置： ```Element* ContainerNode::QuerySelectorAll(const AtomicString& selectors, ExceptionState& exception_state) ```函数中```if (!selector_query)```作用域之后
+ 功能说明： 与QuerySelector DOM Interface类似
```
  FinLoggerX * finlogger = new FinLoggerX();
  String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
  if (executing_window == "localhost"){
        finlogger->Query_Log("QuerySelectorAll\t",selectors.Utf8().c_str()); 
  }
  //If no element found, create element accordingly
  if(!selector_query->QueryAll(*this)){
    auto* context = MakeGarbageCollected<CSSParserContext>(
      kHTMLStandardMode, SecureContextMode::kInsecureContext);
    auto* sheet = MakeGarbageCollected<StyleSheetContents>(context);
    CSSTokenizer tokenizer(selectors);
    const auto tokens = tokenizer.TokenizeToEOF();
    CSSParserTokenRange range(tokens);
    CSSSelectorList list =
        CSSSelectorParser::ParseSelector(range, context, sheet);
    if (selectors!="html"){
    //遍历selectorlist里面的每一个selector
      for (const CSSSelector* s = list.First(); s; s = list.Next(*s)) {  
        const CSSSelector* s1 = nullptr;
        const CSSSelector* s2 = nullptr;
        Element* other_one = nullptr;
        Element* other_two = nullptr;
        
        int depth =0;
        String rela;
        int ele_num = 0;
        int ele = 0;
        for (; s; s = s->TagHistory()) {
            if (depth ==0){s1 = s;}
            if (depth ==1){s2 = s;}
            depth = depth+1;
          if (ele_num == 0 && s->Match()== CSSSelector::kTag){
            other_one = GetDocument().CreateRawElement(s->TagQName());
            ele_num = ele_num + 1;
          }
          if (ele == 1 && s->Match()== CSSSelector::kTag){
            other_two = GetDocument().CreateRawElement(s->TagQName());
            ele_num = ele_num + 1;     
          }
          ele = ele_num;
          if (depth == 1){
            switch (s->Relation()) {
                case CSSSelector::kDescendant: //
                  rela = "des";
                  break;
                case CSSSelector::kChild: //>
                  rela = "child";
                  break;
                case CSSSelector::kDirectAdjacent: //+
                  rela = "dj";
                  break;
                case CSSSelector::kSubSelector:
                  rela = "sub";
                  //NOTREACHED();
                  break;
                default:
                  rela = "null";
                  break;
              }
          }
          
          if(!(s->TagHistory())){
            break;
          }
        }
        
        if( depth > 2 ) {break;}

        if (depth == 1){
          switch(ele) {
                case 0: {     
                    bool flag= false;        
                    if(s->Match() == CSSSelector::kId && rela == "sub"){
                      Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
                      div_node->setAttribute(html_names::kIdAttr, s->Value());
                      GetDocument().body()->AppendChild(div_node);  
                      flag = true; 
                    }
                    if(s->Match() == CSSSelector::kClass && rela == "sub"){
                      Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
                        div_node->setAttribute(html_names::kClassAttr, s->Value());
                        GetDocument().body()->AppendChild(div_node);
                        flag = true; 
                    }
                    if(s->IsAttributeSelector() && rela == "sub"){
                      Attr* attr = GetDocument().createAttribute(s->Attribute().LocalName(), ASSERT_NO_EXCEPTION);
                      attr->setValue("Fingerprinting Test", ASSERT_NO_EXCEPTION);
                      Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
                      attr->AttachToElement(div_node, s->Attribute().LocalName());
                      GetDocument().body()->AppendChild(div_node);
                      flag = true; 
                    }
                    if(!flag){break;}
                    break;   
                }
                case 1: {
                  if(other_one && rela == "sub"){  
                    GetDocument().body()->AppendChild(other_one);
                  }
                  break;
                }
              
          }

      }
      
      if (depth ==2){  
        switch(ele){
          case 0:{
            Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
            switch (s1->Match()){
              case CSSSelector::kId: 
                    div_node->setAttribute(html_names::kIdAttr, s1->Value());
                    break;
              case CSSSelector::kClass:
                    div_node->setAttribute(html_names::kClassAttr, s1->Value());
                    break;
              default:
                  break; 
              }      
            if(s1->IsAttributeSelector()){
                  Attr* attr = GetDocument().createAttribute(s1->Attribute().LocalName(), ASSERT_NO_EXCEPTION);
                  attr->setValue("Fingerprinting Test", ASSERT_NO_EXCEPTION);
                  attr->AttachToElement(div_node, s1->Attribute().LocalName());
            }
            switch (s2->Match()){
              case CSSSelector::kId: 
                    div_node->setAttribute(html_names::kIdAttr, s2->Value());
                    break;
              case CSSSelector::kClass:
                    div_node->setAttribute(html_names::kClassAttr, s2->Value());
                    break;
              default:
                  break; 
              }      
            if(s2->IsAttributeSelector()){
                  Attr* attr = GetDocument().createAttribute(s2->Attribute().LocalName(), ASSERT_NO_EXCEPTION);
                  attr->setValue("Fingerprinting Test", ASSERT_NO_EXCEPTION);
                  attr->AttachToElement(div_node, s2->Attribute().LocalName());
            }
            GetDocument().body()->AppendChild(div_node);
            break;
          }
          case 1:{
            switch (s2->Match()){
              case CSSSelector::kId: 
                    other_one->setAttribute(html_names::kIdAttr, s2->Value());
                    break;
              case CSSSelector::kClass:
                    other_one->setAttribute(html_names::kClassAttr, s2->Value());
                    break;
              default:
                  break; 
              }      
              if(s2->IsAttributeSelector()){
                  Attr* attr = GetDocument().createAttribute(s2->Attribute().LocalName(), ASSERT_NO_EXCEPTION);
                  attr->setValue("Fingerprinting Test", ASSERT_NO_EXCEPTION);
                  other_one->setAttributeNode(attr, exception_state);
              }
              GetDocument().body()->AppendChild(other_one);
              break;       
          }
          case 2:{
            if(other_one && other_two){
                  if (rela == "des"){
                      other_one->AppendChild(other_two);
                      GetDocument().body()->AppendChild(other_one);
                    }
                  if (rela =="child"){
                      other_two->AppendChild(other_one);
                      GetDocument().body()->AppendChild(other_two);
                  }
                  if (rela == "dj"){
                      GetDocument().body()->AppendChild(other_one);
                      GetDocument().body()->AppendChild(other_two);
                  }    

            }
            break;
          } 
      }}
    }      
    }
  }
```


+ 添加位置： ```HTMLCollection* ContainerNode::getElementsByTagName(const AtomicString& qualified_name) ```函数开头
+ 功能说明： 记录扩展程序对标签的请求，如果页面没有，则按照要求创建一个，由此触发扩展更多行为
```
  if(EnsureCachedCollection<TagCollection>(kTagCollectionType,qualified_name)->length()==0){
    std::string str1 {"<"}, str2{qualified_name.Utf8()}, str3 = {"></"},str4 = ">";
    std::string code = (str1+str2+str3+str2+str4).c_str();
    GetDocument().body()->setInnerHTML(String(code));
    FinLoggerX * finlogger = new FinLoggerX();
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
          finlogger->Query_Log("getElementsByTagname\t", qualified_name.Utf8().c_str());
    } 
   }
```
+ 添加位置： ```getElementsByTagNameNS(const AtomicString& namespace_uri, const AtomicString& local_name)``` 函数开头
+ 功能说明： 不常用，记录即可
```
    if(EnsureCachedCollection<TagCollectionNS>(kTagCollectionNSType, namespace_uri.IsEmpty() ? g_null_atom : namespace_uri, local_name)->length()==0){
        FinLoggerX * finlogger = new FinLoggerX();
        String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
        if (executing_window == "localhost"){
            finlogger->Query_Log("getElementsByTagnameNS\t", local_name.Utf8().c_str());
        }
    }
```



+ 添加位置： ```NodeList* ContainerNode::getElementsByName(const AtomicString& element_name)```函数开头
+ 功能说明： 记录getElementsByName DOM Interface的关键参数，如果没有对应元素则为其创建
```
    FinLoggerX * finlogger = new FinLoggerX();
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
          finlogger->Query_Log("getElementsByName\t", element_name.Utf8().c_str());
          Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
        div_node->setAttribute(html_names::kNameAttr, element_name);
        DVLOG(0)<< div_node->outerHTML().Ascii().c_str();
        DVLOG(0)<<this->ToString();
        if(this->ToString() != "#document"){
          this->AppendChild(div_node); 
        } else{
          GetDocument().body()->AppendChild(div_node);
        }
    }
```


+ 添加位置： ```HTMLCollection* ContainerNode::getElementsByClassName(const AtomicString& class_names)```函数开头
+ 功能说明： 记录getElementsByClassName DOM Interface的关键参数，如果没有对应元素则为其创建
```
    FinLoggerX * finlogger = new FinLoggerX();
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
        finlogger->Query_Log("getElementsByClassName\t",class_names.Utf8().c_str());
        Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
        div_node->setAttribute(html_names::kClassAttr, class_names);
        if(this->ToString() != "#document"){
            this->AppendChild(div_node); 
        } else{
            GetDocument().body()->AppendChild(div_node);
        }
    }
```


#### 源代码路径：third_party/blink/renderer/core/dom/element.h
+ 添加位置： 所有class定义之前
+ 功能说明： 定义日志类
```
    #include <iostream>
    #include <string.h>
    #include <fstream>
    #include <vector>
    #ifdef __APPLE__
            #include <sys/uio.h>
    #else
            #include <io.h>
    #endif

    #ifndef COMMAND_DEFINE_H
    #define COMMAND_DEFINE_H
    static const int MAX_STR_LEN = 4096;
    static const char * APIPREFIX = "[API]:";
    static const char * MDOMPREFIX = "[M_DOM]:";
    static const char * ORIGINDOMPREFIX = "[O_DOM]:";
    static const char * EXTENSIONPREFIX = "\n --------------------------\n[EXTENSION_ID]: ";
    #endif
    class BASE_EXPORT FinLoggerZ{
    public:    
        //默认构造函数
        FinLoggerZ();
        virtual ~FinLoggerZ();
    public:
        WTF::Vector<WTF::String>  GenerateLogFormat(WTF::String content, WTF::String origin);
        //直接记录DOM操作
        void Direct_Log(const char* API_name, WTF::Vector<WTF::String> obj);
        void Query_Log(const char* API_name, const char* content);
    private:
        //写文件的操作
        void LogFin(const char * strInfo);
    private:
        //写日志文件流
        FILE * m_pFileStream;
        //日志的路径
        //线程同步的临界区变量
        //pthread_mutex_t *pMutex;
    std::string m_strLogPath;
    void* m_pCritSection;
    };
```

#### 源代码路径：third_party/blink/renderer/core/dom/element.cc
+ 添加位置： 所有class定义之前
+ 功能说明： 实例化日志类
```
    #ifndef BASE_LOGGING_H_
    #include "/base/logging.h"
    #endif

    #include <iostream>
    #include <string.h>
    #include <fstream>
    #include <vector>
    #ifdef __APPLE__
            #include <sys/uio.h>
    #else
            #include <io.h>
    #endif

    #ifndef BASE_LOGGING_H_
        #include "/base/logging.h"
    #endif


    using namespace std;
    FinLoggerZ::FinLoggerZ()
    {
    //默认构造函数
    m_pFileStream = NULL;
    m_strLogPath ="/Users/myf/Desktop/chro/extension.log";
    pthread_mutex_t *pMutex = new pthread_mutex_t;
    pthread_mutex_init(pMutex, NULL);
    m_pCritSection = reinterpret_cast<void*>(pMutex);
    // use InitializeCriticalSection(&m_cs) instead in Windows'
    }

    //析构函数
    FinLoggerZ::~FinLoggerZ()
    {
    //DeleteCriticalSection(&m_cs); in Windows
    pthread_mutex_t *pMutex = reinterpret_cast<pthread_mutex_t*>(m_pCritSection);
    pthread_mutex_destroy(pMutex);
    delete pMutex;

    if(m_pFileStream)
        fclose(m_pFileStream);
    }

    //写操作的函数

    void FinLoggerZ::LogFin(const char* strInfo)
    {
    if(!strInfo)
        return;
    //进入临界区，EnterCriticalSection(&m_cs); in Windows
    pthread_mutex_lock(reinterpret_cast<pthread_mutex_t*>(m_pCritSection));
    //若文件流没有打开，则重新打开
    if(!m_pFileStream)
        {
        char temp[1024] = {0};
        strcat(temp, m_strLogPath.c_str());
        m_pFileStream = fopen(temp, "a+");
        if(!m_pFileStream)
        {
            return;
        }
        }
        //写日志信息到文件流
        DVLOG(0)<<strInfo;
        fprintf(m_pFileStream, "%s\n", strInfo);
        fflush(m_pFileStream);
        //离开临界区, LeaveCriticalSection(&m_cs); in Windows
        pthread_mutex_unlock(reinterpret_cast<pthread_mutex_t*>(m_pCritSection));
    }


    WTF::Vector<WTF::String>  FinLoggerZ::GenerateLogFormat(WTF::String content, WTF::String origin){
    WTF::Vector<WTF::String> obj;
    obj.push_back(MDOMPREFIX);
    obj.push_back(content);
    obj.push_back(ORIGINDOMPREFIX);
    obj.push_back(origin);
    DVLOG(0)<< origin;
    
    return obj;
    }


    void FinLoggerZ::Direct_Log(const char* API_name, WTF::Vector<WTF::String> obj )
    {

    char pTemp[MAX_STR_LEN] = {0};
    strcpy(pTemp, APIPREFIX);
    strcpy(pTemp+strlen(pTemp), API_name);
    for(int i=0; i<4;i++){
        strcpy(pTemp+strlen(pTemp), obj[i].Ascii().c_str());
    }
    //写日志文件
    LogFin(pTemp);
    }

```


+ 添加位置： 函数```void Element::removeAttribute(const QualifiedName& name)```开头
+ 功能说明： 记录removeAttribute DOM Interface的关键参数
```
    FinLoggerZ * finlogger = new FinLoggerZ();
    WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(name.LocalName(),name.LocalName());
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
        finlogger->Direct_Log("removeAttribute", obj);
    }
```




+ 添加位置： 函数```void Element::setAttribute(const QualifiedName& name,const String& string,ExceptionState& exception_state)```开头
+ 功能说明： 记录setAttribute DOM Interface的关键参数
```
    FinLoggerZ * finlogger = new FinLoggerZ();
    WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(name.LocalName()+string, DynamicTo<Element>(this)->outerHTML());
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
        finlogger->Direct_Log("SetAttribute", obj);
    }
```



+ 添加位置： 函数```Attr* Element::removeAttributeNode(Attr* attr, ExceptionState& exception_state)```开头
+ 功能说明： 记录removeAttributeNode DOM Interface的关键参数
```
    FinLoggerZ * finlogger = new FinLoggerZ();
    WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(attr->GetQualifiedName().ToString(), DynamicTo<Element>(this)->outerHTML());
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
        finlogger->Direct_Log("removeAttributeNode", obj);
    }
```

+ 添加位置： 函数```void Element::SetInnerHTMLInternal(const String& html, bool include_shadow_roots, ExceptionState& exception_state)```的```if (auto* template_element = DynamicTo<HTMLTemplateElement>(*this))```语句之前
+ 功能说明： 记录所有jQuery元素添加API，以及InnterHTML DOM Interface的关键参数
```
    FinLoggerZ * finlogger = new FinLoggerZ();
    WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(html, DynamicTo<Element>(container)->outerHTML());
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
        finlogger->Direct_Log("SetInnerHTML", obj);
    }
```
+ 添加位置：函数```void Element::setOuterHTML(const String& html, ExceptionState& exception_state) ```的```Node* p = parentNode();```语句之后
+ 功能说明： 记录setOuterHTML DOM Interface的关键参数
```
    FinLoggerZ * finlogger = new FinLoggerZ();
    WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(html, DynamicTo<Element>(p)->outerHTML());
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
        finlogger->Direct_Log("SetOuterHTML", obj);
    }  
```


+ 添加位置：函数```Node* Element::InsertAdjacent(const String& where, Node* new_child,ExceptionState& exception_state)```开头
+ 功能说明： 记录InsertAdjacent DOM Interface的关键参数
```
    FinLoggerZ * finlogger = new FinLoggerZ();
    WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(DynamicTo<Element>(new_child)->outerHTML(),where);
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
        finlogger->Direct_Log("InsertAdjacent", obj);
    }  
```
+ 添加位置：函数```Element* Element::insertAdjacentElement(const String& where, Element* new_child, ExceptionState& exception_state)```开头
+ 功能说明： 记录insertAdjacentElement DOM Interface的关键参数
```
    FinLoggerZ * finlogger = new FinLoggerZ();
    WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(DynamicTo<Element>(new_child)->outerHTML(),where);
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
        finlogger->Direct_Log("InsertAdjacentElement", obj);
    } 
```

+ 添加位置：函数```void Element::insertAdjacentText(const String& where, const String& text, ExceptionState& exception_state) ```开头
+ 功能说明： 记录insertAdjacentText DOM Interface的关键参数
```
    FinLoggerZ * finlogger = new FinLoggerZ();
    WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(text,where);
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
        finlogger->Direct_Log("InsertAdjacentText", obj);
    } 
```

+ 添加位置：函数```void Element::insertAdjacentHTML(const String& where, const String& markup, ExceptionState& exception_state) ```的```Node* context_node = ContextNodeForInsertion(where, this, exception_state);```语句后
+ 功能说明： 记录insertAdjacentHTML DOM Interface的关键参数
```
    FinLoggerZ * finlogger = new FinLoggerZ();
    WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(markup,where);
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
        finlogger->Direct_Log("InsertAdjacentHTML", obj);
    }  
```





#### 源代码路径：third_party/blink/renderer/core/dom/node.h
+ 添加位置： 所有class定义之前
+ 功能说明： 定义文件类
```
    #include <iostream>
    #include <string.h>
    #include <fstream>
    #include <vector>
    #ifdef __APPLE__
            #include <sys/uio.h>
    #else
            #include <io.h>
    #endif

    #ifndef COMMAND_DEFINE_H
    #define COMMAND_DEFINE_H
    static const int MAX_STR_LEN = 4096;
    static const char * APIPREFIX = "[API]:";
    static const char * MDOMPREFIX = "[M_DOM]:";
    static const char * ORIGINDOMPREFIX = "[O_DOM]:";
    static const char * EXTENSIONPREFIX = "\n --------------------------\n[EXTENSION_ID]: ";
    #endif

    class BASE_EXPORT FinLoggerY{
    public:    
        //默认构造函数
        FinLoggerY();
        virtual ~FinLoggerY();
    public:
        WTF::Vector<WTF::String>  GenerateLogFormat(WTF::String content, WTF::String origin);
        //直接记录DOM操作
        void Direct_Log(const char* API_name, WTF::Vector<WTF::String> obj);
    private:
        //写文件的操作
        void LogFin(const char * strInfo);
    private:
        //写日志文件流
        FILE * m_pFileStream;
        //日志的路径
        //线程同步的临界区变量
        //pthread_mutex_t *pMutex;
    std::string m_strLogPath;
    void* m_pCritSection;
    };
```

#### 源代码路径：third_party/blink/renderer/core/dom/node.cc
+ 添加位置： 所有class定义之前
+ 功能说明： 实例化日志类
```
    #include <stdarg.h>
    #include <iostream> 
    #include <stddef.h>
    #include <stdio.h>
    #include <string.h>
    #include <fstream>
    #include <vector>
    #include <iterator>
    #include <memory>
    #include <set>
    #include <utility>
    #ifdef __APPLE__
            #include <sys/uio.h>
    #else
            #include <io.h>
    #endif

    #ifndef BASE_LOGGING_H_
    #include "/base/logging.h"
#endif

using namespace std;

FinLoggerY::FinLoggerY()
{
  //默认构造函数
  m_pFileStream = NULL;
  m_strLogPath = "/Users/myf/Desktop/chro/extension.log";
  pthread_mutex_t *pMutex = new pthread_mutex_t;
  pthread_mutex_init(pMutex, NULL);
  m_pCritSection = reinterpret_cast<void*>(pMutex);
  // use InitializeCriticalSection(&m_cs) instead in Windows'
}

//析构函数
FinLoggerY::~FinLoggerY()
{
  //DeleteCriticalSection(&m_cs); in Windows
  pthread_mutex_t *pMutex = reinterpret_cast<pthread_mutex_t*>(m_pCritSection);
  pthread_mutex_destroy(pMutex);
  delete pMutex;

  if(m_pFileStream)
    fclose(m_pFileStream);
}

//写操作的函数

void FinLoggerY::LogFin(const char* strInfo)
{
  if(!strInfo)
    return;
  //进入临界区，EnterCriticalSection(&m_cs); in Windows
  pthread_mutex_lock(reinterpret_cast<pthread_mutex_t*>(m_pCritSection));
  //若文件流没有打开，则重新打开
  if(!m_pFileStream)
    {
      char temp[1024] = {0};
      strcat(temp, m_strLogPath);
      m_pFileStream = fopen(temp, "a+");
      if(!m_pFileStream)
      {
        return;
      }
    }
    //写日志信息到文件流
    DVLOG(0)<<strInfo;
    fprintf(m_pFileStream, "%s\n", strInfo);
    fflush(m_pFileStream);
    //离开临界区, LeaveCriticalSection(&m_cs); in Windows
    pthread_mutex_unlock(reinterpret_cast<pthread_mutex_t*>(m_pCritSection));
}


WTF::Vector<WTF::String>  FinLoggerY::GenerateLogFormat(WTF::String content, WTF::String origin){
  WTF::Vector<WTF::String> obj;
  obj.push_back(MDOMPREFIX);
  obj.push_back(content);
  obj.push_back(ORIGINDOMPREFIX);
  obj.push_back(origin);
  DVLOG(0)<< origin;
  
  return obj;
}


void FinLoggerY::Direct_Log(const char* API_name, WTF::Vector<WTF::String> obj )
{

  char pTemp[MAX_STR_LEN] = {0};
  strcpy(pTemp, APIPREFIX);
  strcpy(pTemp+strlen(pTemp), API_name);
  for(int i=0; i<4;i++){
    strcpy(pTemp+strlen(pTemp), obj[i].Ascii().c_str());
  }
  //写日志文件
  LogFin(pTemp);
}
```


+ 添加位置： 函数```Node* Node::appendChild(Node* new_child, ExceptionState& exception_state) ```内部
+ 功能说明： 记录AppendChild DOM Interface的关键参数
+ 修改说明：将以下的原始代码用新代码替换
原始代码
```
 if (this_node)
    return this_node->AppendChild(new_child, exception_state);
```
替换为：
```
if (this_node){
    FinLoggerY * finlogger = new FinLoggerY();
    WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(DynamicTo<Element>(new_child)->outerHTML(), DynamicTo<Element>(this_node)->outerHTML());
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
      if (!(new_child->IsInTreeScope())){
        finlogger->Direct_Log("AppendChild", obj);
      }
    }
    return this_node->AppendChild(new_child, exception_state);
}
```





#### 源代码路径：third_party/blink/renderer/core/dom/tree_scope.h
+ 添加位置： 所有class定义之前
+ 功能说明： 定义日志类
```
    #include <vector>
    #include <stdarg.h>
    #include <iostream> 
    #include <stddef.h>
    #include <stdio.h>
    #include <string.h>
    #include <fstream>
    #include <iterator>
    #include <memory>
    #include <set>
    #include <utility>
    #ifdef __APPLE__
            #include <sys/uio.h>
    #else
            #include <io.h>
    #endif
    #ifndef COMMAND_DEFINE_H
    #define COMMAND_DEFINE_H
    static const int MAX_STR_LEN = 4096;
    static const char * APIPREFIX = "[API]:";
    static const char * MDOMPREFIX = "[M_DOM]:";
    static const char * ORIGINDOMPREFIX = "[O_DOM]:";
    static const char * EXTENSIONPREFIX = "\n --------------------------\n[EXTENSION_ID]: ";
    #endif
    class BASE_EXPORT FinLoggerW{
    public:    
        //默认构造函数
        FinLoggerW();
        //构造函数
        //FinLogger();
        virtual ~FinLoggerW();
    public:
        void Query_Log(const char* API_name, const char* content);
    private:
        //写文件的操作
        void LogFin(const char * strInfo);
    private:
        //写日志文件流
        FILE * m_pFileStream;
        //日志的路径
        //线程同步的临界区变量
        //pthread_mutex_t *pMutex;
    std::string m_strLogPath;
    void* m_pCritSection;
    
    };
```


#### 源代码路径：third_party/blink/renderer/core/dom/tree_scope.cc
+ 添加位置： 在本文件原定义的所有class之前
+ 功能说明： 实例化日志类
```
    #include <iostream>
    #include <string.h>
    #include <fstream>
    #include <vector>
    #ifdef __APPLE__
            #include <sys/uio.h>
    #else
            #include <io.h>
    #endif

    using namespace std;
    FinLoggerW::FinLoggerW()
    {
    //默认构造函数
    m_strLogPath = "/Users/myf/Desktop/chro/extension.log";
    m_pFileStream = NULL;
    pthread_mutex_t *pMutex = new pthread_mutex_t;
    pthread_mutex_init(pMutex, NULL);
    m_pCritSection = reinterpret_cast<void*>(pMutex);
    // use InitializeCriticalSection(&m_cs) instead in Windows'
    }

    //析构函数
    FinLoggerW::~FinLoggerW()
    {
    //DeleteCriticalSection(&m_cs); in Windows
    pthread_mutex_t *pMutex = reinterpret_cast<pthread_mutex_t*>(m_pCritSection);
    pthread_mutex_destroy(pMutex);
    delete pMutex;

    if(m_pFileStream)
        fclose(m_pFileStream);
    }

    //写操作的函数
    void FinLoggerW::LogFin(const char* strInfo)
    {
    if(!strInfo)
        return;
    //进入临界区，EnterCriticalSection(&m_cs); in Windows
    pthread_mutex_lock(reinterpret_cast<pthread_mutex_t*>(m_pCritSection));
    //若文件流没有打开，则重新打开
    if(!m_pFileStream)
        {
        char temp[1024] = {0};
        strcat(temp, m_strLogPath.c_str());
        m_pFileStream = fopen(temp, "a+");
        if(!m_pFileStream)
        {
            return;
        }
        }
        DVLOG(0) << strInfo;
        //写日志信息到文件流
        fprintf(m_pFileStream, "%s\n", strInfo);
        fflush(m_pFileStream);
        //离开临界区, LeaveCriticalSection(&m_cs); in Windows
        pthread_mutex_unlock(reinterpret_cast<pthread_mutex_t*>(m_pCritSection));
    }

    void FinLoggerW::Query_Log(const char* API_name, const char* content)
    {
    if(!content)
        return;
    char pTemp[MAX_STR_LEN] = {0};
    strcpy(pTemp, APIPREFIX);
    strcpy(pTemp+strlen(pTemp), API_name);
    strcpy(pTemp + strlen(pTemp), content);
    //写日志文件
    LogFin(pTemp);
    }
```

+ 添加位置： 函数```Element* TreeScope::getElementById(const AtomicString& element_id) ```开头
+ 功能说明： 记录getElementById关键参数，并在没有符合条件对象时创建
```
    FinLoggerW * finlogger = new FinLoggerW();
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if ((executing_window == "localhost")){
        if (!GetDocument().HasElementWithId(element_id)){
            if ((element_id!="___gatsby")&& (element_id!="__next")&& (element_id != "react-root")){
                finlogger->Query_Log("getElementsById\t",element_id.Utf8().c_str());
                Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
                div_node->setAttribute(html_names::kIdAttr, element_id);
                GetDocument().body()->AppendChild(div_node);
            }
        }
    }
```

#### 源代码路径：third_party/blink/renderer/core/editing/frame_caret.cc
+ 添加位置： 函数```void FrameCaret::UpdateStyleAndLayoutIfNeeded() ```开头
```
    frame_->GetDocument()->UpdateStyleAndLayout(DocumentUpdateReason::kJavaScript);
```


#### 源代码路径：third_party/blink/renderer/core/html/html_element.h
+ 添加位置： 所有class定义之前
+ 功能说明： 定义日志类
```
    #ifndef COMMAND_DEFINE_H
    #define COMMAND_DEFINE_H
    static const int MAX_STR_LEN = 4096;
    static const char * APIPREFIX = "[API]:";
    static const char * MDOMPREFIX = "[M_DOM]:";
    static const char * ORIGINDOMPREFIX = "[O_DOM]:";
    static const char * EXTENSIONPREFIX = "\n --------------------------\n[EXTENSION_ID]: ";
    #endif
    class BASE_EXPORT FinLoggerN{
    public:    
        //默认构造函数
        FinLoggerN();
        //构造函数
        //FinLogger();
        virtual ~FinLoggerN();
    public:
        WTF::Vector<WTF::String>  GenerateLogFormat(WTF::String content, WTF::String origin);
        //直接记录DOM操作
        void Direct_Log(const char* API_name, WTF::Vector<WTF::String> obj);
    private:
        //写文件的操作
        void LogFin(const char * strInfo);
    private:
        //写日志文件流
        FILE * m_pFileStream;
        //日志的路径
        //线程同步的临界区变量
        //pthread_mutex_t *pMutex;
    std::string m_strLogPath;
    void* m_pCritSection;
    
    };
```


#### 源代码路径：third_party/blink/renderer/core/dom/tree_scope.cc
+ 添加位置： 在本文件原定义的所有class之前
+ 功能说明： 实例化日志类
```
    #include <vector>
    #include <stdarg.h>
    #include <iostream> 
    #include <stddef.h>
    #include <stdio.h>
    #include <string.h>
    #include <fstream>
    #include <iterator>
    #include <memory>
    #include <set>
    #include <utility>
    #ifdef __APPLE__
            #include <sys/uio.h>
    #else
            #include <io.h>
    #endif

    using namespace std;
    FinLoggerN::FinLoggerN()
    {
    //默认构造函数
    m_pFileStream = NULL;
    m_strLogPath ="/Users/myf/Desktop/chro/extension.log";
    pthread_mutex_t *pMutex = new pthread_mutex_t;
    pthread_mutex_init(pMutex, NULL);
    m_pCritSection = reinterpret_cast<void*>(pMutex);
    // use InitializeCriticalSection(&m_cs) instead in Windows'
    }
    //析构函数
    FinLoggerN::~FinLoggerN()
    {
    //DeleteCriticalSection(&m_cs); in Windows
    pthread_mutex_t *pMutex = reinterpret_cast<pthread_mutex_t*>(m_pCritSection);
    pthread_mutex_destroy(pMutex);
    delete pMutex;

    if(m_pFileStream)
        fclose(m_pFileStream);
    }

    //写操作的函数

    void FinLoggerN::LogFin(const char* strInfo)
    {
    if(!strInfo)
        return;
    //进入临界区，EnterCriticalSection(&m_cs); in Windows
    pthread_mutex_lock(reinterpret_cast<pthread_mutex_t*>(m_pCritSection));
    //若文件流没有打开，则重新打开
    if(!m_pFileStream)
        {
        char temp[1024] = {0};
        strcat(temp, m_strLogPath.c_str());
        m_pFileStream = fopen(temp, "a+");
        if(!m_pFileStream)
        {
            return;
        }
        }
        DVLOG(0) << strInfo;
        //写日志信息到文件流
        fprintf(m_pFileStream, "%s\n", strInfo);
        fflush(m_pFileStream);
        //离开临界区, LeaveCriticalSection(&m_cs); in Windows
        pthread_mutex_unlock(reinterpret_cast<pthread_mutex_t*>(m_pCritSection));
    }



    WTF::Vector<WTF::String>  FinLoggerN::GenerateLogFormat(WTF::String content, WTF::String origin){
    WTF::Vector<WTF::String> obj;
    obj.push_back(MDOMPREFIX);
    obj.push_back(content);
    obj.push_back(ORIGINDOMPREFIX);
    obj.push_back(origin);
    return obj;
    }

    void FinLoggerN::Direct_Log(const char* API_name, WTF::Vector<WTF::String> obj )
    {

    char pTemp[MAX_STR_LEN] = {0};
    strcpy(pTemp, APIPREFIX);
    strcpy(pTemp+strlen(pTemp), API_name);
    for(int i=0; i<4;i++){
        strcpy(pTemp+strlen(pTemp), obj[i].Ascii().c_str());
    }
    //写日志文件
    LogFin(pTemp);
    }
```

+ 添加位置：函数```void HTMLElement::setInnerText(const String& text, ExceptionState& exception_state) ```开头
+ 功能说明： 记录setInnerText DOM Interface的关键参数
```
    FinLoggerN * finlogger = new FinLoggerN();
    WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(text,DynamicTo<Element>(this)->outerHTML());
    String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
    if (executing_window == "localhost"){
        finlogger->Direct_Log("SetInnerText", obj);
    } 
```

+ 添加位置：函数```void HTMLElement::setOuterText(const String& text, ExceptionState& exception_state)```的```ContainerNode* parent = parentNode();```语句之后
+ 功能说明： 记录setOuterText DOM Interface的关键参数
```
  FinLoggerN * finlogger = new FinLoggerN();
  WTF::Vector<WTF::String> obj = finlogger->GenerateLogFormat(text,DynamicTo<Element>(parent)->outerHTML());
  String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
  if (executing_window == "localhost"){
        finlogger->Direct_Log("SetOuterText", obj);
  } 
```

