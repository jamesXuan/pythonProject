import requests
import asyncio
import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
import os

def get_iframe_src(url):
    resp = requests.get(url)
    result = BeautifulSoup(resp.text, 'html.parser')
    result = result.find("div", class_='embed-responsive clearfix') #获取div标签下，class属性为embed-responsive clearfix的字段
    result = result.find("script")   #这段字符串处理比较笨，就是粗暴的分解
    str = result.text.split('url":"')
    str = str[1].split('","url_next')
    str = str[0].replace('\\', '')
    return str

def get_key(url):
    resp=requests.get(url)
    return resp.text

def download_m3u8(src,name):
    resp=requests.get(src)
    with open(name,mode="wb") as f:
        f.write(resp.content)

async def down_ts(url,name,session):
    async with  session.get(url) as resp:
        async with aiofiles.open(f"video/{name}",mode="wb") as f:
            await f.write(await resp.content.read())
    #print(f"{name}下载完毕！")

async def dec_ts(name,key):
    aes=AES.new(key=key,IV=b'0000000000000000',mode=AES.MODE_CBC)
    async with aiofiles.open(f"video/{name}",mode="rb") as f1,\
        aiofiles.open(f"video2/{name}",mode="wb") as f2:
        bs=await f1.read()
        await f2.write(aes.decrypt(bs))#aes解密
    #print(f"{name}处理完毕")

async def aio_dec(key,i):
    tasks=[]
    #从第二个m3u8文件里获得文件名
    async with aiofiles.open(f"斗罗大陆{i+1}",mode="r",encoding="utf-8") as f:
        async for line in f:
            if line.startswith("#"):
                continue
            line = line.strip()
            name = line.split("hls/")[1]
            task = asyncio.create_task(dec_ts(name,key))
            tasks.append(task)
        await asyncio.wait(tasks)

def rename_ts(list):
    #合并的ts文件名太长，给每个ts文件重命名
    lst=[]
    os.chdir('E:\\pythonProject\\video2')
    i=0;
    for line in list:
        i=i+1
        os.rename(line,f"{i}")
        lst.append(f"video2\\{i}")
    return lst

async def aio_download(src,i):
    tasks=[]
    #timeout = aiohttp.ClientTimeout(total=800)  # 将超时时间设置为600秒
    connector = aiohttp.TCPConnector(limit=50)  # 将并发数量降低

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
                    #lst=getfile_name('E:\pythonProject\\video')

def downsecond_ts(src,name):
    resp=requests.get(src)
    print(src)
    with open(f"video/{name}", mode="wb") as f:
        f.write(resp.content)
    print(f"{name}下载完毕")

def getfile_name(file_dir):
    #获取该目录下所有的信息
    lst=[]
    for root, dirs, files in os.walk(file_dir):
         #print(root) #当前目录路径
         #print(dirs) #当前路径下所有子目录
         lst.append(files) #当前路径下所有非目录子文
    lst=lst[0]
    print(lst)
    print(len(lst))
    return lst

def merge_ts(i):
    combine=[]
    with open(f"斗罗大陆{i+1}",mode="r",encoding='utf-8') as f:
        for line in f:
            if line.startswith("#"):
                continue
            line=line.strip()
            name = line.split("hls/")[1]
            combine.append(name)
    s="+".join(rename_ts(combine))
    s=f"copy /b {s} {i+1}.mp4    "#合并ts，os操作系统命令‘cat ’
    os.chdir('E:\\pythonProject')
    os.system(s)
    print(f"{i+1} end!")

def del_file(path):
    #移除该目录下的所有文件夹，以为需要下载多集视频资源，所以在下载之前需要把上一次下载的ts片段清空
    ls = os.listdir(path)
    for i in ls:
        c_path = os.path.join(path, i)
        if os.path.isdir(c_path):
            del_file(c_path)
        else:
            os.remove(c_path)

def main(url,i):
    iframe_src=get_iframe_src(url)
    download_m3u8(iframe_src,f"斗罗大陆_fist_{i+1}")
    with open(f"斗罗大陆_fist_{i+1}",mode="r",encoding='utf-8') as f:
        for line in f:
            if line.startswith("#"):
                continue
            else:
                line=line.strip()
    #m3u8_url='https://iqiyi.sd-play.com'
    #https: // iqiyi.sd - play.com / 20211026 / OyYbXQrp / index.m3u8
    #m3u8_url=iframe_src.split("/20211026")[0]+line#https://iqiyi.sd-play.com/20211017/0KgHrBlM/1200kb/hls/index.m3u8
    m3u8_url=iframe_src.split('/index.m3u8')[0]+'/1200kb/hls/index.m3u8'
    print(m3u8_url)
    download_m3u8(m3u8_url, f"斗罗大陆{i+1}")
    asyncio.run(aio_download(m3u8_url,i))
    Is_down(getfile_name('E:\pythonProject\\video'),i)
    print("ts下载完毕！")
    key_url=m3u8_url.replace("index.m3u8","key.key")
    #print(key_url)
    key=get_key(key_url)
    #print(key)
    asyncio.run(aio_dec(key,i))
    merge_ts(i);
    del_file('E:\pythonProject\\video')
    del_file('E:\pythonProject\\video2')

if __name__=='__main__':
    i=0#下载的集数
    while(i<1):
        url=f'http://www.dmh8.com/player/4102-0-{i}.html'#4102-0-i
        main(url,i)
        i=i+1
