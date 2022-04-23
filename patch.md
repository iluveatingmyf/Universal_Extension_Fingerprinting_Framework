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

【注意】所有依据extension请求而新创建的元素，都会为其创建值为trigger的class属性，帮助区分真实的扩展行为


#### Append(only for Element)



#### InnerHTML方法(only for Element)
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
#### GetElementById方法(only for Document)
+ 目录： /third_party/blink/renderer/core/dom/tree_scope.cc
+ 函数：Element* TreeScope::getElementById


#### setInnerText()
+ 目录： /third_party/blink/renderer/core/html/html_element.cc
+ 函数：void HTMLElement::setInnerText


#### querySelector()
+ 目录： /third_party/blink/renderer/core/dom/container_node.cc
+ 函数：Element* ContainerNode::QuerySelector
```
  auto* context = MakeGarbageCollected<CSSParserContext>(
      kHTMLStandardMode, SecureContextMode::kInsecureContext);
  auto* sheet = MakeGarbageCollected<StyleSheetContents>(context);
  CSSTokenizer tokenizer(selectors);
  const auto tokens = tokenizer.TokenizeToEOF();
  CSSParserTokenRange range(tokens);
  CSSSelectorList list =
        CSSSelectorParser::ParseSelector(range, context, sheet);

  //记录queryselector的参数     
  FILE *fp = NULL;
  fp = fopen("/Users/myf/Desktop/chro/log.txt","a+");
  if (fp != NULL)
  {
    fputs("[QuerySelector]",fp);
    fputs(selectors.Utf8().c_str(),fp);
    fputs("\n", fp);
    fputs("[CreateAccordingly]",fp);
    fputs("\n", fp);
  }else{
        int errNum = errno;
        printf("open fail errno = %d reason = %s \n",errNum,strerror(errno));
  }
  
  
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
              DVLOG(0)<< ">";
              rela = "child";
              break;
            case CSSSelector::kDirectAdjacent: //+
              DVLOG(0)<< "+";
              rela = "dj";
              break;
            case CSSSelector::kSubSelector:
              rela = "sub";
              DVLOG(0) << "sub";
              //NOTREACHED();
              break;
            default:
              DVLOG(0) << "~ ";
              rela = "null";
              break;
          }
      }
      
      if(!(s->TagHistory())){
        break;
      }
    }
    VLOG(0) << depth;
    VLOG(0) << s;
    
    if( depth > 2 ) {break;}

    if (depth == 1){
      switch(ele) {
            case 0: {     
                bool flag= false;        
                if(s->Match() == CSSSelector::kId && rela == "sub"){
                  Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
                  div_node->setAttribute(html_names::kIdAttr, s->Value());
                  GetDocument().body()->appendChild(div_node);  
                  flag = true; 
                }
                if(s->Match() == CSSSelector::kClass && rela == "sub"){
                   Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
                    div_node->setAttribute(html_names::kClassAttr, s->Value());
                    GetDocument().body()->appendChild(div_node);
                    flag = true; 
                }
                if(s->IsAttributeSelector() && rela == "sub"){
                  Attr* attr = GetDocument().createAttribute(s->Attribute().LocalName(), ASSERT_NO_EXCEPTION);
                  attr->setValue("happy", ASSERT_NO_EXCEPTION);
                  Element* div_node =  GetDocument().CreateRawElement(html_names::kDivTag);
                  attr->AttachToElement(div_node, s->Attribute().LocalName());
                  GetDocument().body()->appendChild(div_node);
                  flag = true; 
                }
                if(!flag){break;}
                break;   
            }
            case 1: {
              if(other_one && rela == "sub"){  
                GetDocument().body()->appendChild(other_one);
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
                attr->setValue("happy", ASSERT_NO_EXCEPTION);
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
                attr->setValue("happy", ASSERT_NO_EXCEPTION);
                attr->AttachToElement(div_node, s2->Attribute().LocalName());
          }
          GetDocument().body()->appendChild(div_node);
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
                DVLOG(0) <<"attribute";
                DVLOG(0) << s2->Attribute().LocalName();
                Attr* attr = GetDocument().createAttribute(s2->Attribute().LocalName(), ASSERT_NO_EXCEPTION);
                DVLOG(0)<< attr;
                attr->setValue("happy", ASSERT_NO_EXCEPTION);
                DVLOG(0) << s2->Attribute().LocalName();
                other_one->setAttributeNode(attr, exception_state);
                DVLOG(0) << attr;
            }
            VLOG(0) << other_one;
            GetDocument().body()->appendChild(other_one);
            DVLOG(0)<<"success";
            break;       
        }
        case 2:{
          if(other_one && other_two){
                VLOG(0) << rela;
                if (rela == "des"){
                    other_one->appendChild(other_two);
                    GetDocument().body()->appendChild(other_one);
                  }
                if (rela =="child"){
                    VLOG(0) <<"?";
                    other_two->appendChild(other_one);
                    GetDocument().body()->appendChild(other_two);
                }
                if (rela == "dj"){
                    GetDocument().body()->appendChild(other_one);
                    GetDocument().body()->appendChild(other_two);
                }    

          }
          break;
        } 
    }}
  }

  

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
