import Foundation
import WatchKit

struct DeviceInfo: Codable {
    let deviceType: String = "apple_watch"
    let model: String
    let osVersion: String
    let deviceName: String

    enum CodingKeys: String, CodingKey {
        case deviceType = "device_type"
        case model
        case osVersion = "os_version"
        case deviceName = "device_name"
    }

    static func current() -> DeviceInfo {
        let device = WKInterfaceDevice.current()
        return DeviceInfo(
            model: device.model,
            osVersion: device.systemVersion,
            deviceName: device.name
        )
    }
}

enum PairingError: Error {
    case invalidCode
    case invalidResponse
    case networkError
}
