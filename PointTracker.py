import collections

class PointTracker(object):
    def __init__(self, buffer_size: int, landmark_index: int):
        self.buffer = collections.deque(maxlen=buffer_size)
        self.landmark_index = landmark_index

        self.x = 0
        self.y = 0
        self.z = 0

        self.displacement = (0,0,0)



    def update_point(self, new_x: float, new_y: float, new_z: float):
        self.buffer.append((new_x, new_y, new_z))
        avg_x = sum(p[0] for p in self.buffer) / len(self.buffer)
        avg_y = sum(p[1] for p in self.buffer) / len(self.buffer)
        avg_z = sum(p[2] for p in self.buffer) / len(self.buffer)


        self.displacement = (avg_x - self.x, avg_y - self.y, avg_z - self.z)
        self.x = avg_x
        self.y = avg_y
        self.z = avg_z

        return avg_x, avg_y, avg_z