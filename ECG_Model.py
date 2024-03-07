from PyQt6.QtWidgets import QApplication
import sys
import time
import asyncio
from PyQt6.QtCore import QThread, pyqtSignal, QObject
import numpy as np
from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic
from bleak.uuids import uuid16_dict
import math

#参考的polarH10的数据协议
class PolarH10:
    ## HEART RATE SERVICE
    HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
    # Characteristics
    HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"    # notify
    BODY_SENSOR_LOCATION_UUID = "00002a38-0000-1000-8000-00805f9b34fb"      # read

    ## USER DATA SERVICE
    USER_DATA_SERVICE_UUID = "0000181c-0000-1000-8000-00805f9b34fb"
    # Charateristics
    # ...

    ## DEVICE INFORMATION SERVICE
    DEVICE_INFORMATION_SERVICE = "0000180a-0000-1000-8000-00805f9b34fb"
    MANUFACTURER_NAME_UUID = "00002a29-0000-1000-8000-00805f9b34fb"
    MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
    SERIAL_NUMBER_UUID = "00002a25-0000-1000-8000-00805f9b34fb"
    HARDWARE_REVISION_UUID = "00002a27-0000-1000-8000-00805f9b34fb"
    FIRMWARE_REVISION_UUID = "00002a26-0000-1000-8000-00805f9b34fb"
    SOFTWARE_REVISION_UUID = "00002a28-0000-1000-8000-00805f9b34fb"
    SYSTEM_ID_UUID = "00002a23-0000-1000-8000-00805f9b34fb"

    ## BATERY SERIVCE
    BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
    BATTERY_LEVEL_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

    ## UNKNOWN 1 SERVICE
    U1_SERVICE_UUID = "6217ff4b-fb31-1140-ad5a-a45545d7ecf3"
    U1_CHAR1_UUID = "6217ff4c-c8ec-b1fb-1380-3ad986708e2d"      # read
    U1_CHAR2_UUID = "6217ff4d-91bb-91d0-7e2a-7cd3bda8a1f3"      # write-without-response, indicate

    ## Polar Measurement Data (PMD) Service
    PMD_SERVICE_UUID = "fb005c80-02e7-f387-1cad-8acd2d8df0c8"
    PMD_CHAR1_UUID = "fb005c81-02e7-f387-1cad-8acd2d8df0c8" #read, write, indicate – Request stream settings?
    PMD_CHAR2_UUID = "fb005c82-02e7-f387-1cad-8acd2d8df0c8" #notify – Start the notify stream?

    # POLAR ELECTRO Oy SERIVCE
    ELECTRO_SERVICE_UUID = "0000feee-0000-1000-8000-00805f9b34fb"
    ELECTRO_CHAR1_UUID = "fb005c51-02e7-f387-1cad-8acd2d8df0c8" #write-without-response, write, notify
    ELECTRO_CHAR2_UUID = "fb005c52-02e7-f387-1cad-8acd2d8df0c8" #notify
    ELECTRO_CHAR3_UUID = "fb005c53-02e7-f387-1cad-8acd2d8df0c8" #write-without-response, write

    # START PMD STREAM REQUEST
    HR_ENABLE = bytearray([0x01, 0x00])
    HR_DISABLE = bytearray([0x00, 0x00])

    # ECG and ACC Notify Requests
    ECG_WRITE = bytearray([0x02, 0x00, 0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0E, 0x00])
    ACC_WRITE = bytearray([0x02, 0x02, 0x00, 0x01, 0xC8, 0x00, 0x01, 0x01, 0x10, 0x00, 0x02, 0x01, 0x08, 0x00])

    ACC_SAMPLING_FREQ = 200
    ECG_SAMPLING_FREQ = 130

class CircularBuffer2D:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.buffer = np.full((rows, cols), np.nan)
        self.head = 0
        self.tail = 0
        self.dequeued_row = np.full((1,3), np.nan)

# 预定义UUID映射基于心率GATT服务协议
uuid16_dict = {v: k for k, v in uuid16_dict.items()}
MODEL_NBR_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(uuid16_dict.get("Model Number String"))
MANUFACTURER_NAME_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(uuid16_dict.get("Manufacturer Name String"))
BATTERY_LEVEL_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(uuid16_dict.get("Battery Level"))

# START PMD STREAM REQUEST
HR_ENABLE = bytearray([0x01, 0x00])
HR_DISABLE = bytearray([0x00, 0x00])

