# coding=utf-8
import json
import numpy
import os
import xmlMatch
class exampleFound():
    def __init__(self,queryIndexInTrace):
        self.positiveExample = []
        # ['yes','handle','node']
        self.negativeExample = []
        self.res = []
        self.queryIndexInTrace = queryIndexInTrace
        pass

    def processOneTestAction(self,testAction):
        if 'selector' not in testAction:
            return

        nodeMatchedWithSelector,notMatchedNodes = self.findMatchedNodeWithSelector(testAction['selector'],testAction['xml'])
        res = self.getPositiveAndNegativeExample(testAction['trace'],nodeMatchedWithSelector,notMatchedNodes,testAction['xml'])

        self.res.append(res)
        #self.positiveExample.append(positiveExample)
        #self.negativeExample.append(negativeExample)

    def processOneJsonFile(self,jsonPath):
        s = open(jsonPath)
        ss = s.read()
        data = json.loads(ss)
        case_data = data["case_data"]
        for testAction in case_data:
            self.processOneTestAction(testAction)

    def findMatchedNodeWithSelector(self,selector,xml):
        xP = xmlMatch.xmlProcess()
        allNodes = xP.getUIElementsList2(xml.encode('utf-8'),{})

        for node in allNodes:
            if len(list(selector.keys()))>2:
                if 'instance' in list(selector.keys()) and 'rid' in list(selector.keys()) and 'text' in list(selector.keys()) and selector['rid'] == u'com.tencent.mm:id/set_pay_pwd_confirm':
                    if selector['rid'] == node['resource-id'] and selector['instance'] == node['idIndex']:
                        allNodes.remove(node)
                        return node, allNodes
                else:
                    print(list(selector.keys()))
                    raise RuntimeError("aaaaaaaaaaaaaaa")
            elif len(list(selector.keys()))==2:
                if 'instance' in list(selector.keys()):
                    if 'rid' in list(selector.keys()):
                        if selector['rid'] == node['resource-id'] and selector['instance']==node['idIndex']:
                            allNodes.remove(node)
                            return node,allNodes
                    elif 'text' in list(selector.keys()):
                        if selector['text'] == node['text'] and selector['instance']==node['textIndex']:
                            allNodes.remove(node)
                            return node, allNodes
                    elif 'contains' in list(selector.keys()):
                        if selector['contains'] in node['text'] and selector['instance']==node['textIndex']:
                            allNodes.remove(node)
                            return node, allNodes
                    elif 'class' in list(selector.keys()):
                        if selector['class'] == node['class'] and selector['instance']==node['classIndex']:
                            allNodes.remove(node)
                            return node, allNodes
                    else:
                        print(list(selector.keys()))
                        raise RuntimeError("here 4")
                else:
                    if 'rid' in list(selector.keys()):
                        if selector['rid'] == node['resource-id']:
                            allNodes.remove(node)
                            return node, allNodes
                    elif 'text' in list(selector.keys()):
                        if selector['text'] == node['text']:
                            allNodes.remove(node)
                            return node, allNodes
                    elif 'contains' in list(selector.keys()):
                        if selector['contains'] in node['text']:
                            allNodes.remove(node)
                            return node, allNodes
                    elif 'class' in list(selector.keys()):
                        if selector['class'] == node['class']:
                            allNodes.remove(node)
                            return node, allNodes
                    else:
                        print(list(selector.keys()))
                        raise RuntimeError("here 5")
            else:
                #len =1
                if list(selector.keys())[0] == 'rid':
                    if selector['rid'] == node['resource-id']:
                        allNodes.remove(node)
                        return node, allNodes
                elif list(selector.keys())[0] == 'text':
                    if selector['text'] == node['text']:
                        allNodes.remove(node)
                        return node, allNodes
                elif list(selector.keys())[0] == 'contains':
                    if selector['contains'] in node['text']:
                        allNodes.remove(node)
                        return node, allNodes
                elif list(selector.keys())[0] == 'class':
                    if selector['class'] == node['class']:
                        allNodes.remove(node)
                        return node, allNodes
                elif list(selector.keys())[0] == 'description':
                    if selector['description'] == node['content-desc']:
                        allNodes.remove(node)
                        return node, allNodes
                else:
                    print(list(selector.keys())[0])
                    raise RuntimeError("here 3")


    def getPositiveAndNegativeExample(self,handle,nodeMatchedWithSelector,notMatchedNodes,xml):

        positiveDoc = self.getDocByNode(nodeMatchedWithSelector,isNegative=False)

        queryIndexInTrace = self.queryIndexInTrace
        query = handle.split("\n")[queryIndexInTrace].split(" ")[0]
        print(query)
        #query = handle
        negativeDocs =[]
        for notMatchedNode in notMatchedNodes:
            negativeDoc = self.getDocByNode(notMatchedNode,isNegative=True)
            if not negativeDoc is None:
                negativeDocs.append(negativeDoc.replace("\t"," ").replace("\n"," "))

        res = {'query':query.replace("_"," "),'positiveDoc':positiveDoc.replace("\t"," ").replace("\n"," "),'negativeDocs':negativeDocs,'xml':xml}

        return res

    def getDocByNode(self,nodeMatchedWithSelector,isNegative):
        if nodeMatchedWithSelector['text']!='':
            return nodeMatchedWithSelector['text']
        if nodeMatchedWithSelector['content-desc']!='':
            return nodeMatchedWithSelector['content-desc']
        if nodeMatchedWithSelector['resource-id']!='' and not isNegative:
            return nodeMatchedWithSelector['resource-id']
        if nodeMatchedWithSelector['class']!='' and not isNegative:
            return nodeMatchedWithSelector['class']
        return None



