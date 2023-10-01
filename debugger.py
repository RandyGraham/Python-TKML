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
        self.tokens.append(DebugToken(0, 0, "EOF"))

    def print_buffer(self, buffer):
        print("BUFFER: |", "".join([t.ch for t in buffer]).replace("\n", "$"))

    def buffer2str(self, buffer):
        return "".join(t.ch for t in buffer)

    def get_window(self, window=12):
        return (
            "WINDOW: |"
            + self.buffer2str(self.tokens[self.p - window : self.p]).replace("\n", "$")
            + "["
            + self.tokens[self.p].ch.replace("\n", "$")
            + "]"
            + self.buffer2str(self.tokens[self.p + 1 : self.p + 1 + window]).replace(
                "\n", "$"
            )
            + "|"
        )

    def print_window(self, window=12):
        print(self.get_window(window))

    def parse_white_space(self):
        buffer = []
        self.print_window()
        while self.tokens[self.p].ch in " \n\t":
            buffer.append(self.tokens[self.p])
            if self.p + 1 >= len(self.tokens):
                return buffer
            self.p += 1
        self.print_window()
        print("PARSE WHITE SPACE", len(buffer))
        return buffer

    def parse_start_tag(self, keep_ws=False):
        print("PARSE START TAG")
        # SELF_CLOSING_TAG: "<" text "/" ">"
        # START_TAG: "<" text ">"

        buffer = []
        assert (
            self.tokens[self.p].ch == "<"
        ), f"Expected '<' @ {self.p} {self.get_window()}"
        buffer.append(self.tokens[self.p])
        self.p += 1

        # character* ["/"]
        self_closing = False
        inside_string = False
        while self.tokens[self.p].ch != ">":
            buffer.append(self.tokens[self.p])
            if self.tokens[self.p].ch == '"':
                inside_string = not (inside_string)
            if self.tokens[self.p].ch == "/" and not inside_string:
                self_closing = True
            self.p += 1

        # ">"
        assert (
            self.tokens[self.p].ch == ">"
        ), f"Expected '<' @ {self.p} {self.get_window()}"

        buffer.append(self.tokens[self.p])
        self.p += 1
        buffer.extend(self.parse_white_space())
        self.print_buffer(buffer)
        self.print_window()
        print("END PARSE START TAG\n\n")
        return buffer, self_closing

    def parse_end_tag(self):
        print("PARSE END TAG")
        # END_TAG: "<" "/" text ">"
        buffer = []
        buffer.append(self.tokens[self.p])
        self.p += 1
        while self.tokens[self.p].ch != ">":
            buffer.append(self.tokens[self.p])
            self.p += 1
        # ">"
        buffer.append(self.tokens[self.p])
        self.p += 1

        self.print_buffer(buffer)
        self.print_window()

        print("END PARSE END TAG\n\n")
        return buffer

    def next_tag_type(self):
        # Check if there is another element
        p = self.p

        while self.tokens[p].ch != "<":
            p += 1

        # self.tokens[p] == "<"
        p += 1

        while self.tokens[p].ch == " ":
            p += 1

        print("Next Tag Type:", self.tokens[p].ch)
        if self.tokens[p].ch == "/":
            return "end"
        else:
            return "start"

    def parse_element(self):
        print("PARSE ELEMENT")
        # ELEMENT: (WS* SELF_CLOSING_TAG WS*) | (WS* START_TAG WS* (text | ELEMENT*) END_TAG WS*)

        # start_tag
        buffer = []

        buffer.extend(self.parse_white_space())

        start_tag_buffer, self_closing = self.parse_start_tag()
        buffer.extend(start_tag_buffer)

        buffer.extend(self.parse_white_space())

        if self_closing:
            symbol = (
                f"Self-Closing Tag @ Line {buffer[0].line}, Col {buffer[0].col}\n"
                + "".join([t.ch for t in buffer])
            )
            print("New Symbol", symbol)
            self.symbols[self.symbol_count] = symbol

            p = self.p
            while self.tokens[p].ch != "/":
                p -= 1

            self.injection_points[p] = self.symbol_count
            self.symbol_count += 1
            self.print_buffer(buffer)
            self.print_window()
            print("END PARSE ELEMENT\n\n")
            return buffer

        injection_point = p
        # [  (element* or character*)
        # Check if it's going to be elements
        is_element = True
        p = self.p
        while self.tokens[p].ch != "<":
            if self.tokens[p].ch in ascii_letters:
                is_element = False
            p += 1

        print(
            f"PARSE ELEMENT :: PARSE CHIDLREN :: MODE={ 'elements' if is_element else 'text' }"
        )
        if is_element:
            # element *
            while self.next_tag_type() == "start":
                print("RECURSING")
                self.print_window()
                child_buffer = self.parse_element()
                buffer.extend(child_buffer)

                self.print_buffer(buffer)
                self.print_window()
                print("BACK TO MAIN\n")
                # input("NEXT: ")
        else:
            # character *
            a = self.p
            while self.tokens[self.p].ch != "<":
                buffer.append(self.tokens[self.p])
                self.p += 1
            b = self.p
            print("TEXT:", "".join([t.ch for t in self.tokens[a:b]]))

        print("PARSE ELEMENT :: END PARSE CHILDREN\n")
        buffer.extend(self.parse_white_space())
        # end_tag
        end_buffer = self.parse_end_tag()
        buffer.extend(end_buffer)

        buffer.extend(self.parse_white_space())
        print("END PARSE ELEMENT\n\n")

        symbol = f"\n╔ Element @ Line {buffer[0].line}, Col {buffer[0].col}\n"

        for line in "".join([t.ch for t in buffer]).split("\n"):
            symbol += "║ " + line + "\n"

        symbol += f"╚ End @ Line {buffer[-1].line}, Col {buffer[-1].col}"

        self.symbols[self.symbol_count] = symbol
        self.injection_points[injection_point] = self.symbol_count
        self.symbol_count += 1
        print("New Symbol", symbol)
        return buffer

    def parse_document(self):
        print("PARSE DOCUMENT")
        # DOCUMENT: ELEMENT eof
        buffer = self.parse_element()
        self.print_window()
        assert self.tokens[self.p].ch == "EOF"
        return buffer


with open("./calculator.xml", "r") as f:
    d = Debugger(f.read())
    d.parse_document()
    print(d.symbols)
    previous = 0
    buffer = []
    for injection in d.injection_points:
        buffer.append(d.text[previous : injection - 1])
        previous = injection - 1
        buffer.append(f' _DEBUG_SYM_REF = "{d.injection_points[injection]}" ')
        print(injection)
    print("".join(buffer))
