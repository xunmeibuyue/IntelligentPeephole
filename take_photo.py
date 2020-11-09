from picamera import PiCamera
from time import sleep
import RPi.GPIO as GPIO
from com.obs.client.obs_client import ObsClient
from com.obs.models.put_object_header import PutObjectHeader
from com.obs.models.server_side_encryption import SseKmsHeader

# 配置GPIO
GPIO.setmode(GPIO.BOARD)  # 设置BMC或者BOARD模式
pin = 8
GPIO.setup(pin, GPIO.IN)  # 设置引脚为输入

# 配置相机
camera = PiCamera()
camera.resolution = (720, 480)

# 配置OBS
obs_address = "obs.cn-north-4.myhuaweicloud.com"  # 即endpoint
objBucket = "my-bucket-input"
ak = "4SZGD6PKPPLXCUWJQUIF"
sk = "K4oGec3T2jRWm0Q3jvRBnh8FG4vFiNrZyrkFyo39"


# 向OBS上传文件
def PostObject(obsAddr, bucket, objName, ak, sk):
    TestObs = ObsClient(access_key_id=ak,
                        secret_access_key=sk,
                        server=obsAddr,
                        ssl_verify=False,
                        max_retry_count=5,
                        timeout=20)

    Lheaders = PutObjectHeader(md5=None,
                               acl='private',
                               location=None,
                               contentType='text/plain')

    Lheaders.sseHeader = SseKmsHeader.getInstance()
    h = PutObjectHeader(contentType='image/jpeg')
    Lmetadata = {'key': 'value'}

    objPath = '/home/pi/picamera/photos/' + objName
    resp = TestObs.postObject(bucketName=bucket,
                              objectKey=objName,
                              file_path=objPath,
                              metadata=Lmetadata,
                              headers=h)
    if isinstance(resp, list):
        for k, v in resp:
            print('PostObject, objectKey', k, 'common msg:status:', v.status,
                  ',errorCode:', v.errorCode, ',errorMessage:', v.errorMessage)
    else:
        print('PostObject, common msg: status:', resp.status, ',errorCode:',
              resp.errorCode, ',errorMessage:', resp.errorMessage)

    return (int(resp.status))


# 拍照
def take_photo():
    fileName = 'face.jpg'
    filePath = '/home/pi/picamera/photos/%s' % fileName
    camera.start_preview()
    camera.capture(filePath)
    camera.stop_preview()

    status = PostObject(obs_address, objBucket, fileName, ak, sk)  # 上传


# 主函数，循坏查找10s
def main():
    while True：
    if GPIO.input(pin) == 1:
        sleep(1)
        take_photo()


if __name__ == '__main__':
    main()
