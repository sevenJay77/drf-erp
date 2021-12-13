import pandas as pd
import jieba
import os
from resources.models import SearchWords
from django.db import transaction

import logging
log = logging.getLogger("django")

STOP_LIST = []

# 加载过滤词组
def load_stop():
    global STOP_LIST
    if not STOP_LIST:
        log.info("=================== load stop words =================")
        stop_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chineseStopWords.csv')
        log.info(stop_path)
        stopwords = pd.read_csv(stop_path, encoding='utf-8', names=['stopword'], index_col=False)
        STOP_LIST = stopwords['stopword'].tolist()


# 保存入库
def storage_word(word):
    query = SearchWords.objects.filter(word=word).first()
    if not query:
        query = SearchWords()
        query.word = word
        query.count = 1
    else:
        count = query.count
        query.count = count + 1
    query.save()



def cut_words_jieba(words):
    # jieba分词
    load_stop()
    cut_func = lambda x : [i.strip() for i in jieba.cut(x) if i not in STOP_LIST and i.strip() != '']
    search_list = cut_func(words)
    search_list.insert(0, words)
    # 去重
    search_data = [i for n, i in enumerate(search_list) if i not in search_list[:n]]
    # 入库
    with transaction.atomic():
        for key in search_data:
            storage_word(key)

    log.info("search_data {}".format(search_data))
    return search_data

