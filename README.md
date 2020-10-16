# 智能猫眼项目
实现对上传到OBS中的图片调用华为云人脸识别服务，对返回结果进行分析，将分析结果以csv文件的格式返回到OBS中

## 项目配置
本项目基于华为云部署，本代码部署于华为云函数工作流(FunctionGraph)服务中
函数工作流中，需要配置：
* 环境变量obs_address，对应OBS输入桶的endpoint
* 触发器配置为输入桶
* 输出桶名称设置为output-bucket(也可在代码中自行修改)
* 输入输出的桶名称不能相同

## 项目结构
```
IntelligentPeephole                                
├─ com        // 常用SDK结构
│  ├─ obs
├─ frsaccess  /************/
├─ frsclient       FRS
├─ frscommon       SDK
├─ frsutils   /************/
├─ index.py   // 主函数
└─ README.md
```