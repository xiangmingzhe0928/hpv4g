# hpv4g 
基于`python`的用于 **`约苗`**小程序 HPV疫苗秒杀的脚本.

## 背景
`HPV`量太少了.女朋友抢购多次都没预约上,想试试能不能用脚本的方式帮忙秒杀。

## 使用
- 流程
    - 传入抓包获取的token,Cookie(基于微信小程序登录信息,需要使用`fiddler`等自行抓包)
    - 查询接种人信息
    - 查询待秒杀的疫苗列表
    - 等待秒杀开始
    - 多线程并发秒杀

- use
    ```
    hpv4g.py tkstring cookiestring
    # 使用-h参看可选参数
    ```
  

## ?
- 服务端做了频率限制,尚不确定是基于`Ip`还是秒杀人`ID`
  - 针对IP限制,目前加入了IP代理(使用免费的第三方API ref:https://github.com/jiangxianli/ProxyIpLib)
  - 针对ID限制, 还没想好怎么处理(疫苗秒杀比较特殊,只有秒杀本人才能接种)
