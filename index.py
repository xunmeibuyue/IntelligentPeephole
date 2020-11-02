# -*- coding: utf-8 -*-
import sys
import os
import time
import json

from com.obs.client.obs_client import ObsClient
from com.obs.models.acl import ACL
from com.obs.models.put_object_header import PutObjectHeader
from com.obs.models.get_object_header import GetObjectHeader
from com.obs.models.get_object_request import GetObjectRequest
from com.obs.response.get_result import ObjectStream
from com.obs.models.server_side_encryption import SseKmsHeader
from com.obs.log.Log import *

from frsclient import FrsClient

from smnsdkcore.client import SMNClient
from smnsdkrequests.v20171105 import Publish
from smnsdkrequests.v20171105.Publish import PublishMessage
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

current_file_path = os.path.dirname(os.path.realpath(__file__))
# append current path to search paths, so that we can import some third party libraries.
sys.path.append(current_file_path)

TEMP_ROOT_PATH = "/tmp/"
region = 'china'
secure = True
signature = 'v4'
port = 443
path_style = True

# 获取OBS文件
def GetObject(obsAddr, bucketName, objName, ak, sk):

    TestObs = ObsClient(access_key_id=ak, secret_access_key=sk,
               is_secure=secure, server=obsAddr, signature=signature, path_style=path_style, region=region,ssl_verify=False, port=port,
               max_retry_count=5, timeout=20)

    LobjectRequest = GetObjectRequest(content_type='application/zip', content_language=None, expires=None,
                                      cache_control=None, content_disposition=None, content_encoding=None,
                                      versionId=None)    
    
    Lheaders = GetObjectHeader(range='', if_modified_since=None, if_unmodified_since=None, if_match=None,
                               if_none_match=None)
      

    loadStreamInMemory = False
    resp = TestObs.getObject(bucketName=bucketName, objectKey=objName, downloadPath=TEMP_ROOT_PATH,
                             getObjectRequest=LobjectRequest, headers=Lheaders, loadStreamInMemory=loadStreamInMemory)
    
    print('*** GetObject resp: ', resp)
    
    if isinstance(resp.body, ObjectStream):
        if loadStreamInMemory:
            print(resp.body.size)
        else:
            response = resp.body.response
            chunk_size = 65536
            if response is not None:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    print(chunk)
                response.close()
    else:
        pass #print(resp.body)

# 向OBS上传文件
def PostObject(obsAddr, bucket, objName, ak, sk):
    TestObs = ObsClient(access_key_id=ak, secret_access_key=sk,
               is_secure=secure, server=obsAddr, signature=signature, path_style=path_style, region=region,ssl_verify=False, port=port,
               max_retry_count=5, timeout=20)
   

    Lheaders = PutObjectHeader(md5=None, acl='public-read-write', location=None, contentType='text/plain')
   
    Lheaders.sseHeader = SseKmsHeader.getInstance()
    h = PutObjectHeader(contentType='text/json')
    Lmetadata = {'key': 'value'}

    objPath = TEMP_ROOT_PATH + objName
    resp = TestObs.postObject(bucketName=bucket, objectKey=objName, file_path=objPath,
                              metadata=Lmetadata, headers=h)
    if isinstance(resp, list):
        for k, v in resp:
            print('PostObject, objectKey',k, 'common msg:status:', v.status, ',errorCode:', v.errorCode, ',errorMessage:', v.errorMessage)
    else:
        print('PostObject, common msg: status:', resp.status, ',errorCode:', resp.errorCode, ',errorMessage:', resp.errorMessage)

    return (int(resp.status))

def getObsObjInfo(event): 
    bucket = event['Records'][0]['s3']['bucket']["name"]
    objName = event['Records'][0]['s3']['object']["key"]
    return (bucket, objName)

def upload_json_to_OBS(obs_address, objBucket, ak, sk, fileName, result):
    filePath = TEMP_ROOT_PATH + fileName
    with open(filePath, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=4, separators=(',',': '))

    status = PostObject(obs_address, objBucket, fileName, ak, sk)  # Enter the file name. By default, the file is placed under the same directory as the function entry.
    if (status == 200 or status == 201):
        print("File uploaded to OBS successfully. View details in OBS.")
    else:
        print("Failed to upload the file to OBS.")

# 发送smn消息
def demoPublishMessage(client, topic_urn, message):
    request = PublishMessage()
    request.set_topic_urn(topic_urn)
    request.set_subject("Subject, only display to email subscription")
    request.set_message(message)
    return client.send(request)

