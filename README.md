# hpv4g 
## 约苗疫苗秒杀(只做学习研究使用)
```
    只为了给女朋友抢一针疫苗,当好舔狗
```

### precondition

   - 使用`Fiddler`等抓包工具抓取约苗小程序请求header
        - tk
        - cookie
        
### use


   - 执行秒杀 使用-h参看可选参数
       ```
        # tkstring cookiestring 为抓包得到的tk cookie
        hpv4g.py tkstring cookiestring
       ```
   - 扫描所有城市疫苗列表(没啥实际X用) 生成本地cache/vaccines.json文件
        ```
        # tkstring cookiestring 为抓包得到的tk cookie
        scan_vaccine.py tkstring cookiestring
        ```
        
### 一些废话
    能力有限保证不了成功率，只是信赖机器比单身手速更快而已。而且小程序不停更新(防刷、加盐Header...)。
    本人也确实秒杀成功过,但在小程序更新后成功率大大降低          