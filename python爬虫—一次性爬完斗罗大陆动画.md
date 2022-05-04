# python爬虫—一次性爬完斗罗大陆动画



## 写在前面

看完b站大佬Python-小旋风的爬虫教学（[【Python爬虫教程】花12800买的Python爬虫全套教程2022完整版现分享给大家！（学完可就业）_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1UY411V7aA?p=43&spm_id_from=333.788.top_right_bar_window_history.content.click)）后，想着拿自己最近一直在追的动画斗罗大陆练手。200多级的动画一次性爬完之后的感觉是真的棒！



## 思路

素材的选择当然是樱花动漫啦，里面的资源还是很多的，适合白嫖党。这里要记下它的网址（http://www.dmh8.com/）

![素材](C:\Users\RuYi\AppData\Roaming\Typora\typora-user-images\image-20220504151607126.png)



接下来的主角当然是选择的动漫了，这里我选的是斗罗大陆。由于网站广告过多，咱就截取最重要的部分了啊（http://www.dmh8.com/player/4102-0-0.html）

![image-20220504152051270](C:\Users\RuYi\AppData\Roaming\Typora\typora-user-images\image-20220504152051270.png)



通过F12（有些电脑是Fn+F12）或者鼠标右击查看网页源代码,爬视频我们需要找到video的网页链接或者m3u8文件（大部分的视频是存储在m3u8文件中）的地址，这里是m3u8文件

![image-20220504153048096](C:\Users\RuYi\AppData\Roaming\Typora\typora-user-images\image-20220504153048096.png)

这里的m3u8乍一看不像是一个网址(源代码中的网址通常是蓝色下划线的超链接)，但是仔细看你就会发现（url":"https:\/\/iqiyi.sd-play.com\/20211017\/TVRRrTFY\/index.m3u8"）这不就是一个网址吗



访问这个网址之后会下载一个文件

![image-20220504153731555](C:\Users\RuYi\AppData\Roaming\Typora\typora-user-images\image-20220504153731555.png)

注意最后一行，它和我们刚刚下载m3u8文件的网址有一点相似，我们把它和（https:\/\/iqiyi.sd-play.com/\）拼接起来，再访问进去。得到了一个新的m3u8文件



![image-20220504154301569](C:\Users\RuYi\AppData\Roaming\Typora\typora-user-images\image-20220504154301569.png)



这里面就是我们需要的视频资源了！我们再通过网站调试工具确认一下，对（http://www.dmh8.com/player/4102-0-0.html）按下F12跳转到调试工具，选择Network选项（有的浏览器是网络选项）



![image-20220504154711527](C:\Users\RuYi\AppData\Roaming\Typora\typora-user-images\image-20220504154711527.png)



在视频播放的同时你会发现网页加载了两个m3u8文件

![image-20220504154539650](C:\Users\RuYi\AppData\Roaming\Typora\typora-user-images\image-20220504154539650.png)



![image-20220504155007138](C:\Users\RuYi\AppData\Roaming\Typora\typora-user-images\image-20220504155007138.png)



![image-20220504155025324](C:\Users\RuYi\AppData\Roaming\Typora\typora-user-images\image-20220504155025324.png)



是不是和我们下载的txt文件里的内容一样呢，里面的每一个链接就是我们需要的视频资源了。这里注意一下上图的第6行代码，它的意思是该文件使用了AES加密，密钥在后面的url中，我们之后的解密会用到它。所以大致的思路就有了：

1. 获取樱花动漫中斗罗大陆的url
2. 获取第一层m3u8文件
3. 获取第二层m3u8文件
4. 下载ts视频片段
5. 解密
6. 合并视频

## 实战



### 获取url

```python
url=f'http://www.dmh8.com/player/4102-0-{i}.html'
```

这里的url就是我们访问斗罗大陆第一集的那个链接，里面的i表示第i-1集。



### 获取first_m3u8

```python
def get_iframe_src(url):
    resp = requests.get(url)
    result = BeautifulSoup(resp.text, 'html.parser')
    result = result.find("div", class_='embed-responsive clearfix')
    result = result.find("script")
    str = result.text.split('url":"')
    str = str[1].split('","url_next')
    str = str[0].replace('\\', '')
    return str
```

这里我用的是BeautifulSoup,也可以用正则或者Xpath。前端知识有限，处理了好几次字符串，还请见谅。



### 获取second_m3u8

```python
m3u8_url=iframe_src.split('/index.m3u8')[0]+'/1200kb/hls/index.m3u8'
```

第一层m3u8文件中的地址+上域名，简单的字符串拼接



