### 部分函数逻辑记录

```python
def findMatchedNodeWithSelector(selector, xml)
```
参数解释：selector是一个UI元素选择器，是个字典，其中含有的keys可能有
- instance, 表示id
- rid，表示resource-id
- text，表示text
- contains，也表示text
当text或者contains都在keys里时，instance表示的时textIndex
- class，表示ui的class，这个时候instance表示的是classIndex
- description，表示content-desc
xml就是uiautomator爬出来的xml文件，这个文件里包含了所有node的信息
这个函数会把xml中match了selector的node全都取出来
**重写进度：30%**

```python
def getPositiveAndNegativeExample(handle, nodeMatchedWithSelector,notMatchedNodes, xml)
```
参数解释：handle，就是每次action的trace



```python
def getDocByNode(nodeMatchedWithSelector, isNegative)
```
如果isNegative是False，表示获取MatchedNode里面的信息，这个时候是比较sound的，能多获取就多获取，如果是True，表示是notMatchedNode，不获取太多信息
相比较之下，可能多获取的信息就是rid和class