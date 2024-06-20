import os, sys
import struct
import binascii
import traceback
import configparser
from colorama import Fore, Back, Style, init
from intelhex import IntelHex
from common import *

init(autoreset=True)
print(Fore.LIGHTYELLOW_EX + "/******************************")
print(Fore.LIGHTYELLOW_EX + "Company:   AUO")
print(Fore.LIGHTYELLOW_EX + "Object :   Generate Bin/Hex File")
print(Fore.LIGHTYELLOW_EX + "Author :   Jeffrey Chen (RRSEB0)")
print(Fore.LIGHTYELLOW_EX + "Version:   V3")
print(Fore.LIGHTYELLOW_EX + "Date   :   2024/06/17")
print(Fore.LIGHTYELLOW_EX + "******************************/")
print(Fore.LIGHTYELLOW_EX + "Project List --")
print(Fore.LIGHTYELLOW_EX + "Project:   GEELY CX1E")
print(Fore.LIGHTYELLOW_EX + "Project:   SGM U557")
print(Fore.LIGHTYELLOW_EX + "******************************/")
# path = "../../"
# thisdirpath = os.getcwd()
# thisdirrealpath = os.path.realpath(path)
# thisdirabspath = os.path.abspath(path)
# print("?111")
# print(thisdirpath)
# print(thisdirrealpath)
# print(thisdirabspath)

def FloderCheckAndBuild(folders: list[str]):
    for folder in folders:
        folder_path = os.path.abspath(os.path.join(os.getcwd(),folder))
        #folder_path = os.path.abspath(os.path.join(os.path.curdir, folder))
        print(f'folder position @ {folder_path}')
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

def GenerateMcuFirmwareCode(BlockInformation_BinFile_Addr_Range,OutputPath):
    print("#---#Start Generate MCU Firmware Files")
    hex_mcu_file = IntelHex()
    isProcessGood = True
    for BinFile, addCRC32, Addr, RangeStart, RangeEnd, RangeCrcStart, RangeCrcEnd in BlockInformation_BinFile_Addr_Range:
        if os.path.exists(BinFile):
            with open(BinFile,'rb') as fp:
                fs = fp.read()
                hex_mcu_file.puts(Addr,fs[RangeStart:RangeEnd])
                if addCRC32 == "yes":
                    crc32_bin = binascii.crc32(fs[RangeCrcStart:RangeCrcEnd],0)
                    byte_crc32_bin = crc32_bin.to_bytes(4,'big')
                    print(f'{BinFile} crc32 = {b2hstr(byte_crc32_bin)}')
                    hex_mcu_file.puts(Addr+RangeEnd-RangeStart,crc32_bin.to_bytes(4,'big'))
        else:
            print(f'{BinFile} File does not exist')
            isProcessGood = False
            break
    print("#---#Output MCU Hex file")
    if isProcessGood:
        hex_mcu_file.write_hex_file(OutputPath)
    else:
        print("#---#Output MCU Hex file Fail!@#$%^&*()")

def GenerateMcuCrc32BinCode(BlockInformation_BinFile_Addr_Range,OutputPath):
    print("#---#Start Generate MCU Firmware Files") 
    byte_temp_binfile = b''
    isProcessGood = True
    for BinFile, addCRC32, Addr, RangeStart, RangeEnd, RangeCrcStart, RangeCrcEnd in BlockInformation_BinFile_Addr_Range:
        if os.path.exists(BinFile):
            with open(BinFile,'rb') as fp:
                fs = fp.read()
                byte_temp_binfile += fs[RangeStart:RangeEnd]
                if addCRC32 == "yes":
                    crc32_bin = binascii.crc32(fs[RangeCrcStart:RangeCrcEnd],0)
                    byte_crc32_bin = crc32_bin.to_bytes(4,'big')
                    byte_temp_binfile += byte_crc32_bin
                    print(f'{BinFile} crc32 = {b2hstr(byte_crc32_bin)}')
        else:
            print(f'{BinFile} File does not exist')
            isProcessGood = False
            break
    print("#---#Output MCU Crc32 Bin file")
    if isProcessGood:
        with open(OutputPath,'wb') as fp:
            fp.write(byte_temp_binfile)
    else:
        print("#---#Output MCU Crc32 Bin file Fail!@#$%^&*()")

