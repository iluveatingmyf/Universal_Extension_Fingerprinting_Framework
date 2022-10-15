import os
import time
import subprocess


#一个测试单元的持续时间
DELAY=50

if __name__ == '__main__':
    #需要替换的路径变量
    Dataset_path = '[本地自定义路径]/chrome_extensions/6/' #某一个分类扩展程序的路径
    Config_path = '[本地自定义路径]/config.txt'#Chromium配置文件的存放路径
    UUID = 'ebfjcddknegphmacmpahfgpbkgedfhlk' #Autotester扩展程序的UUID
    cmd ='[本地路径]/chro/src/out/Release/Chromium.app/Contents/MacOS/Chromium --no-sandbox' #Chromium在命令行的启动命令
    PathSet = os.listdir(Dataset_path)
    
    '''
        迭代开启每一轮测试单元：
            1）生成当前测试单元的相关配置参数写入config.txt；
            2）开启一次Chromium实例，CHromium中安装的Autotester会自动开始指纹收集
            3）因为无法获取一个测试单元完成的信号，因此根据具体测试经验规定了每一轮测试所用的时延（DELAY），在时延到了之后退出Chromium；
            4）再次进入1）步骤，开启新一轮测试单元的进程
    '''
    config = open(Config_path,'w+')
    for path in PathSet:
        if (path=='.DS_Store'):
            continue
        path =Dataset_path+path
        content = 'crxpath=' + path + '/\n' + \
                  'autotester_id='+UUID
        config.truncate()
        config.write(content)
        p = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE)
        t_begining = time.time()
        while True:
            if p.poll() is not None:
                break
            seconds_passed = time.time()-t_begining
            if seconds_passed > DELAY:
                p.terminate()