def dataProcess(isTrainingSet,trainingPath,queryIndexInTrace,rootPath,outputPath):

    updatedFunctionSet = set()

    # 读取git log 将git commit过程中变更的函数记录在本地文件里。

    updatedFile = open("toAdded.txt")
    updatedFileLines = updatedFile.readlines()
    updatedFile.close()
    for line in updatedFileLines:
        updatedFunctionSet.add(line.strip())


    if isTrainingSet:
        trainFile = open(trainingPath)
        trainFileLines = trainFile.readlines()
        trainSet = {}
        for line in trainFileLines:
            if line.strip().split("\t")[0]=='no' or len(line.strip().split("\t"))<3:continue
            query = line.strip().split("\t")[1]
            doc = line.strip().split("\t")[2]
            if query not in trainSet:
                trainSet[query] = [doc]
            else:
                trainSet[query].append(doc)

    result = []
    res = open(outputPath,'w')

    infoSet = set()
    for filePath,dirnames,filenames in os.walk(rootPath):

        for filename in filenames:
            if '.json' in filename and 'result' in filename:
                eF = exampleFound(queryIndexInTrace)
                print(filePath+'/'+filename)
                eF.processOneJsonFile(filePath+'/'+filename)
                result.append(eF.res)

                for example in eF.res:
                    if example['query'] == 'init' or 'login' in example['query'] or example['query'] == 'system requests from direct business':
                        continue

                    #todo 先统计一下git commit 影响的函数
                    if example['query'].replace(" ","_") not in updatedFunctionSet:
                        continue

                    label = 'yes'
                    doc = example['query']
                    ans = example['positiveDoc'].replace('\n','')

                    if isinstance(ans,unicode):
                        ans_ = ans.encode('utf-8')
                    else:
                        ans_ = ans
                    if doc in trainSet and ans_ in trainSet[doc]:
                        continue

                    queryDoc = label.encode('utf-8')+'\t'+doc.encode('utf-8')+'\t'+ans.encode('utf-8')+'\n'
                    if queryDoc not in infoSet:
                        infoSet.add(queryDoc)
                        res.write(queryDoc)

                    if False:
                        for ans in example['negativeDocs']:
                            label = 'no'
                            doc = example['query']

                            queryDoc = label.encode('utf-8') + '\t' + doc.encode('utf-8') + '\t' + ans.encode(
                                'utf-8') + '\n'
                            if queryDoc not in infoSet:
                                infoSet.add(queryDoc)
                                res.write(queryDoc)

    res.close()


if __name__ == "__main__":
    # -2, -6 根据观察日志格式得出
    dataProcess(False, '', -2, '/Users/pkun/PycharmProjects/ui_api_automated_test/testlog_oldVersion', "resV2.tsv")
    dataProcess(True, 'resV2.tsv', -6,'/Users/pkun/PycharmProjects/ui_api_automated_test/testlog_NewVersion',"res09v7.tsv")
