from collections import namedtuple
from string import ascii_letters

DebugToken = namedtuple("DebugToken", ("line", "col", "ch"))
DebugSymbol = namedtuple("DebugSymbol", ("start", "end", "text"))

class Debugger:
    def __init__(self, text):
        print("Debugging info injector -- Experimental")
        self.text = text.replace("\t", "    ")
        self.symbols = {}
        self.symbol_count = 0
        self.injection_points = {}
        self.p = 0
        self.tokens = []
        for row, line in enumerate(self.text.split("\n")):
            for col, ch in enumerate(line):
                self.tokens.append(DebugToken(row + 1, col + 1, ch))
            self.tokens.append(DebugToken(row + 1, len(line) + 1, "\n"))
        print("".join([t.ch for t in self.tokens]))

    def _ignore_until(self, ch):
        while self.tokens[self.p].ch != ch:
            self.p += 1

    def print_buffer(self, buffer):
        print("".join( [t.ch for t in buffer]))

    def get_window(self, window):
        return "".join([t.ch for t in self.tokens[self.p-window:self.p+window]])

    def print_window(self, window=12):
        print( "WINDOW:", "".join( [t.ch.replace("\n", "$").replace(" ", ".") for t in self.tokens[self.p-window:self.p+window]] ), "Current:", self.tokens[self.p].ch )

    def parse_start_tag(self):
        print("PARSE START TAG")
        # WS* "<" character* ["/"] ">"
        # WHITE SPACE *
        buffer = []
        while self.tokens[self.p].ch != "<":
            buffer.append(self.tokens[self.p])
            self.p += 1
        # "<"
        buffer.append(self.tokens[self.p])
        self.p += 1


        #character* ["/"]
        self_closing = False
        inside_string = False
        while self.tokens[self.p].ch != ">":
            buffer.append(self.tokens[self.p])
            if self.tokens[self.p].ch == '"':
                inside_string = not(inside_string)
            if self.tokens[self.p].ch == "/" and not inside_string:
                self_closing = True
            self.p += 1

        

        # ">"
        buffer.append(self.tokens[self.p])
        self.p += 1
        self.print_buffer(buffer)
        print("END PARSE START TAG")
        return buffer, self_closing
        
    def parse_end_tag(self):
        print("PARSE END TAG")
        # "<" WS* "/" character* ">"
        buffer = []
        buffer.append(self.tokens[self.p])
        self.p += 1
        while buffer != ">":
            buffer.append(self.tokens[self.p])
            self.p += 1
        # ">"
        buffer.append(self.tokens[self.p])
        self.p += 1
        self.print_buffer(buffer)
        print("END PARSE END TAG")
        return buffer

    def parse_element(self):
        print("PARSE ELEMENT")
        # start_tag [ (element* or character*) end_tag ]

        # start_tag
        buffer = []
        start_tag_buffer, self_closing = self.parse_start_tag()
        buffer.extend(start_tag_buffer)

        if self_closing:
            symbol = (
                f"Self-Closing Tag @ Line {buffer[0].line}, Col {buffer[0].col}\n"
                + ["".join([t.ch for t in buffer])]
            )
            print("New Symbol", symbol)
            self.symbols[self.symbol_count] = symbol
            self.injection_points[ (buffer[-2].line, buffer[-2].col) ] = self.symbol_count
            self.symbol_count += 1
            self.print_buffer(buffer)
            print("END PARSE ELEMENT")
            return buffer
        # [  (element* or character*)
        # Check if it's going to be elements
        is_element = True
        p = self.p
        while self.tokens[p].ch != "<":
            if self.tokens[p].ch in ascii_letters:
                is_element = False
            p += 1
        
        
        if is_element:
            # element *
            while self.tokens[self.p].ch != "<":
                child_buffer = self.parse_element()
                buffer.extend(child_buffer)
                self.p += 1
        else:
            # character *
            while self.tokens[self.p].ch != "<":
                buffer.append(self.tokens[self.p])
                self.p += 1

        # end_tag
        end_buffer = self.parse_end_tag()
        buffer.extend(end_buffer)
        self.print_buffer(buffer)
        print("END PARSE ELEMENT")
        return buffer




    
with open("./calculator.xml", "r") as f:
    Debugger(f.read()).parse_element()