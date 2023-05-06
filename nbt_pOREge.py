#!/usr/bin/env python3
import argparse
import glob
import logging
import os
import sys
import time

from nbt.nbt import NBTFile, TAG_Compound, TAG_String, TAG_Byte, TAG_List

from config import SERVERS, SERVERS_LOCATION

_NAME = "nbt_pOREge"
_LOGGER = logging.getLogger(_NAME)
_LOGGER.setLevel(logging.DEBUG)


def get_tag_size(tag, type_distinction=True) -> int:
    def get_brief_type(_tag) -> str:
        return str(type(_tag)).split('\'')[1].split('.')[-1]
    size_of_data = 0
    if type_distinction:  # Tag distinction uses 1 byte
        size_of_data += 1
    if tag.name:
        size_of_data += 2  # Length of name is always 2 bytes
        size_of_data += len(tag.name)  # Length of name is equal to the number of bytes
    match get_brief_type(tag):
        case "TAG_Byte":
            size_of_data += 1
        case "TAG_Short":
            size_of_data += 2
        case "TAG_Int" | "TAG_Float":
            size_of_data += 4
        case "TAG_Long" | "TAG_Double":
            size_of_data += 8
        case "TAG_Compound":
            for item in tag.tags:
                size_of_data += get_tag_size(item)
            size_of_data += 1  # Closing tag
        case "TAG_String":
            size_of_data += 2 + len(tag.valuestr().encode('utf-8'))  # Modified UTF-8 made manageable by encoding
        case "TAG_List":
            size_of_data += 1  # Distinction of type in this list
            size_of_data += 4  # Length of items in list (signed int)
            for item in tag.tags:
                size_of_data += get_tag_size(item, type_distinction=False)
        case "TAG_Byte_Array" | "TAG_Int_Array" | "TAG_Long_Array":
            length = 4
            multiplier = 0
            if get_brief_type(tag) == "TAG_Byte_Array":
                multiplier = 1
            elif get_brief_type(tag) == "TAG_Int_Array":
                multiplier = 4
            elif get_brief_type(tag) == "TAG_Long_Array":
                multiplier = 8
            size_of_data += (len(tag) * multiplier) + length
    return size_of_data


def write_slot(data: NBTFile, slot: int):
    def get_book():
        book = TAG_Compound()
        book.tags.append(TAG_Byte(name="Slot", value=slot))
        book.tags.append(TAG_String(name="id", value="minecraft:written_book"))
        book.tags.append(TAG_Byte(name="Count", value=1))
        book_data = TAG_Compound(name="tag")
        book_data.tags.append(TAG_String(name="author", value="ORE"))
        book_data.tags.append(TAG_String(name="title", value="§4Read Me"))
        tag_list = TAG_List(name="pages", type=TAG_String)
        tag_list.append(TAG_String(value='{"text":"Dear community member,\\n\\nWe, the ORE Staff Team, take pride in '
                                         'ensuring the servers we run are both functional and enjoyable."}'))
        tag_list.append(TAG_String(value='{"text":"Your inventory has been fixed as it contained '
                                         'larger-than-appropriate NBT data.\\n\\nWith love,\\nORE Staff"}'))
        tag_list.append(TAG_String(value='{"text":"This is an automated procedure. If you believe this was an '
                                         'error, please contact Staff.","italic":true}'))
        book_data.tags.append(tag_list)
        book.tags.append(book_data)
        return book
    data['Inventory'][slot] = get_book()
    data.write_file()


def get_dats(location, minutes=60):
    for file in glob.glob(location):
        if os.path.getmtime(file) > time.time() - (minutes * 60):
            yield file


def _run(servers, _time):
    for server in servers:
        playerdata_location = SERVERS_LOCATION / server / "world" / "playerdata" / "*.dat"
        for playerdata_file in get_dats(str(playerdata_location), _time):
            _LOGGER.debug(f"Found file {playerdata_file}")
            nbtfile = NBTFile(playerdata_file, "rb")
            for index, item in enumerate(nbtfile['Inventory']):
                size = get_tag_size(item, type_distinction=False)
                if size > 2097152:
                    _LOGGER.info(f"\'{playerdata_file}\' has an item in slot {index} of size {size}: {item}")
                    write_slot(nbtfile, index)


def main():
    parser = argparse.ArgumentParser(_NAME)
    parser.add_argument("-v", "--verbose", nargs="?", const=True)
    parser.add_argument(
        "-t", "--time", help="The time, in minutes, to filter playerdata files with modified date less than.",
        nargs="?", const=60
    )
    required_args = parser.add_argument_group("required arguments")
    required_args.add_argument(
        "-s", "--servers", help="The server to clean NBT data.", nargs="+",
        required=True, choices={
            serv for serv in SERVERS
            if serv != "survival" and serv != "seasonal" and serv != "prodxy"
        })
    args = parser.parse_args()
    if args.verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s: %(message)s'))
        _LOGGER.addHandler(console_handler)

    _run(args.servers, int(args.time))


if __name__ == "__main__":
    main()
