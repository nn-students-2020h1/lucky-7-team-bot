from warnings import warn


class Data(object):
    def __init__(self):
        self.data_list = []
        self.total = 0

    def fill(self, value):
        if isinstance(value, int):
            for i in range(value+1):
                self.data_list.append(i*2)
                self.total += i*2
        else:
            warn("Argument is not an integer value", UserWarning)

    def get_sum(self):
        if isinstance(self.total, int):
            return self.total
        else:
            raise TypeError("Data type error")

    def clear(self):
        self.data_list = None