def CombineOriginFiles(paths: list[str],OutputPath):
    print("#---#Start Combine OTA Files")
    sectiondata = b''
    combined_data_stream = b''
    checksum = 0
    isProcessGood = True
    for path in paths:
        if os.path.exists(path):
            with open(path,'rb') as fp:
                print(path)
                sectiondata = fp.read()
                combined_data_stream += sectiondata
                checksum = binascii.crc32(sectiondata, 0)
                byte_checksum = struct.pack(">I",checksum)
                print(f"crc32: {checksum}, aka: {b2hstr(byte_checksum)}")
        else:
            print(f'{path} File does not exist')
            isProcessGood = False
            break
    checksum = binascii.crc32(combined_data_stream, 0)
    byte_checksum = struct.pack(">I",checksum)
    print(f"combined data crc32: {checksum}, aka (MSB): {b2hstr(byte_checksum)}")
    print("#---#Output OTA Combined file")
    if isProcessGood:
        with open(OutputPath,'wb') as fp:
            fp.write(combined_data_stream)
    else:
        print("#---#Output OTA Combined file Fail!@#$%^&*()")

def ZeekrOTAHeaderBuild(OutputPath):
    # Initial and load Config File
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Set up header information
    try:
        OTA_header_fs = b''
        with open(config['CONFIG']['output_ota_bin_without_header_fp'],'rb') as fp:
            fs = fp.read()
            int_fs_crc = binascii.crc32(fs,0)
        OTA_header_fs += int_fs_crc.to_bytes(4,'little')
        OTA_header_fs += int(config['HEAD-3IN1-INFO']['header_size'],10).to_bytes(4,'big')
        bytes_partnumber = config['HEAD-3IN1-INFO']['part_number'].encode()
        OTA_header_fs += bytes_partnumber
        for i in range(int(config['HEAD-3IN1-INFO']['part_number_size'],10)-len(bytes_partnumber)):
            OTA_header_fs += b'\0'
        OTA_header_fs += int(config['CONFIG']['mcu_version_hex'],16).to_bytes(2,'big')
        OTA_header_fs += int(config['HEAD-3IN1-INFO']['total_block'],10).to_bytes(4,'big')
        for i in range(int(config['HEAD-3IN1-INFO']['total_block'],10)):
            OTA_header_fs += int(i+1).to_bytes(12,'big')
        start_addr = 0
        block_length = 0
        start_addr += int(config['HEAD-3IN1-INFO']['header_size'],10)
        OTA_header_fs += int(start_addr).to_bytes(4,'big')
        with open(config['MCU-AB-CRC']['filepath'],'rb') as fp:
            fs = fp.read()
            block_length = len(fs)
            OTA_header_fs += int(block_length).to_bytes(4,'big')
        start_addr += block_length
        OTA_header_fs += int(start_addr).to_bytes(4,'big')
        with open(config['TCON']['filepath'],'rb') as fp:
            fs = fp.read()
            block_length = len(fs)
            OTA_header_fs += int(block_length).to_bytes(4,'big')
        start_addr += block_length
        OTA_header_fs += int(start_addr).to_bytes(4,'big')
        with open(config['TDDI']['filepath'],'rb') as fp:
            fs = fp.read()
            block_length = len(fs)
            OTA_header_fs += int(block_length).to_bytes(4,'big')
        OTA_header_fs += b'\xFF\xFF\xFF\xFF'
        print(f'{b2hstr(OTA_header_fs)}')
        with open(OutputPath,'wb') as fp:
            fp.write(OTA_header_fs)
    except Exception:
        print(traceback.format_exc())
        print(Fore.YELLOW + "Build Zeekr OTA header Fail")

