___扩展程序启动___
---------------
使用--no-sandbox参数使日志能被记录到本地文件
```[chromium本地存储路径]/src/out/Release/Chromium.app/Contents/MacOS/Chromium --no-sandbox```

___开启扩展测试单元___
---------------
#### /chrome/browser/extensions/extension_service.cc

在void ExtensionService::EnableExtension中，将extension_id.c_str()记录在日志文件

___DOM方法插桩___
---------------
#### GetElementById方法
+ 目录： /third_party/blink/renderer/core/dom/element.cc
+ 函数：void Element::SetInnerHTMLInternal
```
fputs("[InnerHTML]",fp);
          DVLOG(0) << "[InnerHTML]"<< html.Utf8();   
          fputs(html.Utf8().c_str(),fp);
          fputs("[to]",fp);
          fputs("(type)",fp);
          fputs(container->nodeName().Utf8().c_str(),fp);
```


___备注___
---------------

#### 判断DOM活动上下文
Node包括网页范围以及treescope范围（就是浏览器本身的），因此在判断是否记录dom变化时，可以通过以下代码判断执行环境是不是在网页内

```
String executing_window = GetDocument().GetExecutionContext()->GetSecurityOrigin()->Domain();
 if (executing_window == "localhost"){
         [代码]
 }
 ```
 
#### 日志记录功能 
 日志记录代码（注意 windows和macos不同，这里仅记录macos的方法）      
 ```
        FILE *fp = NULL;
        fp = fopen("[日志记录文件的绝对路径]","a+");
        if (fp != NULL)
        {
          fputs("[GetElementbyID]",fp);
          DVLOG(0) << "[GetElementbyID1]"<< element_id.Utf8();
          fputs(element_id.Utf8().c_str(),fp);
          fputs("\n",fp);
          fputs("Create Accordingly",fp);
          fputs("\n",fp);
          fclose(fp);
          }else{
          int errNum = errno;
          printf("open fail errno = %d reason = %s \n",errNum,strerror(errno));
          }
          Element* div_node =  RootNode().GetDocument().CreateRawElement(html_names::kDivTag);
          div_node->SetIdAttribute(element_id);
          GetDocument().body()->appendChild(div_node);
 ```
 
 #### 获取节点属性
```
       if (const auto* contain =DynamicTo<Element>(container)){
            if(contain->GetClassAttribute()){
              fputs("(class)",fp);
              fputs(contain->GetClassAttribute().Utf8().c_str(), fp);
            }
            if(contain->GetIdAttribute()){
              fputs("(id)",fp);
              fputs(contain->GetIdAttribute().Utf8().c_str(), fp);
            }
            if(contain->GetNameAttribute()){
              fputs("(name)",fp);
              fputs(contain->GetNameAttribute().Utf8().c_str(), fp);
            }    
          }
```
