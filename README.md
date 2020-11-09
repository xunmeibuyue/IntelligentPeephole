# 智能猫眼项目
实现对上传到OBS中的图片调用华为云人脸识别服务，对返回结果进行分析，将分析结果以csv文件的格式返回到OBS中

## 项目配置
本项目基于华为云部署，本代码部署于华为云函数工作流(FunctionGraph)服务中
函数工作流中，需要配置：
* 环境变量obs_address，对应OBS输入桶的endpoint
* 触发器配置为输入桶
* 输出桶名称设置为output-bucket(也可在代码中自行修改)
* 输入输出的桶名称不能相同
* SMN服务配置自己的账号密码(index.py 123行)，可参考[官方说明](https://github.com/huaweicloudDocs/smn/blob/master/cn.zh-cn/SDK%E5%8F%82%E8%80%83/%E7%AE%80%E4%BB%8B.md)
* `take_photo,py`是树莓派端程序，需要提前在树莓派上将com文件夹复制到程序所在目录下(需要RPi和picamera库支持)
