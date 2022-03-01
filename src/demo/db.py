import pymongo

my_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = ''
gui_col = ''


records = []
events = []
guis = []
descriptions = []

def insert_record(record):
    pass