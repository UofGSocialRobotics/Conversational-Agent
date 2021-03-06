import pyrebase
from ca_logging import log
import copy
import config
import os

from termcolor import colored

class PyrebaseMultipleRefs:
    def __init__(self, ref=None):
        if ref:
            if isinstance(ref, pyrebase.pyrebase.Database):
                self.ref = ref
            else:
                log.error("Cannot be used as a reference!! Expecting pyrebase.pyrebase.Database, got %s" % type(ref).__name__)
        else:
            self.firebase = pyrebase.initialize_app(config.FIREBASE_CONFIG)
            self.reference = self.firebase.database()
            self.img_ref = self.firebase.storage()

    def ref(self):
        return self.reference

    def new_ref(self, children):
        # copy current ref
        tmp_database = copy.deepcopy(self.reference)
        if isinstance(children, list):
            for child in children:
                tmp_database.child(child)
                if not tmp_database.path == "":
                    log.error("Problem with path at %s"%child)
        elif isinstance(children, str):
            tmp_database.child(children)
        return tmp_database

    def path(self):
        return self.reference.path

    def stream(self, stream_handler, stream_id):
        self.reference.stream(stream_handler, stream_id=stream_id)

    def push_here(self, data):
        self.reference.push(data=data)

    def push_at(self, data, path):
        tmp_database = copy.deepcopy(self.reference)
        tmp_database.child(path)
        tmp_database.push(data=data)

    def update_here(self, data):
        self.reference.update(data=data)

    def update_at(self, data, path):
        tmp_database = copy.deepcopy(self.reference)
        tmp_database.child(path)
        tmp_database.update(data=data)

    def put_here(self, data):
        print(colored(data,'red'))
        self.img_ref.child("images/"+data.__str__()).put(data)
        # url = self.img_ref.child("images/example2.jpg").get_url()
        # print(colored(url))
        # return url


if __name__ == "__main__":
    fb = PyrebaseMultipleRefs()
    mypath = 'food/resources/img/recipe_card/small/PNGs/'
    onlyfiles = [f for f in os.listdir(mypath) if (os.path.isfile(mypath + f) and "reduced" in f)]
    c = 0
    for f in onlyfiles:
        fb.put_here(mypath+f)
        if c % 50 == 0:
            print(c)
        c += 1
