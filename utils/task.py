from PyQt5.QtCore import QRunnable


class Task(QRunnable):
    """Set up to be able to run a function with args. For use with threadpool """
    def __init__(self, func, *args):
        super(Task, self).__init__()
        self.fn = func
        self.args = args

    def run(self):
        self.fn(*self.args)
