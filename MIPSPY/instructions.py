from ctypes import addressof
from math import ceil
import re
from .mips import MIPS

# Helper function to emulate the 32 bit word size
def validate(tmp: int) -> int:
    if tmp > 2147483647:
        # Only grab 8 relevant bytes
        byte = tmp.to_bytes(ceil(tmp.bit_length() / 8), "big")[-8:]
        tmp = int.from_bytes(byte, "big")

    elif tmp < -2147483648:
        byte = tmp.to_bytes(ceil(tmp.bit_length() / 8), "big", signed=True)[-8:]
        tmp = int.from_bytes(byte, "big", signed=True)

    return tmp


def sw_offset(mips: MIPS, register: str) -> int:

    offset, reg = register.split("(")
    # Conver offset
    if offset:
        offset = int(offset)
    else:
        offset = 0

    # Clean value by cutting off leading parenthesis
    reg = reg[:-1]

    # get value
    return mips.registers[reg] + offset


def lw_offset(mips: MIPS, register: str) -> int:
    # we only convert RA
    offset, reg = register.split("(")
    # Conver offset
    offset = int(offset)
    # Clean value by cutting off leading parenthesis
    reg = reg[:-1]

    # get value
    return mips.registers[reg] + offset


# ARTHMETIC INSTRUCTIONS
# add
def add(mips: MIPS, reg1: str, reg2: str, reg3: str) -> None:
    tmp: int = mips.registers[reg2] + mips.registers[reg3]

    # "Return"
    mips.registers[reg1] = validate(tmp)


# subtract
def sub(mips: MIPS, reg1, reg2, reg3):
    mips.registers[reg1] = validate(mips.registers[reg2] - mips.registers[reg3])


# add immediate
def addi(mips: MIPS, reg1, reg2, imd):
    if reg1 == "$ra":
        # Convert back to base 1
        mips.registers[reg1] = (mips.registers[reg2] + int(imd)) // 4
    mips.registers[reg1] = mips.registers[reg2] + int(imd)


# add unsigned
def addu(mips: MIPS, reg1, reg2, reg3):
    mips.registers[reg1] = mips.registers[reg2] + mips.registers[reg3]


# subtract unsigned
def subu(mips: MIPS, reg1, reg2, reg3):
    mips.registers[reg1] = mips.registers[reg2] - mips.registers[reg3]


# add immediate unsigned
def addiu(mips: MIPS, reg1, reg2, imd):
    mips.registers[reg1] = mips.registers[reg2] + int(imd)


# multiply (without overflow) TODO: fix multiplication
def mul(mips: MIPS, reg1, reg2, reg3):
    mips.registers[reg1] = mips.registers[reg2] * mips.registers[reg3]


# multiply (with overflow) TODO: also fix this one too
def mult(mips: MIPS, reg1, reg2):
    ans: int = mips.registers[reg1] * mips.registers[reg2]
    bs = ans.to_bytes(ceil(ans.bit_length() / 8), "big")
    if len(bs) > 4:
        mips.registers["$lo"] = int.from_bytes(bs[-4:], "big")  # grabs last 4 bytes
        mips.registers["$hi"] = int.from_bytes(bs[:-4], "big")  # grabs first 4 bytes
    else:
        mips.registers["$lo"] = int.from_bytes(bs, "big")  # grabs last 4 bytes


# divide TODO: implement division
def div(mips: MIPS, reg1, reg2):
    mips


# LOGICAL

# and
def and_(mips: MIPS, reg1, reg2, reg3):
    mips.registers[reg1] = mips.registers[reg2] & mips.registers[reg3]


# or
def or_(mips: MIPS, reg1, reg2, reg3):
    mips.registers[reg1] = mips.registers[reg2] | mips.registers[reg3]


# and immediate
def andi_(mips: MIPS, reg1, reg2, imd):
    mips.registers[reg1] = mips.registers[reg2] & int(imd)


# or immediate
def ori_(mips: MIPS, reg1, reg2, imd):
    mips.registers[reg1] = mips.registers[reg2] | int(imd)


# shift left logical
def sll_(mips: MIPS, reg1, reg2, imd):
    mips.registers[reg1] = mips.registers[reg2] << int(imd)


