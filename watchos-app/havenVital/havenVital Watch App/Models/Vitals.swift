import Foundation

struct WearableVitals: Codable {
    let deviceId: String
    let patientId: String
    let timestamp: String
    let heartRate: Int?
    let heartRateVariability: Double?
    let spo2: Int?
    let respiratoryRate: Int?
    let bodyTemperature: Double?
    let confidence: Double?
    let batteryLevel: Int?
    let isActive: Bool

    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id"
        case patientId = "patient_id"
        case timestamp
        case heartRate = "heart_rate"
        case heartRateVariability = "heart_rate_variability"
        case spo2
        case respiratoryRate = "respiratory_rate"
        case bodyTemperature = "body_temperature"
        case confidence
        case batteryLevel = "battery_level"
        case isActive = "is_active"
    }
}