# 发送短信
def sendTextMessage():
    client = SMNClient(username='YourAccountUserName', domain_name='YourAccountDomainName', password='YourAccountPassword', region_id='YourRegionName')

    test_urn = 'urn:smn:cn-north-1: xxxx:python-sdk'
    subscription_urn = 'urn:smn:cn-north-1: xxxx:python-sdk:xxxx'
    message = '【智能猫眼提醒】您的门外有可疑人员活动！请注意！'

    status, headers, response_body = demoPublishMessage(client, test_urn, message)
    print status, response_body

def handler (event, context):
    '''
    基础配置，地区,桶地址,aksk,图片路径等
    '''
    region = "cn-north-4"
    srcBucket, srcObjName = getObsObjInfo(event)
    obs_address = context.getUserData('obs_address')  # 这样可以通过环境变量获得参数
    if obs_address is None:
        obs_address = '100.125.15.200'
    ak = context.getAccessKey()
    sk = context.getSecretKey()
    projectId = context.getProjectID()
    # download file uploaded by user from obs
    GetObject(obs_address, srcBucket, srcObjName, ak, sk)
    # 获取图片路径
    srcObjNamePath = TEMP_ROOT_PATH + srcObjName

    '''
    人脸识别
    '''
    frs_client = FrsClient(ak=ak, sk=sk, project_id=projectId)
    ds = frs_client.get_detect_service()
    res = ds.detect_face_by_file(srcObjNamePath, "1,2,4")
    print res.content_eval

    # 解析人脸识别属性
    attributes = res.content_eval['faces'][0]['attributes']
    gender = attributes['gender']
    age = attributes['age']
    glass = attributes['dress']['glass']
    hat = attributes['dress']['hat']

    # 打印人脸识别结果
    gender_map = {"male": "男", "female": "女", "unknown": "未知"}
    glass_map = {"yes": "戴眼镜", "dark": "戴墨镜", "none": "未戴眼镜", "unknown": "未知"}
    hat_map = {"yes": "戴帽子", "none": "未戴帽子", "unknown": "未知"}
    print "#########本次人脸识别结果为############"
    print "年龄：" + str(age)
    print "性别：" + gender_map[gender]
    print "是否戴眼镜：" + glass_map[glass]
    print "是否戴帽子：" + hat_map[hat]
    print "######################################"

    '''
    将结果发送到OBS中
    '''
    objBucket = "output-bucket"
    fileName = "face_detect_result.json"
    face_result = {
        "age": age,
        "gender": gender_map[gender],
        "glass": glass_map[glass],
        "hat": hat_map[hat]
    }
    upload_json_to_OBS(obs_address, objBucket, ak, sk, fileName, face_result)

    # 判断是否是可疑人员
    if (hat == "yes" and glass == "dark"):
        sendTextMessage()

if __name__ == '__main__':
    event = '{"record":[{"event_version":"1.0","smn":{"topic_urn":"urn:smn:southchina:66e0f4622d6f4e3fb2db2e495298a61a:swtest","timestamp":"2017-10-27T06:16:32Z","message_attributes":null,"message":"{\"Records\":[{\"eventVersion\":\"2.0\",\"eventSource\":\"aws:s3\",\"awsRegion\":\"southchina\",\"eventTime\":\"2017-10-27T06:16:29.950Z\",\"eventName\":\"ObjectCreated:Put\",\"userIdentity\":{\"principalId\":\"dc8c156df46d44ebbdefb43c37ae35a6\"},\"requestParameters\":{\"sourceIPAddress\":\"10.57.52.231\"},\"responseElements\":{\"x-amz-request-id\":\"0002F4BCF60000015F5C7989FE55F3C6\",\"x-amz-id-2\":\"DPq9pCp5+g6gkZtpd6EE2WiY4dsAObRPx9WuGfY4TNtGnFrtVblULW5QTJuD1Fyh\"},\"s3\":{\"s3SchemaVersion\":\"1.0\",\"configurationId\":\"swtest\",\"bucket\":{\"name\":\"swbucket\",\"ownerIdentity\":{\"PrincipalId\":\"39e798a6c701403ca78fd4c23b13e71a\"},\"arn\":\"arn:aws:s3:::swbucket\"},\"object\":{\"key\":\"favicon.ico\",\"eTag\":\"e3fde65d45896f909a4a2b3857328592\",\"size\":4286,\"versionId\":\"0000015F5C798A65ea5ec7bf799e61b67cb71e958eb78b53000355445346485a\",\"sequencer\":\"0000000015F5C798C1881FCC60000000\"}}}]}","type":"notification","message_id":"41ab709d3c7847e9bda8f1032d5777b2","subject":"OBS Notification"},"event_subscription_urn":"urn:fss:southchina:66e0f4622d6f4e3fb2db2e495298a61a:function:default:swtest:latest","event_source":"smn"}]}'
    handler(event, 0)
    