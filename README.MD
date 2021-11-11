### note

这个问题目前被看成了一个从code summarization到UI  Information 的翻译任务

对predict_false中第三个错误的分析，text_a是"enter the payment password again and submit the payment password and verify that the payment password is legal"
text_b是"confirm"

这条数据对应的是newlog/2477/"1620973324**323285"里的用例，bert认为这两个不是前后句关系，图片是1620973936999和1620973914780

值得一提的是，不仅第三个错误是这样的，第26个错误也是这样的，他们都有"enter the payment password again to set the payment password and verify that the payment password is [legal/illegal]"。这个texta在原始数据里对应的元素的text都是完成。然后在trainset里，这两个的对应的另一个句子都是finish，但是在测试集中，对应的另一个句子就变成了complete，搜索了全部的数据也没找到这个confirm是怎么来的=。=
在师兄的模型里，这两条信息也都是错误，但是错误的差距很小，最后出来的结果是[0.48,0.52]之间，所以选择了no，在我自己的模型里，这两个数据的都几乎是压倒性的认为是错误的，这让我有点无法理解[e-06, e-01]，进一步观察发现我这里大部分数据选择NO都有压倒性的优势

观察两次训练的结果发现，虽然数据和模型都是一样的，第一次的训练准确率更高，但是softmax的结果在yes和no之间差距特别小，这是否意味着没有学习到任何有用的信息？在第二次训练中，准确率下降了，但是几乎80%的测试数据都表现出了明显的数量级差距。

数据方面也有一些问题，学长的jsonLoad4脚本里，传入的参数是False时，表示不是TrainSet，此时使用的数据时OldVersion，对应的是base118的数据，传入的参数为True时，表示为TrainSet，此时的数据为NewVersion，为basejsapi-7，但是交接文档里表示train set是将基线118的数据封装好得到的。

另外在NewVersion和OldVersion中，只有NewVersion里才发现了enter...这个数据

关于如何改进的思路：
- 先阅读阅读点论文看看别人是怎么做的，但是目前这个东西没有人做过，概括性的来说，我应该去搜索和软件文档相关的seq2seq模型的论文

考虑原因一：
- 训练数据中没有任何可以体现这俩关系的句子
    - 这里同样的句子在训练集中也出现了，答案是Finish，另一个的答案是Confirm，这里是否是存在着翻译上的问题？

- 让数据更好的可视化
- 做出来的东西要比较符合事物本身的规律
- 如无必要，勿增实体
- 先看看能不能直接从数据里get到一些规则或者启发式的方法，然后再尝试用bert
- 可以考虑语法分析，词性标注
- 启发式的方法，新旧测试肯定会有一些相似的地方，大的逻辑框架应该是类似的
- 考虑新的方法