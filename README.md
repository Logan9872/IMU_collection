# Runner's Data Collection Software

This software is designed for the simultaneous collection of IMU data from a runner's feet and cardiac data, including electrocardiogram (ECG) and heart rate, using the Polar H10 sensor. The IMU data is collected through the IM948 module. This project aims to provide comprehensive monitoring for athletes, researchers, and enthusiasts interested in detailed biometrics during running activities.

## Features

- **IMU Data Collection**: Capture real-time Inertial Measurement Unit (IMU) data from both feet of the runner, providing insights into movement, pace, and gait analysis.
- **Cardiac Data Collection**: Utilize the Polar H10 sensor to accurately collect heart rate and ECG data, essential for understanding the cardiovascular response to exercise.
- **Synchronization**: Seamlessly synchronize data collection between the IMU sensors and the Polar H10 to ensure accurate time alignment of the data points.
- **Data Export**: Easy export of collected data in common formats for further analysis or integration with other software tools and platforms.

## Hardware Requirements

- **Polar H10 Heart Rate Sensor**: For collecting ECG and heart rate data.
- **IM948 Module**: For IMU data collection from the runner's feet.
- Ensure that the devices are properly configured and connected to the host running the collection software.

## Example command to start data collection
python main.py 

**Maintainers**
@Logan9872 luchangda@bsu.edu.cn

**License**
This project is licensed under the MIT License - see the LICENSE file for details.

**Acknowledgments**
Thanks to the Polar team for providing the heart rate sensor technology.
Acknowledge any other contributors or resources that were instrumental in the development of this project.
