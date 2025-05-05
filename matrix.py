import fcntl
import time
import random
import struct
import sys
import termios

# Half-width katakana for consistent width
CHARS = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"

# Matrix color codes
BRIGHT_GREEN = '\033[38;5;46m'   # Bright green for bottom chars
MATRIX_GREEN = '\033[38;5;34m'   # Regular matrix green for middle
DARK_GREEN = '\033[38;5;22m'     # Dark green for top chars

class Column:
    def __init__(self, x, height):
        self.x = x
        self.height = height
        self.chars = [random.choice(CHARS) for _ in range(height)]
        self.bright_position = -1
        self.bright_length = random.randint(4, 8)  # Random number of bright characters
        self.speed = random.randint(1, 2)
        self.skip = 0
        self.visible_length = self.bright_length
        self.max_length = height
        self.done = False

    def move(self):
        if self.speed > self.skip:
            self.skip += 1
            return False
        else:
            self.skip = 0
            self.bright_position += 1
            
            if self.visible_length < self.max_length:
                self.visible_length += 2
            
            if random.random() < 0.05:
                change_pos = random.randint(0, min(self.visible_length, self.height)-1)
                self.chars[change_pos] = random.choice(CHARS)
            
            if self.bright_position > self.height + self.bright_length:
                self.done = True
            return True

class display(list):
    def __init__(self):
        self.height, self.width = struct.unpack('hh', fcntl.ioctl(1, termios.TIOCGWINSZ, '1234'))
        self[:] = [' ' for y in range(self.height) for x in range(self.width)]

    def render_column(self, column):
        for y in range(self.height):
            if y >= column.visible_length:
                continue
                
            pos = y * self.width + column.x
            if pos >= len(self):
                continue
                
            relative_pos = y - column.bright_position

            if 0 <= relative_pos < column.bright_length:
                color = BRIGHT_GREEN
                char = column.chars[y]
            elif relative_pos < 0:
                if random.random() < 0.05:
                    continue
                color = DARK_GREEN
                char = column.chars[y]
            else:
                if random.random() < 0.02:
                    continue
                color = MATRIX_GREEN
                char = column.chars[y]

            if 0 <= pos < len(self):
                self[pos] = f"{color}{char}"

    def __str__(self):
        return ''.join(self)

def matrix(sleep_time=0.05):
    d = display()
    columns = []
    available_x = set(range(d.width))
    used_x = set()
    column_cooldowns = {}  # Track cooldown for each column
    
    sys.stdout.write('\033[2J\033[H')
    
    while True:
        # Update cooldowns
        for x in list(column_cooldowns.keys()):
            column_cooldowns[x] -= 1
            if column_cooldowns[x] <= 0:
                del column_cooldowns[x]
                available_x.add(x)
        
        if available_x:
            num_new_columns = random.randint(1, 3)
            for _ in range(num_new_columns):
                if available_x:
                    x = random.choice(list(available_x))
                    columns.append(Column(x, d.height))
                    available_x.remove(x)
                    used_x.add(x)
        
        d[:] = [' ' for _ in range(d.height * d.width)]
        
        new_columns = []
        for col in columns:
            if not col.done:
                d.render_column(col)
                col.move()
                new_columns.append(col)
            else:
                used_x.remove(col.x)
                # Add cooldown before this column can be used again
                column_cooldowns[col.x] = random.randint(20, 50)  # Adjust these values to control gap size
        
        columns = new_columns
        
        if len(columns) < d.width * 0.4:
            unused = used_x | available_x | set(column_cooldowns.keys())
            available_x.update(set(range(d.width)) - unused)
        
        sys.stdout.write('\033[H%s\033[0m' % d)
        sys.stdout.flush()
        time.sleep(sleep_time)

if __name__ == '__main__':
    sys.stdout.write('\033[2J\033[H')
    try:
        matrix()
    except KeyboardInterrupt:
        sys.stdout.write('\n\033[1m\033[32m=== Matrix Stopped ====\033[0m\n')
        sys.exit()
