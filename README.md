# hpv4g 
## 约苗疫苗秒杀(只做学习研究使用)
```
    只为给女朋友抢一针疫苗,当好舔狗
```

### precondition

   - 使用`Fiddler`等抓包工具抓取约苗小程序请求header
        - tk
        - cookie
        
### use


   - `hpv4g.py`执行秒杀 `-h`可选参数
       ```
        # tkstring cookiestring 为抓包得到的tk cookie
        hpv4g.py tkstring cookiestring
       ```
   - `scan_vaccine.py`扫描所有城市疫苗列表(没啥实际X用) 生成本地cache/vaccines.json文件
        ```
        # tkstring cookiestring 为抓包得到的tk cookie
        scan_vaccine.py tkstring cookiestring
        ```
      
