import sys

from .mips import MIPS

def syscall(mips: MIPS):
    watch = int(mips.registers.get("$v0"))
    match watch:
        case 1: 
            value = mips.registers.get("$a0")
            print(int(value))
        case 2 | 3:
            value = mips.registers.get("$f12")
            value = mips.registers.get("$f12")
            print(value)
            
        case 4:
            value = mips.registers.get('$a0')
            print_string(mips.data[mips.data_labels[value]:])
            
        case 5:
            # read_int
            mips.registers["$v0"] = int(input())
            return
        case 6 | 7:
            #read_float or read_double
            mips.registers["$v0"] = float(input())
            return
        case 8:
            # read_string
            str_length = mips.registers.get("$a1")
            input_str = input()[:str_length]
                
            # Add string to data array
            bites = bytearray(input_str + '\0', 'utf-8')
            mips.data += bites
            mips.registers["$a0"] = mips.data_ptr
            mips.data_ptr += len(bites)
            return
        case 9:
            #sbrk not supported
            return
        case 10:
            # exit
            sys.exit()
        case 11:
            # print_character
            value = mips.registers.get("$a0")
            mips.registers["$a0"] = 0
            print(value)
            return
        case 12:
            # read_character
            input_str = input()
            if(len(input_str) > 1):
                print("Error! Character can only be one byte")
            else:
                mips.registers["$v0"] = input_str
            return
        case 13:
            # open
            return
        case 14:
            # read
            return
        case 15:
            # write
            return
        case 16:
            # close
            file_to_close = mips.registers.get("$a0")
            mips.registers["$a0"] = 0
            file_to_close.close()
            return
        case 17:
            # exit2
            mips.registers["$a0"] = input()
            sys.exit()

def print_string(bites: bytearray):
    for pos, bite in enumerate(bites):
        if bite == 0:
            break
        
        if chr(bite) == '\\':
            # "manage" specials character
            # TODO: implement the rest of the escape characters
            
            next = bites.pop(pos + 1)
            
            match chr(next):
                case 'n':
                    print('\n', end="")
                case '\\':
                    print('\\', end="")
                case 't':
                    print('\t', end="")
                                
        else:
            print(chr(bite), end="")