def main():
    # Initial and load Config File
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Check Dir file
    FloderCheckAndBuild(folders = ["MCU", "TCON", "TDDI", "OUTPUT"])

    # Iterating through sections
    string_text = "filepath"
    for section in config.sections():
        print('Section:', section)
        for key, value in config[section].items():
            if (key == string_text):
                print(f'{key} = {value}')
                if os.path.exists(value):
                    print(Fore.GREEN + "File is exists")
                else:
                    print(Fore.YELLOW + "File does not exist, please check again")

    # Build MCU Hex File
    print(Fore.LIGHTCYAN_EX + "Build MCU Hex File")
    McuHexBlockInfo = []
    for section in config.sections():
        if "yes" == config[section]['isMCUHEXFILE']:
            print(f'{section} is MCU = yes ')
            McuHexBlockInfo.append((config[section]['filepath'],
                                  config[section]['needcrc32'],
                                  int(config[section]['shift_addr'],16),
                                  int(config[section]['range_start'],16),
                                  int(config[section]['range_end'],16),
                                  int(config[section]['range_crc_start'],16),
                                  int(config[section]['range_crc_end'],16)
                                  ))
    print(Fore.GREEN +f'McuHexBlockInfo = {McuHexBlockInfo}')
    if len(McuHexBlockInfo) == 0:
        print('MCU Hex Block data info is empty')
    else:
        GenerateMcuFirmwareCode(McuHexBlockInfo,config['CONFIG']['output_mcu_hex_fp'])

    # Build MCU A/B CRC32 Bin File (For Zeekr OTA case)
    print(Fore.LIGHTCYAN_EX + "Build MCU A/B CRC32 Bin File")
    McuCrc32BinBlockInfo = []
    for section in config.sections():
        if "yes" == config[section]['isMCUCRC32BINFILE']:
            
            print(f'{section} is MCU CRC32 = yes ')
            McuCrc32BinBlockInfo.append((config[section]['filepath'],
                                  config[section]['needcrc32'],
                                  int(config[section]['shift_addr'],16),
                                  int(config[section]['range_start'],16),
                                  int(config[section]['range_end'],16),
                                  int(config[section]['range_crc_start'],16),
                                  int(config[section]['range_crc_end'],16)
                                  ))
    print(Fore.GREEN + f'McuCrc32BinBlockInfo = {McuCrc32BinBlockInfo}')
    if len(McuCrc32BinBlockInfo) == 0:
        print('MCU Crc32 Bin data info is empty')
    else:
        GenerateMcuCrc32BinCode(McuCrc32BinBlockInfo,config['CONFIG']['output_mcu_ab_crc_fp'])
    
    # Build OTA Combined File with no header (For Zeekr OTA case)
    print(Fore.LIGHTCYAN_EX + "Build OTA Combined File with no header")
    OtaFilePath = []
    for section in config.sections():
        if "yes" == config[section]['isOTAFILE']:
            print(f'{section} is a part of OTA file without header = yes ')
            OtaFilePath.append(config[section]['filepath'])
    print(Fore.GREEN + f'OtaFilePath = {OtaFilePath}')
    if len(OtaFilePath) == 0:
        print('OTA file is empty')
    else:
        CombineOriginFiles(OtaFilePath,config['CONFIG']['output_ota_bin_without_header_fp'])

    # Build Zeekr OTA header
    print(Fore.LIGHTCYAN_EX + "Build Zeekr OTA header")
    ZeekrOTAHeaderBuild(config['CONFIG']['output_ota_bin_header_fp'])

    # Build OTA Combined File with Zeekr OTA header
    print(Fore.LIGHTCYAN_EX + "Build OTA Combined File with Zeekr OTA header")
    FullOtaFilePath = []
    for section in config.sections():
        if "yes" == config[section]['isOTAFileWithHeader']:
            print(f'{section} is a part of OTA file with header = yes ')
            FullOtaFilePath.append(config[section]['filepath'])
    print(Fore.GREEN + f'FullOtaFilePath = {FullOtaFilePath}')
    if len(FullOtaFilePath) == 0: 
        print('Full OTA file is empty')
    else:
        CombineOriginFiles(FullOtaFilePath,config['CONFIG']['output_ota_bin_fp'])

if __name__ == "__main__":
    try:
        print("#####Start")
        main()
    except Exception:
        print(traceback.format_exc())
        os.system("pause")
    finally:     
        print("#####End")
        os.system("pause")