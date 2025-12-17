from enum import IntFlag

class Actions(IntFlag):
    read   = 1 << 0
    create = 1 << 1
    update = 1 << 2
    delete = 1 << 3