# shift right logical
def srl_(mips: MIPS, reg1, reg2, imd):
    mips.registers[reg1] = mips.registers[reg2] >> int(imd)


# DATATRANSFER

# load word
def lw(mips: MIPS, reg1, adr1: str):
    if "(" in adr1:
        adr1 = lw_offset(mips, adr1)
    ret = int.from_bytes(mips.data[adr1 : adr1 + 4], "big", signed=True)

    mips.registers[reg1] = ret


# store word
def sw(mips: MIPS, reg1, adr1):
    bs = list(mips.registers[reg1].to_bytes(4, "big", signed=True))

    if "(" in adr1:
        adr1 = sw_offset(mips, adr1)

    # TODO: FIX THIS

    l = list(mips.data)
    if (len(l) - 1) < adr1 + 4:
        l += [0] * ((adr1 + 4) - ((len(l)) - 1))
    l[adr1 : adr1 + 4] = bs
    mips.data = bytearray(l)
    mips.data_ptr = len(mips.data) - 1


# load upper immediate TODO:
def lui(mips: MIPS, reg1, const: int):
    u_bytes = const.to_bytes(2, "big")
    l_bytes = mips.registers[reg1]


# load address
def la(mips: MIPS, reg1, lab):
    mips.registers[reg1] = lab


# load immediate
def li(mips: MIPS, reg1, imm):
    mips.registers[reg1] = imm


# move from hi
def mfhi(mips: MIPS, reg1):
    mips.registers[reg1] = mips.registers["$hi"]


# move from low
def mflo(mips: MIPS, reg1):
    mips.registers[reg1] = mips.registers["$lo"]


# move
def move(mips: MIPS, reg1, reg2):
    mips.registers[reg1] = mips.registers[reg2]


# CONDITIONAL BRANCH

# branch on equal
def beq(mips: MIPS, reg1, reg2, label):
    if reg1 == reg2:
        mips.program_counter = mips.instr_labels[label]
        mips.program_counter -= 1


# branch on not equal
def bne(mips: MIPS, reg1, reg2, label):

    if mips.registers[reg1] != mips.registers[reg2]:
        mips.program_counter = mips.instr_labels[label]
        mips.program_counter -= 1


# branch on greater than
def bgt(mips: MIPS, reg1, reg2, imd):
    if reg1 > reg2:
        mips.program_counter += int(imd)
        mips.program_counter -= 1


# branch on greater than or equal
def bge(mips: MIPS, reg1, reg2, imd):
    if reg1 >= reg2:
        mips.program_counter += int(imd)
        mips.program_counter -= 1


# branch on less than
def blt(mips: MIPS, reg1, reg2, imd):
    if reg1 < reg2:
        mips.program_counter += int(imd)
        mips.program_counter -= 1


# branch on less than or equal
def ble(mips: MIPS, reg1, reg2, label):
    if reg1 <= reg2:
        mips.program_counter = mips.instr_labels[label]
        mips.program_counter -= 1


# COMPARISON

# set on less than
def slt(mips: MIPS, reg1, reg2, reg3):
    if reg2 == reg3:
        mips.registers[reg1] = 1
    else:
        mips.registers[reg1] = 0


# set on less than immediate
def slti(mips: MIPS, reg1, reg2, imd):
    if reg2 == int(imd):
        mips.registers[reg1] = 1
    else:
        mips.registers[reg1] = 0


# UNCONDITIONAL JUMP

# jump
def j(mips: MIPS, label):
    mips.program_counter = mips.instr_labels[label]

    mips.program_counter -= 1


# jump register
def jr(mips: MIPS, reg1):
    # We convert the base 4 positioning of our register to a program counter
    mips.program_counter = mips.registers[reg1] // 4


# jump and link
def jal(mips: MIPS, label):
    mips.registers["$ra"] = mips.program_counter * 4
    mips.program_counter = mips.instr_labels[label]

    mips.program_counter -= 1


# jump and link register
def jalr(mips: MIPS, reg1):
    # convert from our program counter to base 4
    mips.registers["$ra"] = mips.program_counter * 4
    mips.program_counter = mips.instr_labels[mips.registers[reg1]]

    mips.program_counter -= 1
