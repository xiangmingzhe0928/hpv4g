# hpv4g 
## 约苗疫苗秒杀(只做学习研究使用)
```
    只为给女朋友抢一针疫苗,当好舔狗
```

### precondition

   - 使用`Fiddler`等抓包工具抓取约苗小程序请求header
        - tk
        - cookie
        <img width="509" alt="2" src="https://user-images.githubusercontent.com/7719370/99932763-06f41000-2d94-11eb-80b6-3c76b112db6d.png">
### use


   - `hpv4g.py`执行秒杀 `-h`可选参数
       ```
        # tkstring cookiestring 为抓包得到的tk cookie
        hpv4g.py tkstring cookiestring
       ```
   - `scan_vaccine.py` 扫描所有城市 检索当前有疫苗列表的城市(想想没啥实际X用)  生成本地cache/vaccines.json文件
        ```
        # tkstring cookiestring 为抓包得到的tk cookie
        scan_vaccine.py tkstring cookiestring
        ```
      
<img width="889" alt="1" src="https://user-images.githubusercontent.com/7719370/99932751-f9d72100-2d93-11eb-8840-1110e0be3136.png">
