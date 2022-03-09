import json
import requests
import os
import time


def processOneJsonFile(jsonPath):
    s = open(jsonPath, encoding='UTF-8')
    ss = s.read()
    data = json.loads(ss)
    return data


def downloadFromUrl(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"}

    r = requests.get(url, verify=False, headers=headers)
    return r.content
    # with open(os.path.join(os.path.dirname(os.path.abspath("__file__")), "file.txt"), "wb") as f:
    #     f.write(r.content)


if __name__ == '__main__':
    url = 'http://xuatbeta.wxp.oa.com/ctreport/202105/14/2021051400764160/2641/1620975458_result_test_1Receipts_324104.json'
    url = 'http://xuatbeta.wxp.oa.com/ctreport/202105/14/2021051400764160/2641/1620975501196.jpg'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"}

    r = requests.get(url, verify=False, headers=headers)
    with open(os.path.join(os.path.dirname(os.path.abspath("__file__")), "file.txt"), "wb") as f:
        f.write(r.content)
    exit(0)

    # path = 'E:\\sa\\response_1621237627750.json'

    # path = 'F:\\response_1627384464583.json'

    # urlRepo = processOneJsonFile(path)

    # rootPath = 'F:\\w9Log\\'

    # for phone, logList in urlRepo['data'].items():
    #     for log in logList:
    #         url = log['url']

    #         if '_result_test_' in url:
    #             splits = url.split('/')
    #             relativePath = splits[-2]+'\\'+splits[-1]

    #             jsonContent = downloadFromUrl(url)

    #             # mkdir file if not exists
    #             if not os.path.exists(rootPath+splits[-2]+'\\'):
    #                 os.mkdir(rootPath+splits[-2]+'\\')
    #             with open(rootPath+relativePath, "wb") as f:
    #                 f.write(jsonContent)

    #             jpgs = processOneJsonFile(rootPath+relativePath)['case_data']

    #             for jpg in jpgs:
    #                 if jpg['screenshotPathInit']!='':
    #                     initRelativePath = jpg['screenshotPathInit'].split('/')[-1]
    #                     initJpg = downloadFromUrl(url.replace(splits[-1],initRelativePath))

    #                     absoluteInitPath = rootPath + relativePath.replace(splits[-1], initRelativePath)
    #                     with open(absoluteInitPath, "wb") as f:
    #                         f.write(initJpg)
    #                 if jpg['screenshotPathNext']!='':
    #                     initRelativePath = jpg['screenshotPathNext'].split('/')[-1]
    #                     nextJpg = downloadFromUrl(url.replace(splits[-1],initRelativePath))
    #                     with open(rootPath + relativePath.replace(splits[-1],initRelativePath), "wb") as f:
    #                         f.write(nextJpg)
    #             time.sleep(1)
