
from PyQt6.QtCore import QThread, pyqtSignal
import asyncio
from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic
import numpy as np

from datetime import datetime, timedelta
import os
from multiprocessing import Process

# 设备的Characteristic UUID
par_notification_characteristic = 0x0007
par_write_characteristic = 0x0005

# par_device_addr = "59:7e:4b:aa:28:d4" # 设备2的MAC地址
# par_device_addr = "c8:fe:40:28:4d:c3" # 设备3的MAC地址
# par_device_addr = "1A:55:F7:C4:22:19" # 设备1的MAC地址
# par_device_addr = "6d:9f:6a:e9:cb:f0" # 设备4的MAC地址
par_device_addr = "54:7f:25:4a:aa:fd" # 设备5的MAC地址

# 文件保存路径
start_time = datetime.now().strftime('%Y%m%d_%H%M%S')

# 表头
headers = [
    "Time", "Timestamp",
    "aX", "aY", "aZ",
    "AX", "AY", "AZ",
    "GX", "GY", "GZ",
    "CX", "CY", "CZ",
    "Temperature", "AirPressure", "Height",
    "QuatW", "QuatX", "QuatY", "QuatZ",
    "AngleX", "AngleY", "AngleZ",
    "OffsetX", "OffsetY", "OffsetZ",
    "Steps", "Walking", "Running", "Biking", "Driving",
    "asX", "asY", "asZ",
    "ADC", "GPIO","Timestamp"
    "ADC", "GPIO","Timestamp"
]
# 表头
headers1 = [
    "Timestamp",
    "aX", "aY", "aZ",
    "AX", "AY", "AZ",
    "GX", "GY", "GZ",
    "CX", "CY", "CZ",
    "W", "X", "Y", "Z"
]

# Windows线程优先级常量
THREAD_PRIORITY_LOWEST = -2
THREAD_PRIORITY_BELOW_NORMAL = -1
THREAD_PRIORITY_NORMAL = 0
THREAD_PRIORITY_ABOVE_NORMAL = 1
THREAD_PRIORITY_HIGHEST = 2

