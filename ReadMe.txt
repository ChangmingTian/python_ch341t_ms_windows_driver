参考了以下仓库，本仓库提供的版本更加稳定一些
https://github.com/gschorcht/i2c-ch341-usb
https://github.com/openxzx/ch341-py2c/blob/master/quick.py

依赖：
1.pyusb
可以省去学习usb规范和libusb的时间
https://github.com/pyusb/pyusb
2.libusb库
https://github.com/libusb/libusb
3.libusb ms windows backend/driver
zadig可以轻松解决安装驱动的问题
https://zadig.akeo.ie/
libusbK可以用来生成驱动安装包
https://github.com/mcuee/libusbk/

使用步骤：
1.安装pyusb插件
2.下载libusb库，根据你的电脑系统选出所需库文件
3.虽然沁恒官方的库和文档并不能满足需求，但是还是能提供一些信息，建议阅读。
    可以在沁恒官网或者tools目录下获取。
4.我从我的工程中复制除了CH341T相关的部分，还没有调试，应该是可以工作的
   py_src/ch341t/ch341t.py 根据ch341t的指令码，实现初始化，配置，读写功能
   py_src/ch341t_test.py 调用pyusb接口，遍历搜索CH341T设备，测试读写，配置功能
   py_src/libusb libusb库文件
5.由于libusb和python是可以跨平台的，并且没有引入MS Windows动态库文件
    理论上这个驱动也可以跨平台，我还没有测试过其它平台