# ECG and ACC Notify Requests
ECG_WRITE = bytearray([0x02, 0x00, 0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0E, 0x00])
ACC_WRITE = bytearray([0x02, 0x02, 0x00, 0x01, 0xC8, 0x00, 0x01, 0x01, 0x10, 0x00, 0x02, 0x01, 0x08, 0x00])

PMD_SERVICE = "fb005c80-02e7-f387-1cad-8acd2d8df0c8"
PMD_CONTROL = "fb005c81-02e7-f387-1cad-8acd2d8df0c8" #read, write, indicate – Request stream settings?
PMD_DATA = "fb005c82-02e7-f387-1cad-8acd2d8df0c8" #notify – Start the notify stream?

ecg_session_data = []
ecg_session_time = []


def convert_array_to_signed_int(data, offset, length):
    return int.from_bytes(data[offset: offset + length], byteorder="little", signed=True)


def convert_to_unsigned_long(data, offset, length):
    return int.from_bytes(data[offset: offset + length], byteorder="little", signed=False)

class ECGThread(QThread):
    ECGSignals = pyqtSignal(int)
    HRSignals = pyqtSignal(int)
    def __init__(self, device="Polar H10 B606F424"):
        super().__init__()
        self.address = None
        self.target_device = None
        # ---
        self.first_ecg_record = True
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_bleak())
        loop.close()

    # 连接PolarH10设备，并订阅其HR和ECG信号数据
    async def run_bleak(self):
        print("开始搜索ecg设备...")

        # 查找设备id
        # 扫描所有可用的BLE设备
        devices = await BleakScanner.discover()
        # 寻找匹配特定名称的设备
        for device in devices:
            if device.name == "Polar H10 B606F424":
                self.target_device = device
                self.address = self.target_device.address
                print(self.address)
                break
        if self.target_device is None:
            print("未找到匹配的设备'%s'。")
            return

        print("开始连接设备...")

        def disconnected_callback(client):
            # 事件定义
            disconnected_event = asyncio.Event()
            disconnected_event.set()
            print("设备断联!")

        async with BleakClient(self.address,disconnected_callback=disconnected_callback) as self.client:

            print("Polar设备已连接!")
            model_number = await self.client.read_gatt_char(MODEL_NBR_UUID)
            manufacturer_name = await self.client.read_gatt_char(MANUFACTURER_NAME_UUID)
            battery_level = await self.client.read_gatt_char(BATTERY_LEVEL_UUID)
            print(f"Model Number: {model_number.decode()}")
            print(f"Manufacturer Name: {manufacturer_name.decode()}")
            print(f"Battery Level: {int(battery_level[0])}%")

            # 心率
            await self.client.start_notify(PolarH10.HEART_RATE_MEASUREMENT_UUID, self.hr_data_conv)

            # ecg订阅
            await asyncio.sleep(0.5)
            await self.client.write_gatt_char(PolarH10.PMD_CHAR1_UUID, PolarH10.ECG_WRITE, response=True)
            await asyncio.sleep(0.5)
            await self.client.start_notify(PolarH10.PMD_CHAR2_UUID, self.data_conv)

            print(self.client.is_connected)
            print(self.client)
            print("Collecting ECG data...")
            while True:
                await asyncio.sleep(0.2)

    # ------信号控制方法--------
    # 开启ecg信号订阅
    async def start_ecg_stream(self):
        await self.client.write_gatt_char(PolarH10.PMD_CHAR1_UUID, PolarH10.ECG_WRITE, response=True)
        await self.client.start_notify(PolarH10.PMD_CHAR2_UUID, self.data_conv)
        print("开始ECG数据采集...", flush=True)

    # 关闭ecg信号订阅
    async def stop_ecg_stream(self):
        await self.client.stop_notify(PolarH10.PMD_CHAR2_UUID)
        print("停止ECG数据采集...", flush=True)

    async def start_hr_stream(self):
        await self.client.start_notify(PolarH10.HEART_RATE_MEASUREMENT_UUID, self.hr_data_conv)
        print("开始HR数据采集...", flush=True)

    async def stop_hr_stream(self):
        await self.client.stop_notify(PolarH10.HEART_RATE_MEASUREMENT_UUID)
        print("停止HR数据采集...", flush=True)


    # ------数据采集与传输--------
    def data_conv(self,sender, data):
        # 注意调整data_conv方法以符合Bleak的回调签名要求
        if data[0] == 0x00:
            timestamp = convert_to_unsigned_long(data, 1, 8)
            samples = data[10:]
            step = 3
            offset = 0
            while offset < len(samples):
                ecg = convert_array_to_signed_int(samples, offset, step)
                offset += step
                ecg_session_data.append(ecg)
                ecg_session_time.append(timestamp)
                # print("ecg：",ecg)
                # print("ecg_session_data：", ecg_session_data)

                self.ECGSignals.emit(ecg)

    def hr_data_conv(self, sender, data):
        """
        `data` is formatted according to the GATT Characteristic and Object Type 0x2A37 Heart Rate Measurement which is one of the three characteristics included in the "GATT Service 0x180D Heart Rate".
        `data` can include the following bytes:
        - flags
            Always present.
            - bit 0: HR format (uint8 vs. uint16)
            - bit 1, 2: sensor contact status
            - bit 3: energy expenditure status
            - bit 4: RR interval status
        - HR
            Encoded by one or two bytes depending on flags/bit0. One byte is always present (uint8). Two bytes (uint16) are necessary to represent HR > 255.
        - energy expenditure
            Encoded by 2 bytes. Only present if flags/bit3.
        - inter-beat-intervals (IBIs)
            One IBI is encoded by 2 consecutive bytes. Up to 18 bytes depending on presence of uint16 HR format and energy expenditure.
        """

        byte0 = data[0]  # heart rate format
        uint8_format = (byte0 & 1) == 0
        energy_expenditure = ((byte0 >> 3) & 1) == 1
        rr_interval = ((byte0 >> 4) & 1) == 1

        if not rr_interval:
            return

        first_rr_byte = 2
        if uint8_format:
            hr = data[1]
            pass
        else:
            hr = (data[2] << 8) | data[1]  # uint16
            first_rr_byte += 1

        if energy_expenditure:
            # ee = (data[first_rr_byte + 1] << 8) | data[first_rr_byte]
            first_rr_byte += 2

        for i in range(first_rr_byte, len(data), 2):
            ibi = (data[i + 1] << 8) | data[i]
            # Polar H7, H9, and H10 record IBIs in 1/1024 seconds format.
            # Convert 1/1024 sec format to milliseconds.
            # TODO: move conversion to model and only convert if sensor doesn't
            # transmit data in milliseconds.
            ibi = np.ceil(ibi / 1024 * 1000)
            # self.ibi_queue_values.enqueue(np.array([ibi]))
            # self.ibi_queue_times.enqueue(np.array([time.time_ns() / 1.0e9]))

        # print("11111", hr)
        self.HRSignals.emit(hr)

    def ecg_data_conv(self, sender, data):
        # [00 EA 1C AC CC 99 43 52 08 00 68 00 00 58 00 00 46 00 00 3D 00 00 32 00 00 26 00 00 16 00 00 04 00 00 ...]
        # 00 = ECG; EA 1C AC CC 99 43 52 08 = last sample timestamp in nanoseconds; 00 = ECG frameType, sample0 = [68 00 00] microVolts(104) , sample1, sample2, ....
        if data[0] == 0x00:
            timestamp = PolarH10.convert_to_unsigned_long(data, 1, 8) / 1.0e9
            step = 3
            time_step = 1.0 / 130
            samples = data[10:]
            n_samples = math.floor(len(samples) / step)
            offset = 0
            recordDuration = (n_samples - 1) * time_step

            if self.first_ecg_record:
                stream_start_t_epoch_s = time.time_ns() / 1.0e9 - recordDuration
                stream_start_t_polar_s = timestamp - recordDuration
                self.polar_to_epoch_s = stream_start_t_epoch_s - stream_start_t_polar_s
                self.first_ecg_record = False

            sample_timestamp = timestamp - recordDuration + self.polar_to_epoch_s  # timestamp of the first sample in the record in epoch seconds
            while offset < len(samples):
                ecg = PolarH10.convert_array_to_signed_int(samples, offset, step)
                offset += step
                self.ecg_queue_values.enqueue(np.array([ecg]))
                self.ecg_queue_times.enqueue(np.array([sample_timestamp]))
                sample_timestamp += time_step

# ---------测试用----------
# def main():
#
#     app = QApplication(sys.argv)
#
#     ecg_thread = ECGThread("Polar H10 B606F424")
#
#     ecg_thread.start()
#     # 这里您可以连接ECGSignals信号到处理函数，例如：
#     sys.exit(app.exec())
#
# if __name__ == "__main__":
#     main()