class IMUThread(QThread):
    data_signal2 = pyqtSignal(object)
    # data_signal = pyqtSignal(float, float,float, float,float, float, float,float, float)

    # def __init__(self, device_addr="1A:55:F7:C4:22:19",priority=THREAD_PRIORITY_NORMAL):
    # def __init__(self, device_addr="59:7e:4b:aa:28:d4"):
    # def __init__(self, device_addr="c8:fe:40:28:4d:c3"):
    # def __init__(self, device_addr="6d:9f:6a:e9:cb:f0"):
    def __init__(self, device_addr="54:7f:25:4a:aa:fd",priority=THREAD_PRIORITY_NORMAL):


        super(IMUThread, self).__init__()
        self.file_path = os.path.join('IMU_Data5', f'IMU_Data5_{start_time}.csv')
        self.initTime = 0
        self.initTimeSet = False
        self.current_file_path = self.file_path  # 新增属性跟踪当前文件路径
        self.ensure_directory_exists(self.file_path) # 验证当前文件路径
        self.device_addr = device_addr
        self.running = True
        self.start_time = None  # 初始时间戳设置为 None

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.ble_main())
        loop.close()

    async def ble_main(self):
        print("开始搜索设备1...")

        # 基于MAC地址查找设备
        device = await BleakScanner.find_device_by_address(
            par_device_addr, cb=dict(use_bdaddr=False)  # use_bdaddr判断是否是MOC系统
        )
        if device is None:
            print("无法连接设备1 '%s'", par_device_addr)
            return

        # 事件定义
        disconnected_event = asyncio.Event()

        # 断开连接事件回调
        def disconnected_callback(client):
            print("设备断联!")
            disconnected_event.set()
        print("开始连接设备...")

        async with BleakClient(device, disconnected_callback=disconnected_callback) as self.client:
            print("已连接!")
            await self.client.start_notify(par_notification_characteristic, self.notification_handler)

            # 保持连接 0x29
            wakestr = bytes([0x29])
            await self.client.write_gatt_char(par_write_characteristic, wakestr)
            await asyncio.sleep(0.2)
            print("------------------------------------------------")
            # 尝试采用蓝牙高速通信特性 0x46
            fast = bytes([0x46])
            await self.client.write_gatt_char(par_write_characteristic, fast)
            await asyncio.sleep(0.2)

            # 参数设置
            isCompassOn = 0  # 使用磁场融合姿态
            barometerFilter = 2
            # Cmd_ReportTag = 0x0FFF  # 功能订阅标识
            Cmd_ReportTag = 0x002F  # 功能订阅标识   0000000000101111
            params = bytearray([0x00 for i in range(0, 11)])
            params[0] = 0x12
            params[1] = 5  # 静止状态加速度阀值
            params[2] = 200  # 静止归零速度(单位cm/s) 0:不归零 255:立即归零
            params[3] = 0  # 动态归零速度(单位cm/s) 0:不归零
            params[4] = ((barometerFilter & 3) << 1) | (isCompassOn & 1);
            # 采样频率
            params[5] = 250  # 数据主动上报的传输帧率[取值0-250HZ], 0表示0.5HZ
            params[6] = 1  # 陀螺仪滤波系数[取值0-2],数值越大越平稳但实时性越差
            params[7] = 3  # 加速计滤波系数[取值0-4],数值越大越平稳但实时性越差
            params[8] = 5  # 磁力计滤波系数[取值0-9],数值越大越平稳但实时性越差
            params[9] = Cmd_ReportTag & 0xff
            params[10] = (Cmd_ReportTag >> 8) & 0xff
            await self.client.write_gatt_char(par_write_characteristic, params)
            await asyncio.sleep(0.2)
            await self.client.write_gatt_char(par_write_characteristic, params)
            # await asyncio.sleep(0.2)

            notes = bytes([0x19])
            await self.client.write_gatt_char(par_write_characteristic, notes)

            # 添加一个循环，使程序在接收数据时不会退出
            while not disconnected_event.is_set():
                await asyncio.sleep(1.0)

            # await disconnected_event.wait() #休眠直到设备断开连接，有延迟。此处为监听设备直到断开为止
            # await client.stop_notify(par_notification_characteristic)

    # 发送数据
    def send_data_to_device(self, data):
        if self.client and self.client.is_connected:
            asyncio.run(self.sent_message(data))
        else:
            print("设备已连接")

    async def sent_message(self, data):
        try:
            # 使用已经建立的连接发送数据
            await self.client.write_gatt_char(par_write_characteristic, data)
            print("Data sent to device successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")

    # 修改文件名
    def set_file_path(self, new_file_path):
        # 只在文件路径真正改变时更新路径和重置时间戳
        if self.file_path != new_file_path:
            self.file_path = new_file_path
            self.current_file_path = new_file_path
            self.start_time = None  # 重置时间戳
            # 检查新文件是否存在，如果不存在，则创建并写入表头
            if not os.path.isfile(self.file_path):
                with open(self.file_path, 'w') as f:
                    f.write(','.join(headers1) + '\n')

    # 将数据保存到文件
    def save_data_to_file(self, data, file_path):
        # 如果当前文件路径与之前的文件路径不同，为新文件创建文件头
        if self.current_file_path != file_path:
            self.current_file_path = file_path
            self.start_time = None  # 重置初始时间戳
        # 检查文件是否存在，如果不存在，则写入表头
        if not os.path.isfile(file_path):
            with open(file_path, 'w') as f:
                f.write(','.join(headers1) + '\n')
        # 如果是第一次写入数据，设置初始时间戳
        if self.start_time is None:
            self.start_time = datetime.now()

        # 写入时间戳和数据
        # timenow = datetime.now().strftime('%H:%M:%S.%f')
        # timestamp = int(time.mktime(datetime.now().timetuple()) * 1000 + datetime.now().microsecond / 1000)
        # TimeStamp = int(time.mktime(self.start_time.timetuple()) * 1000 + self.start_time.microsecond / 1000)
        with open(file_path, 'a') as f:
            # f.write(f"{timenow},{timestamp}," + ','.join(str(d) for d in data) + '\n')
            f.write(','.join(str(d) for d in data) + '\n')

        # # 更新初始时间为下一个数据点的时间（每次增加4毫秒）
        # self.start_time += timedelta(milliseconds=4)

    def ensure_directory_exists(self, file_path):
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)


    # 解析IMU数据
    def parse_imu(self,buf):

        scaleAccel = 0.00478515625  # 加速度 [-16g~+16g]    9.8*16/32768
        scaleQuat = 0.000030517578125  # 四元数 [-1~+1]         1/32768
        scaleAngle = 0.0054931640625  # 角度   [-180~+180]     180/32768
        scaleAngleSpeed = 0.06103515625  # 角速度 [-2000~+2000]    2000/32768
        scaleMag = 0.15106201171875  # 磁场 [-4950~+4950]   4950/32768
        scaleTemperature = 0.01  # 温度
        scaleAirPressure = 0.0002384185791  # 气压 [-2000~+2000]    2000/8388608
        scaleHeight = 0.0010728836  # 高度 [-9000~+9000]    9000/8388608

        # imu_dat = array('f', [0.0 for i in range(0, 35)])
        # save_data = array('f', [0.0 for i in range(0, 17)])
        # save_data = array('i', [0 for i in range(0, 17)])  # 使用 'i' 作为整数类型

        imu_dat = [0] * 35
        save_data = [0] * 17


        if buf[0] == 0x11:
            if not self.initTimeSet:
                self.initTime = ((buf[6] << 24) | (buf[5] << 16) | (buf[4] << 8) | (buf[3] << 0))
                self.initTimeSet = True
                print("Initial Time Set:", self.initTime)

            ctl = (buf[2] << 8) | buf[1]
            # print("\n subscribe tag: 0x%04x" % ctl)
            imu_dat[34] = ((buf[6] << 24) | (buf[5] << 16) | (buf[4] << 8) | (buf[3] << 0)) - self.initTime
            # aT= ((buf[6] << 24) | (buf[5] << 16) | (buf[4] << 8) | (buf[3] << 0))
            # print(imu_dat[34])



            L = 7  # 从第7字节开始根据 订阅标识tag来解析剩下的数据
            # 三轴无重力加速度
            if ((ctl & 0x0001) != 0):
                tmpX = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAccel;
                L += 2
                # print("\taX: %.3f" % tmpX);  # x加速度aX
                tmpY = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAccel;
                L += 2
                # print("\taY: %.3f" % tmpY);  # y加速度aY
                tmpZ = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAccel;
                L += 2
                # print("\taZ: %.3f" % tmpZ);  # z加速度aZ
                imu_dat[0] = float(tmpX)
                imu_dat[1] = float(tmpY)
                imu_dat[2] = float(tmpZ)

            # 三轴含重力加速度
            if ((ctl & 0x0002) != 0):
                tmpX = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAccel;
                L += 2
                # print("\tAX: %.3f" % tmpX)  # x加速度AX
                tmpY = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAccel;
                L += 2
                # print("\tAY: %.3f" % tmpY)  # y加速度AY
                tmpZ = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAccel;
                L += 2
                # print("\tAZ: %.3f" % tmpZ)  # z加速度AZ
                imu_dat[3] = float(tmpX)
                imu_dat[4] = float(tmpY)
                imu_dat[5] = float(tmpZ)

            # 三轴角速度
            if ((ctl & 0x0004) != 0):
                tmpX = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAngleSpeed;
                L += 2
                # print("\tGX: %.3f" % tmpX)  # x角速度GX
                tmpY = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAngleSpeed;
                L += 2
                # print("\tGY: %.3f" % tmpY)  # y角速度GY
                tmpZ = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAngleSpeed;
                L += 2
                # print("\tGZ: %.3f" % tmpZ)  # z角速度GZ

                imu_dat[6] = float(tmpX)
                imu_dat[7] = float(tmpY)
                imu_dat[8] = float(tmpZ)

            # 三轴磁场!
            if ((ctl & 0x0008) != 0):
                tmpX = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleMag;
                L += 2
                # print("\tCX: %.3f" % tmpX);  # x磁场CX
                tmpY = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleMag;
                L += 2
                # print("\tCY: %.3f" % tmpY);  # y磁场CY
                tmpZ = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleMag;
                L += 2
                # print("\tCZ: %.3f" % tmpZ);  # z磁场CZ

                imu_dat[9] = float(tmpX)
                imu_dat[10] = float(tmpY)
                imu_dat[11] = float(tmpZ)

            # 温度、气压、高度
            if ((ctl & 0x0010) != 0):
                tmpX = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleTemperature;
                L += 2
                # print("\ttemperature: %.2f" % tmpX)  # 温度

                tmpU32 = np.uint32(((np.uint32(buf[L + 2]) << 16) | (np.uint32(buf[L + 1]) << 8) | np.uint32(buf[L])))
                if ((tmpU32 & 0x800000) == 0x800000):  # 若24位数的最高位为1则该数值为负数，需转为32位负数，直接补上ff即可
                    tmpU32 = (tmpU32 | 0xff000000)
                tmpY = np.int32(tmpU32) * scaleAirPressure;
                L += 3
                # print("\tairPressure: %.3f" % tmpY);  # 气压

                tmpU32 = np.uint32((np.uint32(buf[L + 2]) << 16) | (np.uint32(buf[L + 1]) << 8) | np.uint32(buf[L]))
                if ((tmpU32 & 0x800000) == 0x800000):  # 若24位数的最高位为1则该数值为负数，需转为32位负数，直接补上ff即可
                    tmpU32 = (tmpU32 | 0xff000000)
                tmpZ = np.int32(tmpU32) * scaleHeight;
                L += 3
                # print("\theight: %.3f" % tmpZ);  # 高度

                imu_dat[12] = float(tmpX)
                imu_dat[13] = float(tmpY)
                imu_dat[14] = float(tmpZ)

            # 四元数
            if ((ctl & 0x0020) != 0):
                tmpAbs = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleQuat;
                L += 2
                # print("\tw: %.3f" % tmpAbs);  # w
                tmpX = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleQuat;
                L += 2
                # print("\tx: %.3f" % tmpX);  # x
                tmpY = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleQuat;
                L += 2
                # print("\ty: %.3f" % tmpY);  # y
                tmpZ = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleQuat;
                L += 2
                # print("\tz: %.3f" % tmpZ);  # z

                imu_dat[15] = float(tmpAbs)
                imu_dat[16] = float(tmpX)
                imu_dat[17] = float(tmpY)
                imu_dat[18] = float(tmpZ)

            # 导航系加速度
            if ((ctl & 0x0040) != 0):
                tmpX = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAngle;
                L += 2
                # print("\tangleX: %.3f" % tmpX);  # x角度
                tmpY = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAngle;
                L += 2
                # print("\tangleY: %.3f" % tmpY);  # y角度
                tmpZ = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAngle;
                L += 2
                # print("\tangleZ: %.3f" % tmpZ);  # z角度

                imu_dat[19] = float(tmpX)
                imu_dat[20] = float(tmpY)
                imu_dat[21] = float(tmpZ)

            # 三维坐标
            if ((ctl & 0x0080) != 0):
                tmpX = np.short((np.short(buf[L + 1]) << 8) | buf[L]) / 1000.0;
                L += 2
                # print("\toffsetX: %.3f" % tmpX);  # x坐标
                tmpY = np.short((np.short(buf[L + 1]) << 8) | buf[L]) / 1000.0;
                L += 2
                # print("\toffsetY: %.3f" % tmpY);  # y坐标
                tmpZ = np.short((np.short(buf[L + 1]) << 8) | buf[L]) / 1000.0;
                L += 2
                # print("\toffsetZ: %.3f" % tmpZ);  # z坐标

                imu_dat[22] = float(tmpX)
                imu_dat[23] = float(tmpY)
                imu_dat[24] = float(tmpZ)

            # 运动状态判断
            if ((ctl & 0x0100) != 0):
                tmpU32 = ((buf[L + 3] << 24) | (buf[L + 2] << 16) | (buf[L + 1] << 8) | (buf[L] << 0));
                L += 4
                # print("\tsteps: %u" % tmpU32);  # 计步数
                tmpU8 = buf[L];
                L += 1
                if (tmpU8 & 0x01):  # 是否在走路
                    # print("\t walking yes")
                    imu_dat[25] = 100
                else:
                    # print("\t walking no")
                    imu_dat[25] = 0
                if (tmpU8 & 0x02):  # 是否在跑步
                    # print("\t running yes")
                    imu_dat[26] = 100
                else:
                    # print("\t running no")
                    imu_dat[26] = 0
                if (tmpU8 & 0x04):  # 是否在骑车
                    # print("\t biking yes")
                    imu_dat[27] = 100
                else:
                    # print("\t biking no")
                    imu_dat[27] = 0
                if (tmpU8 & 0x08):  # 是否在开车
                    # print("\t driving yes")
                    imu_dat[28] = 100
                else:
                    # print("\t driving no")
                    imu_dat[28] = 0


            if ((ctl & 0x0200) != 0):
                tmpX = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAccel;
                L += 2
                # print("\tasX: %.3f" % tmpX);  # x加速度asX
                tmpY = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAccel;
                L += 2
                # print("\tasY: %.3f" % tmpY);  # y加速度asY
                tmpZ = np.short((np.short(buf[L + 1]) << 8) | buf[L]) * scaleAccel;
                L += 2
                # print("\tasZ: %.3f" % tmpZ);  # z加速度asZ

                imu_dat[29] = float(tmpX)
                imu_dat[30] = float(tmpY)
                imu_dat[31] = float(tmpZ)

            if ((ctl & 0x0400) != 0):
                tmpU16 = ((buf[L + 1] << 8) | (buf[L] << 0));
                L += 2
                # print("\tadc: %u" % tmpU16);  # adc测量到的电压值，单位为mv
                imu_dat[32] = float(tmpU16)

            if ((ctl & 0x0800) != 0):
                tmpU8 = buf[L]
                L += 1
                # print("\t GPIO1  M:%X, N:%X" % ((tmpU8 >> 4) & 0x0f, (tmpU8) & 0x0f))
                imu_dat[33] = float(tmpU8)

        else:
            pass
            # print("[error] data head not define")

        aX = imu_dat[0]
        aY = imu_dat[1]
        aZ = imu_dat[2]

        AX = imu_dat[3]
        AY = imu_dat[4]
        AZ = imu_dat[5]

        GX = imu_dat[6]
        GY = imu_dat[7]
        GZ = imu_dat[8]

        CX = imu_dat[9]
        CY = imu_dat[10]
        CZ = imu_dat[11]

        W = imu_dat[15]
        X = imu_dat[16]
        Y = imu_dat[17]
        Z = imu_dat[18]

        aT = imu_dat[34]
        # ---------
        save_data[0] = aT
        save_data[1] = aX
        save_data[2] = aY
        save_data[3] = aZ
        save_data[4] = AX
        save_data[5] = AY
        save_data[6] = AZ
        save_data[7] = GX
        save_data[8] = GY
        save_data[9] = GZ
        save_data[10] = CX
        save_data[11] = CY
        save_data[12] = CZ
        save_data[13] = W
        save_data[14] = X
        save_data[15] = Y
        save_data[16] = Z

        # 发送信号
        self.save_data_to_file(save_data, self.file_path)
        self.data_signal2.emit(imu_dat)


    # 监听回调函数
    def notification_handler(self,characteristic: BleakGATTCharacteristic, data: bytearray):
       self.parse_imu(data)