### 下载视频片段

```python
async def aio_download(src,i):
    tasks=[]
    #timeout = aiohttp.ClientTimeout(total=800)  # 将超时时间设置为600秒
    connector = aiohttp.TCPConnector(limit=10)  # 将并发数量降低

    async with aiohttp.ClientSession(connector=connector) as session:
         async with aiofiles.open(f"斗罗大陆{i+1}",mode="r",encoding="utf-8") as f:
             async for line in f:
                if line.startswith("#"):
                    continue
                line=line.strip()
                name=line.split("hls/")[1]
                task=asyncio.create_task(down_ts(line,name,session))
                tasks.append(task)
             await asyncio.wait(tasks)
                
                        
async def down_ts(url,name,session):
    async with  session.get(url) as resp:
        async with aiofiles.open(f"video/{name}",mode="wb") as f:
            await f.write(await resp.content.read())
    #print(f"{name}下载完毕！")                     
```

由于视频片段较多，这边上了一个异步协程，加快下载速度。也就是这个异步，给后续调试增加了几个level！！！

### 解密

```python
async def aio_dec(key,i):
    tasks=[]
    async with aiofiles.open(f"斗罗大陆{i+1}",mode="r",encoding="utf-8") as f:
        async for line in f:
            if line.startswith("#"):
                continue
            line = line.strip()
            name = line.split("hls/")[1]
            task = asyncio.create_task(dec_ts(name,key))
            tasks.append(task)
        await asyncio.wait(tasks)
        
async def dec_ts(name,key):
    aes=AES.new(key=key,IV=b'0000000000000000',mode=AES.MODE_CBC)
    async with aiofiles.open(f"video/{name}",mode="rb") as f1,\
        aiofiles.open(f"video2/{name}",mode="wb") as f2:
        bs=await f1.read()
        await f2.write(aes.decrypt(bs))
    #print(f"{name}处理完毕")
```

解密算法加文本读写操作，因为数量庞大，同样是异步。



### 合并

```python
def merge_ts(i):
    combine=[]
    lis=[]
    with open(f"斗罗大陆{i+1}",mode="r",encoding='utf-8') as f:
        for line in f:
            if line.startswith("#"):
                continue
            line=line.strip()
            name = line.split("hls/")[1]
            combine.append(name)
    s="+".join(rename_ts(combine))
    s=f"copy /b {s} {i+1}.mp4"
    os.chdir('E:\\pythonProject')
    os.system(s)
    print(f"{i+1} end!")
```

合并这一块调试的时候也碰到了麻烦，应该是字符串太长了。

在计算机上运行 Microsoft Windows XP 或更高版本，可以在命令提示符下使用的字符串的最大的长度 8191 个字符。
在运行 Microsoft Windows 2000 或 Windows NT 4.0 的计算机上, 将最大长度可以在命令提示符下使用的字符串的为 2047 个字符。

微软官方(https://support.microsoft.com/zh-cn/kb/830473)

后来修改了每个ts文件的文件名，再合并，问题就解决了！

### 关于调试

调试的时候主要出现了两个问题，一个是异步下载的时候总是断开连接，还有一个就是文件合并报错。

![image-20220504164547548](C:\Users\RuYi\AppData\Roaming\Typora\typora-user-images\image-20220504164547548.png)

网上找了一些相关的解决办法([aiohttp.client_exceptions.ServerDisconnectedError: Server disconnected_小玖工作坊的博客-CSDN博客](https://blog.csdn.net/zhb_feng/article/details/118081444))降低并发数量确实有一定效果，但是我最后将并发数量降到5还会时不时断开连接！！！

所以我在这之后又写了一个方法，对于因断开连接没有下载下来的ts文件，单独下载！虽然方法有点笨，但是问题解决了！

```python
def Is_down(lst,i):
    #处理异步连接中断，漏下的几个ts文件
    #real_lst=[]
    flag=0
    with open(f"斗罗大陆{i+1}",mode="r",encoding='utf-8') as f:
        for line in f:
            if line.startswith("#"):
                continue
            else:#判断当前ts文件是否已经下载
                line = line.strip()
                name=line.split("hls/")[1]
                for file in lst:
                    if(file==name):
                        flag=1
                        break
                    #print(f"file: {file}  name: {name}")
                if flag==0:
                    downsecond_ts(line,name)
            flag=0
```

文件合并报错这里就不显示了，因为编码格式不同，报的错都是乱码！！我也只是一个一个猜，最后通过缩短文件名，缩短了合并的字符串最后通过的。总之，第一个爬虫小项目顺利完成！