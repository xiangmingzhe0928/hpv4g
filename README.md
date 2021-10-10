# hpv4g 
## 约苗疫苗秒杀(只做学习研究使用)
```
    只为给女朋友抢一针疫苗,当好舔狗
```

### precondition

   - `python3.8+`

   - 使用`Fiddler`等抓包工具抓取约苗小程序请求header
        - tk 
        - cookie
        <img width="509" alt="2" src="https://user-images.githubusercontent.com/7719370/99932763-06f41000-2d94-11eb-80b6-3c76b112db6d.png">
### use

   - `hpv4g.py`执行秒杀 `-h`可选参数
      - 位置参数(固定必传参数)
        - `tk` 抓包获取的tk数据
        - `cookie` 抓包获取的cookie数据
      - 可选参数
        - `-mw[--max_workers]` 最大秒杀线程数(默认使用min(32, cpu_count + 4))
        - `-rc[--region_code]` 指定区域编码(約苗使用4位行政区域CODE 默认成都:5101)
        - `-reload_cache` 
         本脚本不支持指定 **某一只** 疫苗进行秒杀。而是对当前城市所有可秒杀(**即5S内可开始秒杀**)疫苗一起秒杀。
        因此秒杀前会缓存当前城市可秒杀疫苗列表到 `cache/vaccines_xxx.json`中。真正执行秒杀时从本地获取疫苗列表(减少受Server端降级策略影响)。
        `-reload_cache`参数用于指定本次秒杀需要更新缓存列表(场景:第一天执行秒杀后缓存了数据,第二天再次秒杀时需要重新加载最新疫苗列表一次)
        - `-sp[--single_point]`只秒杀单个疫苗[即所有线程秒杀同一个疫苗] 默认不开启该参数则所有线程分配秒杀所有可秒杀疫苗
        - `-pi`[(`--proxy_ip`)] 开启IP代理池 默认不开启
        测试发现使用IP代理池后 对服务端访问频率限制并没有太明显的效果(仍然大量的请求502、操作频繁...), 初步判断服务端是用 【帐号】 维度的限制(有条件可以使用多个微信帐号同时秒杀)
        - `--log` 日志级别 默认WARNING
        
   - `scan_vaccine.py` 扫描所有城市 检索当前有疫苗列表的城市(想想没啥实际X用)  生成本地cache/vaccines.json文件
        ```
        # tkstring cookiestring 为抓包得到的tk cookie
        scan_vaccine.py tkstring cookiestring
        ```
      
<img width="889" alt="1" src="https://user-images.githubusercontent.com/7719370/99932751-f9d72100-2d93-11eb-8840-1110e0be3136.png">

---
### :purple_heart:
个人能力有限且小程序经常更新
欢迎**Star** **Fork**

---
### Github上其他的一些Hpv疫苗秒杀库 方便大家查找（顺序不分先后）
- `GO` https://github.com/xjblszyy/JiuJia 
- `JAVA` https://github.com/lyrric/seckill
